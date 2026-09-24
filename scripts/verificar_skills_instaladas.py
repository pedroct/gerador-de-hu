"""Compara as skills deste repositorio com as instaladas num projeto.

Existe por causa de duas armadilhas do `npx skills`, descobertas ao atualizar um
projeto real em 2026-09-24:

1. `npx skills update` so ressincroniza o que ja esta no `skills-lock.json`. Uma skill
   nova no repositorio **nao e trazida e nem sequer mencionada** — o comando termina com
   "Updated N skill(s)" e o projeto continua sem ela.
2. `npx skills add --skill <nome> -a claude-code` instala como **copia** dentro de
   `.claude/skills/`, enquanto o padrao do projeto e um diretorio canonico
   `.agents/skills/` com symlinks a partir de cada agente. A copia fica invisivel para os
   outros agentes e nao e atualizada junto.

Uso:
    uv run python scripts/verificar_skills_instaladas.py /caminho/do/projeto
    uv run python scripts/verificar_skills_instaladas.py /caminho/do/projeto --aplicar

Sem `--aplicar`, apenas relata e imprime o comando de sincronizacao.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = "pedroct/gerador-de-hu"

# O unico comando que traz skills novas e mantem o layout canonico com symlinks.
# `update` nao serve: ele so re-busca o que ja esta no lock.
COMANDO_SYNC = ["npx", "--yes", "skills", "add", ORIGEM, "--skill", "*", "-a", "*", "-y"]

# Diretorios de agente que apontam para o canonico.
AGENTES = (".claude/skills", ".codex/skills")
CANONICO = ".agents/skills"


def skills_do_repositorio() -> set[str]:
    """Diretorios da raiz que contem um SKILL.md."""
    return {
        caminho.parent.name
        for caminho in RAIZ.glob("*/SKILL.md")
        if not caminho.parent.name.startswith(".")
    }


def skills_no_lock(projeto: Path) -> set[str]:
    lock = projeto / "skills-lock.json"
    if not lock.is_file():
        return set()
    dados = json.loads(lock.read_text(encoding="utf-8"))
    return set(dados.get("skills", {}))


def instaladas_no_canonico(projeto: Path) -> set[str]:
    base = projeto / CANONICO
    if not base.is_dir():
        return set()
    return {d.name for d in base.iterdir() if d.is_dir() or d.is_symlink()}


def copias_fora_do_canonico(projeto: Path, nossas: set[str]) -> list[str]:
    """Skills DESTE repositorio que viraram copia num diretorio de agente.

    Restrito as nossas: o projeto pode instalar skills de outras origens, e o layout
    delas nao e assunto deste script.
    """
    problemas: list[str] = []
    for agente in AGENTES:
        base = projeto / agente
        if not base.is_dir():
            continue
        for entrada in sorted(base.iterdir()):
            if entrada.name in nossas and entrada.is_dir() and not entrada.is_symlink():
                problemas.append(f"{agente}/{entrada.name}")
    return problemas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projeto", help="raiz do projeto que consome as skills")
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="roda a sincronizacao em vez de apenas relatar",
    )
    args = parser.parse_args()

    projeto = Path(args.projeto).expanduser().resolve()
    if not projeto.is_dir():
        print(f"Projeto nao encontrado: {projeto}", file=sys.stderr)
        return 2

    repo = skills_do_repositorio()
    lock = skills_no_lock(projeto)
    canonico = instaladas_no_canonico(projeto)
    copias = copias_fora_do_canonico(projeto, repo)

    faltando = sorted(repo - canonico)
    fora_do_lock = sorted(canonico - lock)
    orfas = sorted(canonico - repo)

    print(f"repositorio : {len(repo)} skills")
    print(f"projeto     : {projeto}")
    print(f"instaladas  : {len(canonico)} em {CANONICO}\n")

    if faltando:
        print("FALTANDO no projeto (novas no repositorio; `update` nao as traz):")
        for nome in faltando:
            print(f"  - {nome}")
        print()
    if orfas:
        print("INSTALADAS mas ausentes do repositorio (renomeadas ou removidas):")
        for nome in orfas:
            print(f"  - {nome}")
        print()
    if fora_do_lock:
        print("INSTALADAS mas ausentes do skills-lock.json:")
        for nome in fora_do_lock:
            print(f"  - {nome}")
        print()
    if copias:
        print("COPIAS em vez de symlink (invisiveis para os outros agentes):")
        for nome in copias:
            print(f"  - {nome}")
        print()

    if not (faltando or orfas or fora_do_lock or copias):
        print("Tudo em dia.")
        return 0

    comando = " ".join(f"'{p}'" if p == "*" else p for p in COMANDO_SYNC)
    if not args.aplicar:
        print(f"Para sincronizar, rode dentro de {projeto}:\n  {comando}")
        return 1

    print(f"Sincronizando: {comando}")
    # COMANDO_SYNC e constante do modulo; nada dele vem de entrada do usuario.
    concluido = subprocess.run(  # noqa: S603  # nosec B603
        COMANDO_SYNC, cwd=projeto, check=False
    )
    return concluido.returncode


if __name__ == "__main__":
    raise SystemExit(main())

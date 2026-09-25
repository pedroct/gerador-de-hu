"""Verifica se lacunas de negócio vazaram vocabulário técnico.

A regra de tradução exige que uma pergunta destinada à área de negócio não cite arquivo, classe,
método, campo, enum, número de linha ou variável. A evidência `caminho:linha` continua na spec, em
comentário, mas fora do corpo da pergunta.

Uso:
    uv run python redigir-spec-demanda-azure-boards/scripts/verificar_lacunas.py spec.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CABECALHO = re.compile(
    r"^- \*\*(?P<id>[NT]\d+) · (?P<audiencia>Negócio|Técnico)\*\* — (?P<inicio>.*)$"
)
EVIDENCIA = re.compile(r"<!--.*?-->", re.DOTALL)
NOVO_BLOCO = re.compile(r"^(?:- |#)")

EXTENSOES = "java|ts|tsx|js|jsx|dart|py|kt|swift|cs|rb|go|php|vue|html|scss|css|sql|xml|ya?ml|json"
PADROES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("caminho-de-arquivo", re.compile(rf"[\w/.\-]+\.({EXTENSOES})\b")),
    ("numero-de-linha", re.compile(r"(?<!\d):\d+(?:-\d+)?\b")),
    ("chamada-de-metodo", re.compile(r"\b[A-Za-z_][\w.]*\.[a-z]\w*\s*\(")),
    ("identificador-pontuado", re.compile(r"\b[A-Z][A-Za-z0-9]*\.[A-Za-z][A-Za-z0-9]*\b")),
)


@dataclass(frozen=True)
class Lacuna:
    identificador: str
    audiencia: str
    pergunta: str
    linha: int


@dataclass(frozen=True)
class Violacao:
    lacuna: Lacuna
    trecho: str
    padrao: str


def _e_continuacao(linha: str) -> bool:
    """Diz se a linha ainda pertence ao item aberto.

    Linha indentada sempre continua. Sem indentação, continua mesmo assim — continuação preguiçosa
    é Markdown válido e renderiza dentro do item, então o que vaza nela tem de chegar ao gate —,
    a menos que abra outro item ou um título.
    """
    if linha.startswith(("  ", "\t")):
        return True
    return bool(linha.strip()) and not NOVO_BLOCO.match(linha)


def extrair_lacunas(texto: str) -> list[Lacuna]:
    """Devolve as lacunas rotuladas. Uma spec sem rótulos devolve lista vazia, não erro."""
    lacunas: list[Lacuna] = []
    identificador = ""
    audiencia = ""
    linha_inicial = 0
    corpo: list[str] = []
    aberta = False

    def fechar() -> None:
        nonlocal aberta
        if not aberta:
            return
        pergunta = " ".join(EVIDENCIA.sub(" ", " ".join(corpo)).split())
        lacunas.append(Lacuna(identificador, audiencia, pergunta, linha_inicial))
        aberta = False

    for numero, linha in enumerate(texto.splitlines(), start=1):
        encontrado = CABECALHO.match(linha)
        if encontrado:
            fechar()
            identificador = encontrado.group("id")
            audiencia = encontrado.group("audiencia")
            linha_inicial = numero
            corpo = [encontrado.group("inicio")]
            aberta = True
        elif aberta and _e_continuacao(linha):
            corpo.append(linha.strip())
        elif aberta:
            fechar()
    fechar()
    return lacunas


def verificar(texto: str) -> list[Violacao]:
    """Sinaliza vocabulário técnico dentro de perguntas de negócio."""
    violacoes: list[Violacao] = []
    for lacuna in extrair_lacunas(texto):
        if lacuna.audiencia != "Negócio":
            continue
        for nome, padrao in PADROES:
            achado = padrao.search(lacuna.pergunta)
            if achado:
                violacoes.append(Violacao(lacuna=lacuna, trecho=achado.group(0), padrao=nome))
                break
    return violacoes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="caminho da spec, ou '-' para a entrada padrão")
    args = parser.parse_args(argv)

    try:
        texto = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text("utf-8")
    except OSError as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 2

    violacoes = verificar(texto)
    if not violacoes:
        print("Nenhum vazamento de vocabulário técnico em lacunas de negócio.")
        return 0

    for violacao in violacoes:
        print(
            f"linha {violacao.lacuna.linha}: {violacao.lacuna.identificador} "
            f"({violacao.padrao}) — {violacao.trecho!r}",
            file=sys.stderr,
        )
    print(
        f"\n{len(violacoes)} lacuna(s) de negócio citam código. "
        "Reescreva a pergunta e mova a citação para o comentário de evidência.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

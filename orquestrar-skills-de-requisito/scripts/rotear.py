"""Roteia material de requisito para a skill correspondente, com apoio do Jev.

Uso:
    uv run python orquestrar-skills-de-requisito/scripts/rotear.py caminho/do/material.md
    cat material.md | uv run python orquestrar-skills-de-requisito/scripts/rotear.py -
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cliente_jev import carregar_chave, decidir  # noqa: E402
from perguntas import PERGUNTAS  # noqa: E402
from roteamento import rotear  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("material", help="arquivo com o material, ou '-' para ler da entrada")
    parser.add_argument("--json", action="store_true", help="imprime o resultado como JSON")
    args = parser.parse_args()

    texto = sys.stdin.read() if args.material == "-" else Path(args.material).read_text("utf-8")
    if not texto.strip():
        print("Material vazio.", file=sys.stderr)
        return 2

    resultado = rotear(decidir({"material": texto}, PERGUNTAS, carregar_chave())["answers"])

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0

    tipo = resultado["tipo_de_entrada"]
    print(f"Tipo do material : {tipo} (confiança {resultado['confianca']:.2f})")
    if resultado["decidir_com_a_pessoa"]:
        print("\n⚠  Confiança abaixo do limiar. NÃO decida sozinho.")
        print(f"   Alternativas mais prováveis: {', '.join(resultado['alternativas'])}")
        print("   Pergunte à pessoa qual descreve o material antes de seguir.")
    else:
        print(f"\nChame a skill  : {resultado['skill']}")
        print(f"Porque         : {resultado['porque']}")

    if resultado["tambem_considerar"]:
        print("\nConsidere também (opcional, quem decide é a pessoa):")
        for item in resultado["tambem_considerar"]:
            print(f"  - {item['skill']}: {item['porque']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Prioriza um débito técnico com apoio do Jev.

Uso:
    uv run python especificar-debitos-tecnicos/scripts/priorizar.py debito.md
    cat debito.md | uv run python especificar-debitos-tecnicos/scripts/priorizar.py - --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cliente_jev import carregar_chave, decidir  # noqa: E402
from priorizacao import PERGUNTAS, faixa, montar_state, priorizar  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("debito", help="arquivo com a descrição do débito, ou '-' para a entrada")
    parser.add_argument("--contexto", help="demanda ou spec relacionada, opcional")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    texto = sys.stdin.read() if args.debito == "-" else Path(args.debito).read_text("utf-8")
    if not texto.strip():
        print("Descrição vazia.", file=sys.stderr)
        return 2

    resposta = decidir(montar_state(texto, args.contexto), PERGUNTAS, carregar_chave())
    r = priorizar(resposta["answers"])

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    qual = faixa(r)
    if qual == "restricao":
        print("FAIXA          : RESTRIÇÃO — não compete por eficiência.")
        print("                 Severidade alta com probabilidade real; o esforço não a adia.")
    elif qual == "a_confirmar":
        print(
            "FAIXA          : A CONFIRMAR — severidade julgada com confiança "
            f"{r['confiancas']['severidade']:.2f}."
        )
        print("                 Diga na descrição o que acontece quando o débito se manifesta.")
    else:
        print("FAIXA          : candidato — ordena pela fórmula da skill.")
    print(f"Categoria      : {r['categoria']}")
    print(f"Tipo sugerido  : {r['tipo_sugerido']}")
    print(f"Impacto        : {r['impacto']}  (score {r['scores_crus']['impacto']:.2f})")
    print(
        f"Risco          : {r['risco']}  (probabilidade {r['probabilidade']}, "
        f"severidade {r['severidade']})"
    )
    print(f"Esforço        : {r['esforco']}  (score {r['scores_crus']['esforco']:.2f})")
    print(
        f"Prioridade     : {r['prioridade']}   = ({r['impacto']} + {r['risco']}) "
        f"× (6 − {r['esforco']})"
    )
    if r["menor_confianca"] < 0.5:
        baixas = [d for d, c in r["confiancas"].items() if c < 0.5]
        print(f"\n⚠  Confiança baixa em: {', '.join(baixas)}.")
        print("   A skill manda marcar a nota como estimativa e registrar a lacuna.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

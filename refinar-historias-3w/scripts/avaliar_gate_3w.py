"""Roda o gate 3W do Jev contra casos com gabarito e reporta acurácia e custo.

O caso 1 é o exemplo literal de `refinar-historias-3w/SKILL.md`, cujo gabarito
(os três Ws 'Fraco') está escrito na própria skill. Os demais isolam um sinal de
fraqueza por vez.

Uso: uv run python refinar-historias-3w/scripts/avaliar_gate_3w.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cliente_jev import carregar_chave, decidir  # noqa: E402
from gate_3w import PERGUNTAS, aplicar_gate, montar_state  # noqa: E402

CasoTeste = dict[str, Any]

CASOS: list[CasoTeste] = [
    {
        "nome": "exemplo-da-skill",
        "historia": "Como usuário, quero notificações para ficar informado.",
        "fonte_do_gabarito": "refinar-historias-3w/SKILL.md, seção Exemplo",
        "esperado": {"who": "fraco", "what": "fraco", "why": "fraco"},
    },
    {
        "nome": "historia-completa",
        "historia": (
            "Como auditor fiscal responsável por uma diligência em andamento, "
            "quero impedir o cancelamento de um Pré-TOAF que já recebeu lançamentos de "
            "apuração, para não perder o trabalho de apuração já registrado."
        ),
        "fonte_do_gabarito": "os três Ws atendem ao gate descrito nos passos 2 a 4",
        "esperado": {"who": "confirmado", "what": "confirmado", "why": "confirmado"},
    },
    {
        "nome": "what-orientado-a-solucao",
        "historia": (
            "Como analista de crédito do time de originação, quero um botão de exportar "
            "para Excel na tela de propostas, para conferir os valores contra a planilha "
            "do comitê antes da reunião de aprovação."
        ),
        "fonte_do_gabarito": "tabela Referência rápida: What que nomeia tela/componente",
        "esperado": {"who": "confirmado", "what": "fraco", "why": "confirmado"},
    },
    {
        "nome": "why-circular",
        "historia": (
            "Como gerente de uma agência bancária, quero acompanhar o volume de propostas "
            "aprovadas por semana, para ficar acompanhando o volume aprovado por semana."
        ),
        "fonte_do_gabarito": "passo 4: Why que repete o What com outras palavras",
        "esperado": {"who": "confirmado", "what": "confirmado", "why": "fraco"},
    },
    {
        "nome": "why-ausente",
        "historia": (
            "Como coordenador de atendimento, quero reatribuir um chamado para outra equipe."
        ),
        "fonte_do_gabarito": "passo 5: W que não consta no texto é Pendente",
        "esperado": {"who": "confirmado", "what": "confirmado", "why": "pendente"},
    },
]


def main() -> int:
    chave = carregar_chave()
    acertos = 0
    total = 0
    custo = 0.0
    tokens_entrada = 0

    for caso in CASOS:
        resposta = decidir(montar_state(caso["historia"]), PERGUNTAS, chave)
        resultado = aplicar_gate(resposta["answers"])
        uso = resposta.get("usage", {})
        custo += float(uso.get("cost", 0.0))
        tokens_entrada += int(uso.get("input_tokens", 0))

        print(f"\n{'=' * 78}")
        print(f"CASO: {caso['nome']}")
        print(f"  {caso['historia']}")
        print(f"  gabarito de: {caso['fonte_do_gabarito']}")
        print(f"{'-' * 78}")
        print(f"  {'W':<6} {'esperado':<12} {'Jev':<12} {'conf.':<7} ok")
        for w in ("who", "what", "why"):
            esperado = caso["esperado"][w]
            obtido = resultado["ws"][w]["estado"]
            conf = resultado["ws"][w]["confianca"]
            ok = esperado == obtido
            acertos += ok
            total += 1
            print(f"  {w:<6} {esperado:<12} {obtido:<12} {conf:<7.2f} {'sim' if ok else 'NAO'}")
        print(f"  estado 3W: {resultado['estado_3w']}")

    print(f"\n{'=' * 78}")
    print(f"acurácia: {acertos}/{total} julgamentos  ({acertos / total:.0%})")
    print(f"custo total: US$ {custo:.6f} em {len(CASOS)} requisições ({tokens_entrada} tokens in)")
    print(f"custo por história: US$ {custo / len(CASOS):.6f}")
    return 0 if acertos == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

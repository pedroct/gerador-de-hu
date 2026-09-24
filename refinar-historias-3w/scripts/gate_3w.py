"""Gate 3W do repo, aplicado pelo Jev.

As três perguntas e seus critérios são transcritos de `refinar-historias-3w/SKILL.md`
(passos 2 a 5 e a tabela "Referência rápida"). Nenhuma rubrica foi inventada aqui.

As três perguntas são independentes sobre o mesmo `state`, então vão numa única
requisição e são avaliadas em paralelo pelo modelo.
"""

from __future__ import annotations

from typing import Any

ESTADOS = {
    "confirmado": "Passa no gate: o W está resolvido com base no texto, sem inventar fatos.",
    "fraco": "Está presente, mas com o sinal de fraqueza dos critérios. Não passa no gate.",
    "pendente": "Não é possível identificar este W no texto. Não passa no gate.",
}


def _opcoes(sinal_de_fraqueza: str, exemplos_fracos: list[str]) -> dict[str, Any]:
    return {
        "confirmado": ESTADOS["confirmado"],
        "fraco": {
            "o_que": ESTADOS["fraco"],
            "sinal": sinal_de_fraqueza,
            "exemplos": exemplos_fracos,
        },
        "pendente": ESTADOS["pendente"],
    }


PERGUNTAS: dict[str, Any] = {
    "who": {
        "type": "choice",
        "instructions": {
            "julgamento": (
                "Avalie o W 'Who' da história em `historia`. O Who deve identificar o ator ou "
                "beneficiário cujo comportamento, necessidade ou resultado orienta a história, "
                "incluindo o contexto que altera essa necessidade."
            ),
            "regra_do_gate": (
                "Um papel genérico é suficiente APENAS quando distinguir perfis não mudaria a "
                "história. Se perfis diferentes poderiam querer resultados diferentes, um papel "
                "genérico é 'fraco'."
            ),
            "nao_infira": (
                "Não infira persona ou motivação a partir de evidência de código ou de "
                "conhecimento externo. Julgue apenas o que o texto sustenta."
            ),
        },
        "criteria": _opcoes(
            "Papel genérico como 'usuário', 'área' ou 'sistema', sem contexto relevante.",
            ["Como usuário, ...", "Como a área de negócio, ...", "Como o sistema, ..."],
        ),
    },
    "what": {
        "type": "choice",
        "instructions": {
            "julgamento": (
                "Avalie o W 'What' da história em `historia`. O What deve expressar a capacidade "
                "ou o resultado pretendido, em linguagem do domínio e independente de "
                "implementação."
            ),
            "regra_do_gate": (
                "Um What que apenas nomeia a solução não passa no gate. Teste: soluções "
                "alternativas ainda poderiam atender ao mesmo What? Se o texto já fixa a "
                "solução, é 'fraco'."
            ),
            "nao_infira": (
                "Canais, telas, APIs e componentes são restrições ou hipóteses separadas, "
                "não o What."
            ),
        },
        "criteria": _opcoes(
            "Nomeia tela, canal, API, componente ou tarefa técnica em vez da capacidade.",
            [
                "quero um botão de exportar",
                "quero receber push",
                "quero uma tela de consulta",
                "quero notificações",
            ],
        ),
    },
    "why": {
        "type": "choice",
        "instructions": {
            "julgamento": (
                "Avalie o W 'Why' da história em `historia`. O Why deve expressar a mudança útil "
                "para o ator ou o negócio: problema evitado, decisão habilitada ou resultado "
                "alcançado."
            ),
            "regra_do_gate": (
                "O Why precisa explicar o VALOR do What, não repeti-lo com outras palavras. "
                "Um Why circular é 'fraco'."
            ),
            "nao_infira": (
                "Registre evidência ou medida apenas se o texto fornecer. Vantagem não "
                "confirmada e slogan não tornam o Why 'confirmado'."
            ),
        },
        "criteria": _opcoes(
            "Paráfrase do What, slogan ou vantagem não confirmada; justificativa circular.",
            [
                "para ficar informado",
                "para facilitar",
                "para conseguir usar",
                "para melhorar a experiência",
            ],
        ),
    },
}


def montar_state(historia: str, contexto: str | None = None) -> dict[str, Any]:
    state: dict[str, Any] = {"historia": historia}
    if contexto:
        state["contexto_confirmado"] = contexto
    return state


def aplicar_gate(respostas: dict[str, Any]) -> dict[str, Any]:
    """Traduz as respostas do Jev no contrato de entrega do 3W.

    A política fica em código, como manda a skill do TypeSafe: o modelo devolve o
    julgamento por W, e a regra 'Completo só se os três passam' é determinística.
    """
    por_w = {
        w: {
            "estado": respostas[w]["choice"],
            "confianca": respostas[w]["confidence"],
            "probabilidades": respostas[w]["probabilities"],
        }
        for w in ("who", "what", "why")
    }
    completo = all(d["estado"] == "confirmado" for d in por_w.values())
    return {
        "ws": por_w,
        "estado_3w": "Completo" if completo else "Incompleto",
        "menor_confianca": min(d["confianca"] for d in por_w.values()),
    }

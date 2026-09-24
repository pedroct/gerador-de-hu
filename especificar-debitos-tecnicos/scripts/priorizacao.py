"""Priorização de débito técnico com os três primitivos do Jev.

Uma requisição cobre os passos 3 e 4 da skill:

- quatro `score` — Impacto, Probabilidade, Severidade e Esforço, cinco níveis cada;
- um `choice` — a categoria, entre as seis que a skill define;
- um `noul` — há defeito observável, o que decide entre `Bug` e `User Story`.

A aritmética da prioridade, `(Impacto + Risco) × (6 − Esforço)`, fica em código. O
modelo posiciona cada dimensão; ele não multiplica nada.

**Atenção à procedência da rubrica.** As seis categorias, a fórmula e o critério de
`Bug` vs `User Story` são transcritos do `SKILL.md`. Já as descrições dos níveis **não
existem na skill** — ela pede "notas inteiras de 1 a 5" sem dizer o que cada nota
significa. Foram redigidas aqui como situações concretas, no padrão BARS, porque nível
descrito como grau ("moderado", "alto") ou como número degrada o julgamento. São a parte
desta implementação que mais merece revisão de quem conhece o contexto, e
`retranslacao.py` verifica se continuam atraindo exemplos do próprio nível.
"""

from __future__ import annotations

from typing import Any

# Níveis do `score` são 0-indexados; a skill trabalha com notas de 1 a 5.
DESLOCAMENTO_DA_NOTA = 1

# Escala de notas que a skill pede para Impacto, Risco e Esforço.
NOTAS_DA_SKILL = 5

# Faixa de intolerância da matriz de risco. Um item aqui dentro não compete por
# eficiência: ele é restrição, não candidato. `(Impacto + Risco) × (6 − Esforço)` é uma
# métrica de eficiência, e favorecer ganho barato é o que ela serve para fazer — por
# isso um item grave e caro afunda nela. Trocá-la por WSJF não resolve: medido sobre as
# mesmas notas, o WSJF colocou um comentário desatualizado em primeiro lugar, porque ele
# também é métrica de eficiência. A prática estabelecida é classificar antes de ordenar:
# classes de serviço do Kanban, e o uso operacional do CVSS, em que severidade crítica
# fixa prazo independentemente do esforço.
#
# É uma faixa, não uma linha: severidade alta com probabilidade no piso descreve algo sem
# caminho conhecido para acontecer, e tratar isso como obrigatório esvaziaria a distinção.
SEVERIDADE_INTOLERAVEL = 4
PROBABILIDADE_MINIMA_PARA_RESTRICAO = 2

# Abaixo desta confiança na severidade, o portão não decide. Medindo débitos reais, a
# confiança da severidade caiu para 0,14–0,51, enquanto na retranslação das âncoras ela
# ficava entre 0,63 e 1,00. A diferença é que os exemplares da retranslação começavam por
# "Quando acontece, …" — diziam a consequência —, e uma descrição de débito real costuma
# relatar o defeito sem dizer o que acontece quando ele se manifesta. A âncora está boa;
# falta evidência no texto. Classificar como obrigatório, ou deixar de fazê-lo, a partir
# de um julgamento de confiança 0,14 daria ao número uma autoridade que ele não tem.
CONFIANCA_MINIMA_PARA_FAIXA = 0.60

IMPACTO = [
    "Incomoda quem lê o código, mas nenhuma entrega, operação ou evolução muda por causa disso.",
    "Custa tempo ocasional a quem mexe naquela área. Quem usa o produto não percebe, e a operação "
    "não muda.",
    "Qualquer mudança naquela área fica previsivelmente mais lenta ou mais arriscada, e a equipe "
    "já a contorna de propósito.",
    "Já provocou falha, retrabalho ou indisponibilidade observada, ou impede uma evolução que "
    "está planejada.",
    "Afeta a operação ou a segurança de forma contínua, ou impede uma entrega já comprometida "
    "com alguém.",
]

# Risco foi separado em probabilidade e severidade depois que a retranslação BARS mostrou
# a escala única puxando para cima na ponta baixa, com confiança entre 0,38 e 0,60 — o
# sintoma de pergunta multidimensional. Matrizes de risco (ISO 31000, CVSS) separam as
# duas desde sempre; o código as recombina numa nota única de 1 a 5.
#
# Reduzir a probabilidade para quatro níveis foi testado e **não melhorou** (89% contra
# 90%), então a escala permaneceu em cinco. O diagnóstico que se sustentou é outro: a
# ponta baixa depende de evidência operacional — frequência de mudança, tráfego,
# histórico de incidente — que a descrição de um débito normalmente não carrega. Passar
# essa evidência em `contexto_da_demanda` desloca a distribuição na direção certa.
PROBABILIDADE = [
    "Não há caminho conhecido para que ocorra nos próximos doze meses.",
    "Só ocorreria sob uma combinação de condições que não se observa nesta operação.",
    "Pode ocorrer nos próximos doze meses por um caminho que a operação normal percorre.",
    "É provável que ocorra nos próximos doze meses: as condições vêm se formando, ainda "
    "que não haja data.",
    "É praticamente certo que ocorra nos próximos doze meses, ou já vem ocorrendo.",
]

SEVERIDADE = [
    "O efeito é perceptível apenas por quem desenvolve. Quem usa o produto e a operação "
    "seguem normalmente.",
    "Alguém precisa refazer trabalho ou contornar à mão, sem perda de dado nem parada de serviço.",
    "Parte do serviço fica degradada ou indisponível por um período curto, e existe "
    "contorno conhecido.",
    "O serviço para, ou os dados ficam incorretos de um jeito que exige correção coordenada.",
    "Perda ou exposição de dado, quebra de obrigação contratual ou legal, ou parada sem "
    "contorno possível.",
]

ESFORCO = [
    "Mudança localizada num ponto só, já coberta por teste existente.",
    "Alguns arquivos da mesma camada, sem mudar contrato nem formato de dado.",
    "Atravessa camadas ou exige testes novos; algum contrato interno muda.",
    "Muda contrato consumido por outra parte, ou exige migração de dado coordenada.",
    "Reescrita de componente, mudança de infraestrutura ou coordenação entre equipes.",
]

CATEGORIAS = {
    "codigo": "Implementação dentro de um componente: duplicação, complexidade, acoplamento local.",
    "arquitetura": "Fronteiras entre componentes: responsabilidade mal colocada, dependência "
    "cíclica, camada furada.",
    "testes": "Ausência, fragilidade ou lentidão de teste automatizado.",
    "dependencias": "Biblioteca, runtime ou serviço externo desatualizado, sem suporte ou "
    "fixado de forma arriscada.",
    "documentacao": "Conhecimento necessário para operar ou evoluir que só existe na cabeça de "
    "alguém ou está desatualizado.",
    "infraestrutura": "Build, pipeline, ambiente, observabilidade, configuração ou "
    "provisionamento.",
}

ROTULO_DA_CATEGORIA = {
    "codigo": "Código",
    "arquitetura": "Arquitetura",
    "testes": "Testes",
    "dependencias": "Dependências",
    "documentacao": "Documentação",
    "infraestrutura": "Infraestrutura",
}

PERGUNTAS: dict[str, Any] = {
    "impacto": {
        "type": "score",
        "instructions": (
            "Qual é o efeito que este débito, descrito em `debito`, produz HOJE sobre entrega, "
            "operação, segurança, evolução ou confiabilidade? Julgue o efeito presente e "
            "observado, não o que poderia acontecer no futuro — isso é a pergunta de risco."
        ),
        "criteria": IMPACTO,
    },
    "probabilidade": {
        "type": "score",
        "instructions": (
            "Se nada for feito, qual é a chance de o débito descrito em `debito` se manifestar "
            "como incidente nos PRÓXIMOS DOZE MESES? Julgue só a chance de acontecer dentro "
            "dessa janela — o tamanho do estrago é outra pergunta."
        ),
        "criteria": PROBABILIDADE,
    },
    "severidade": {
        "type": "score",
        "instructions": (
            "SE o débito descrito em `debito` se manifestar como incidente, qual é o estrago? "
            "Julgue supondo que já aconteceu, por mais improvável que seja — a chance de ocorrer "
            "é outra pergunta."
        ),
        "criteria": SEVERIDADE,
    },
    "esforco": {
        "type": "score",
        "instructions": (
            "Quanto trabalho é preciso para remediar o débito descrito em `debito`? Julgue o "
            "alcance da mudança — quantas partes do sistema ela toca e o que precisa ser "
            "coordenado — e não a urgência nem o valor de fazê-la."
        ),
        "criteria": ESFORCO,
    },
    "categoria": {
        "type": "choice",
        "instructions": (
            "Em qual categoria o débito descrito em `debito` se enquadra melhor? Escolha pela "
            "natureza do problema, não pelo arquivo onde ele aparece."
        ),
        "criteria": CATEGORIAS,
    },
    "ha_defeito_observavel": {
        "type": "noul",
        "instructions": (
            "O débito descrito em `debito` inclui um comportamento ATUAL incorreto em relação a "
            "um requisito, contrato ou regra já estabelecida — isto é, o sistema hoje faz algo "
            "errado, não apenas algo mal organizado?"
        ),
        "criteria": {
            "true": (
                "Há comportamento observável que contraria regra, contrato ou requisito já "
                "acordado; o dano é corrigir o que o sistema faz."
            ),
            "false": (
                "Trata-se de manutenibilidade, redução de risco ou capacidade técnica ausente, "
                "sem defeito observável a corrigir."
            ),
        },
    },
}

DIMENSOES_PONTUADAS = ("impacto", "probabilidade", "severidade", "esforco")


def montar_state(debito: str, contexto: str | None = None) -> dict[str, Any]:
    state: dict[str, Any] = {"debito": debito}
    if contexto:
        state["contexto_da_demanda"] = contexto
    return state


def _nota(resposta: dict[str, Any]) -> int:
    """Converte o score ponderado na nota inteira de 1 a 5 que a skill pede."""
    nivel: int = round(float(resposta["score"]))
    return nivel + DESLOCAMENTO_DA_NOTA


def _risco_cru(probabilidade: dict[str, Any], severidade: dict[str, Any]) -> float:
    """Combina probabilidade e severidade na forma clássica de matriz de risco.

    **Cada escala é normalizada pelo próprio máximo.** A doc do TypeSafe é explícita:
    scores de escalas de comprimento diferente precisam ser divididos pelo respectivo
    nível máximo antes de combinar. Dividir ambos pelo mesmo número faria a escala mais
    curta pesar mais. Hoje as duas têm cinco níveis, então o erro ficaria dormente.

    O produto normalizado é a forma de perda esperada: frequente e cosmético permanece
    baixo, raro e catastrófico permanece relevante.
    """
    p = float(probabilidade["score"]) / (len(PROBABILIDADE) - 1)
    s = float(severidade["score"]) / (len(SEVERIDADE) - 1)
    return p * s * (NOTAS_DA_SKILL - 1)


def _combinar_risco(probabilidade: dict[str, Any], severidade: dict[str, Any]) -> int:
    """Nota de risco de 1 a 5, derivada da matriz."""
    return round(_risco_cru(probabilidade, severidade)) + DESLOCAMENTO_DA_NOTA


def priorizar(respostas: dict[str, Any]) -> dict[str, Any]:
    """Aplica os passos 3 e 4 da skill sobre as respostas do Jev."""
    impacto = _nota(respostas["impacto"])
    esforco = _nota(respostas["esforco"])
    risco = _combinar_risco(respostas["probabilidade"], respostas["severidade"])
    prioridade = (impacto + risco) * (6 - esforco)

    # O score fracionário não entra na nota, mas desempata itens de mesma prioridade:
    # é julgamento cru reaproveitável, e recalculá-lo não exige nova inferência.
    desempate = (
        float(respostas["impacto"]["score"])
        + _risco_cru(respostas["probabilidade"], respostas["severidade"])
        - float(respostas["esforco"]["score"])
    )

    confiancas = {d: respostas[d]["confidence"] for d in DIMENSOES_PONTUADAS}

    return {
        "categoria": ROTULO_DA_CATEGORIA[respostas["categoria"]["choice"]],
        "tipo_sugerido": "Bug"
        if respostas["ha_defeito_observavel"]["noul"] > 0.5
        else "User Story",
        "impacto": impacto,
        "risco": risco,
        "esforco": esforco,
        "probabilidade": _nota(respostas["probabilidade"]),
        "severidade": _nota(respostas["severidade"]),
        "prioridade": prioridade,
        "desempate": round(desempate, 3),
        "confiancas": confiancas,
        "menor_confianca": min(confiancas.values()),
        "scores_crus": {d: respostas[d]["score"] for d in DIMENSOES_PONTUADAS},
    }


def ordenar(itens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordena por prioridade e desempata pelo score fracionário."""
    return sorted(itens, key=lambda i: (i["prioridade"], i["desempate"]), reverse=True)


def faixa(item: dict[str, Any]) -> str:
    """Classifica o item em `restricao`, `a_confirmar` ou `candidato`.

    `a_confirmar` não é um meio-termo de gravidade: é a recusa de decidir com evidência
    insuficiente. O que falta, quase sempre, é a descrição não dizer o que acontece
    quando o débito se manifesta.
    """
    if item["confiancas"]["severidade"] < CONFIANCA_MINIMA_PARA_FAIXA:
        return "a_confirmar"
    if (
        item["severidade"] >= SEVERIDADE_INTOLERAVEL
        and item["probabilidade"] >= PROBABILIDADE_MINIMA_PARA_RESTRICAO
    ):
        return "restricao"
    return "candidato"


def e_restricao(item: dict[str, Any]) -> bool:
    """Atalho para a faixa de intolerância, já com a confiança respeitada."""
    return faixa(item) == "restricao"


def _por_gravidade(item: dict[str, Any]) -> tuple[int, int, int]:
    return (item["risco"], item["severidade"], item["impacto"])


def separar_em_faixas(itens: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Separa restrições, pendências e candidatos, ordenando cada faixa como lhe cabe.

    As restrições não são ordenadas por eficiência — o esforço não as desempata. Saem por
    gravidade: risco, depois severidade, depois impacto. Os candidatos seguem na fórmula
    da skill, que para eles funciona. As pendências saem pelo mesmo critério de gravidade,
    porque o que se quer é olhar as piores primeiro.
    """
    destino = {
        "restricao": "restricoes",
        "a_confirmar": "a_confirmar",
        "candidato": "candidatos",
    }
    grupos: dict[str, list[dict[str, Any]]] = {v: [] for v in destino.values()}
    for item in itens:
        grupos[destino[faixa(item)]].append(item)

    grupos["restricoes"].sort(key=_por_gravidade, reverse=True)
    grupos["a_confirmar"].sort(key=_por_gravidade, reverse=True)
    grupos["candidatos"] = ordenar(grupos["candidatos"])
    return grupos


def sinalizar_inversoes(itens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aponta pares em que a fórmula coloca um item de menor impacto à frente de outro.

    Vale para a faixa de candidatos: entre eles, a fórmula ainda pode inverter a ordem de
    impacto quando o esforço difere muito, e isso é a fórmula funcionando como métrica de
    eficiência, não um erro de julgamento. A função não a corrige; mostra onde inverteu,
    para que a pessoa decida. Os itens da faixa de restrição já saíram dessa fila.
    """
    ordenados = ordenar(itens)
    inversoes: list[dict[str, Any]] = []
    for pos, acima in enumerate(ordenados):
        for abaixo in ordenados[pos + 1 :]:
            if acima["impacto"] < abaixo["impacto"]:
                inversoes.append(
                    {
                        "acima": acima,
                        "abaixo": abaixo,
                        "porque": (
                            f"esforço {acima['esforco']} contra {abaixo['esforco']} "
                            f"inverteu impacto {acima['impacto']} contra {abaixo['impacto']}"
                        ),
                    }
                )
    return inversoes

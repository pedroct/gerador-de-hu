"""Política de roteamento, em código.

A tabela abaixo é transcrição do fluxo documentado no README (seção "O que o projeto
faz" e "Fluxo de publicação autorizada"). Ela é determinística de propósito: o Jev
não decide qual skill chamar, decide o que o material é. Mudar o pipeline é editar
esta tabela, sem tocar no modelo nem reexecutar inferência.
"""

from __future__ import annotations

from typing import Any

# Acima deste valor um `noul` é tratado como verdadeiro. Provisório: precisa ser
# medido sobre material real antes de virar padrão.
LIMIAR_NOUL = 0.5

# As companheiras são sugestões opcionais que custam tempo de quem lê. Exigem
# evidência mais forte que uma decisão de rota, por isso o limiar é mais alto.
LIMIAR_COMPANHEIRA = 0.75

# Abaixo desta confiança o roteador não decide sozinho; devolve as alternativas
# para a pessoa escolher.
LIMIAR_CONFIANCA = 0.60

REFINAMENTO = {
    "ator_objetivo_ou_valor_vagos": "refinar-historias-3w",
    "falta_conversa_e_confirmacao": "refinar-historias-3c",
    "regras_confirmadas_sem_exemplos": "refinar-historias-gherkin",
}

# Tipos de entrada para os quais faz sentido sugerir as análises especializadas.
TIPOS_COM_ANALISES = {"id_demanda_azure_boards", "pedido_informal_negocio", "spec_escrita"}


def _principal(tipo: str, noul: dict[str, float], refinamento: str) -> tuple[str | None, str]:
    """Devolve (skill, justificativa) para a rota principal."""
    if tipo == "id_demanda_azure_boards":
        return "redigir-spec-demanda-azure-boards", "há ID de Demanda já registrada no board"
    if tipo == "pedido_informal_negocio":
        return "redigir-spec-pedido-negocio", "pedido informal sem spec escrita"
    if tipo == "spec_escrita":
        if noul["tem_lacunas_abertas"] > LIMIAR_NOUL:
            return (
                "entrevistar-lacunas-requisito",
                "a spec tem pendências em aberto; gerar backlog agora produziria Histórias "
                "'Não pronta' em massa",
            )
        return "gerar-backlog-azure-boards", "spec sem pendências declaradas, pronta para decompor"
    if tipo == "backlog_markdown":
        if noul["ja_existe_demanda_no_board"] > LIMIAR_NOUL:
            return (
                "publicar-backlog-demanda-azure-boards",
                "os Épicos devem nascer como filhos da Demanda existente",
            )
        return "publicar-backlog-azure-boards", "não há Demanda de origem; Épicos soltos no projeto"
    if tipo == "historia_individual":
        skill = REFINAMENTO.get(refinamento)
        if skill:
            return skill, f"lacuna de refinamento identificada: {refinamento}"
        return None, "história individual sem lacuna de refinamento identificável"
    if tipo == "documento_de_referencia":
        return (
            None,
            "documento de padrão ou diretriz; não é requisito a decompor, e serve de contexto "
            "para as skills que investigam",
        )
    if tipo == "documento_companheiro":
        return (
            None,
            "artefato derivado de uma spec, consumido por outra etapa; a spec de origem é que "
            "segue o fluxo",
        )
    if tipo == "regras_de_negocio_confirmadas":
        return (
            "refinar-historias-gherkin",
            "regras já acordadas; falta convertê-las em exemplos verificáveis",
        )
    if tipo == "debito_tecnico":
        return "especificar-debitos-tecnicos", "observação técnica interna, sem demanda de negócio"
    return None, "o material não é insumo de requisito reconhecido"


def _companheiras(tipo: str, noul: dict[str, float]) -> list[dict[str, str]]:
    """Análises opcionais que o README marca como condicionais, nunca automáticas."""
    sugestoes: list[dict[str, str]] = []
    if tipo not in TIPOS_COM_ANALISES:
        return sugestoes
    if noul["descreve_interacao_de_tela"] > LIMIAR_COMPANHEIRA:
        sugestoes.append(
            {
                "skill": "especificar-telas-ux-ui",
                "porque": (
                    "o texto descreve interação de tela; quem confirma se há tela nova é a "
                    "skill, por inspeção de código"
                ),
            }
        )
    if noul["tem_copy_de_interface"] > LIMIAR_COMPANHEIRA:
        sugestoes.append(
            {
                "skill": "revisar-textos-requisitos",
                "porque": "há texto que será exibido ao usuário final",
            }
        )
    if noul["menciona_debito_tecnico"] > LIMIAR_COMPANHEIRA and tipo != "debito_tecnico":
        sugestoes.append(
            {
                "skill": "especificar-debitos-tecnicos",
                "porque": "há problema técnico interno que merece registro próprio",
            }
        )
    return sugestoes


def rotear(respostas: dict[str, Any]) -> dict[str, Any]:
    """Traduz as respostas do Jev numa recomendação de rota."""
    tipo_resp = respostas["tipo_de_entrada"]
    tipo = tipo_resp["choice"]
    confianca = tipo_resp["confidence"]
    noul = {
        chave: respostas[chave]["noul"]
        for chave in (
            "tem_lacunas_abertas",
            "ja_existe_demanda_no_board",
            "descreve_interacao_de_tela",
            "tem_copy_de_interface",
            "menciona_debito_tecnico",
        )
    }
    refinamento = respostas["lacuna_de_refinamento"]["choice"]

    skill, justificativa = _principal(tipo, noul, refinamento)

    # Confiança baixa não invalida o julgamento: muda quem decide.
    alternativas: list[str] = []
    if confianca < LIMIAR_CONFIANCA:
        ordenadas = sorted(
            tipo_resp["probabilities"].items(), key=lambda item: item[1], reverse=True
        )
        alternativas = [nome for nome, _ in ordenadas[:3]]

    return {
        "tipo_de_entrada": tipo,
        "confianca": confianca,
        "skill": skill,
        "porque": justificativa,
        "decidir_com_a_pessoa": confianca < LIMIAR_CONFIANCA,
        "alternativas": alternativas,
        "tambem_considerar": _companheiras(tipo, noul),
        "sinais": noul,
    }

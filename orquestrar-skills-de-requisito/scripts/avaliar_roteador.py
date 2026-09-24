"""Testa o roteador contra casos com gabarito, cobrindo todas as rotas do README.

Uso: uv run python orquestrar-skills-de-requisito/scripts/avaliar_roteador.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cliente_jev import carregar_chave, decidir  # noqa: E402
from perguntas import PERGUNTAS  # noqa: E402
from roteamento import rotear  # noqa: E402

CasoTeste = dict[str, Any]

CASOS: list[CasoTeste] = [
    {
        "nome": "id-de-demanda",
        "material": "Preciso trabalhar a Demanda de Negócio 13959 que a área abriu no board.",
        "skill": "redigir-spec-demanda-azure-boards",
        "companheiras": [],
    },
    {
        "nome": "pedido-informal",
        "material": (
            "E-mail da Fiscalização: 'Pessoal, está acontecendo de dois auditores cancelarem "
            "o mesmo Pré-TOAF quase ao mesmo tempo, e aí o segundo cancelamento apaga as "
            "apurações que o primeiro já tinha lançado. Isso já deu retrabalho três vezes "
            "esse mês. Dá para resolver?'"
        ),
        "skill": "redigir-spec-pedido-negocio",
        "companheiras": [],
    },
    {
        "nome": "spec-com-lacunas",
        "material": (
            "# Spec: Encerramento de diligência\n\n"
            "## 2. Requisitos\n"
            "2.1 O sistema deve impedir o cancelamento de um Pré-TOAF com lançamentos.\n"
            "2.2 O auditor deve ser avisado de que há lançamentos vinculados.\n\n"
            "## Lacunas e perguntas abertas\n"
            "- O bloqueio vale também para o supervisor, ou ele pode forçar o cancelamento?\n"
            "- A janela de 24 horas se aplica aqui? [a confirmar com a área]\n"
        ),
        "skill": "entrevistar-lacunas-requisito",
        "companheiras": [],
    },
    {
        "nome": "spec-sem-lacunas",
        "material": (
            "# Spec: Reabertura de diligência\n\n"
            "## 1. Contexto\n"
            "A área confirmou todas as regras em reunião de 12/09.\n\n"
            "## 2. Requisitos\n"
            "2.1 Reabertura permitida em até 24 horas após a conclusão.\n"
            "2.2 A reabertura exige justificativa textual obrigatória.\n"
            "2.3 Ao reabrir, o status volta para 'Em análise'.\n\n"
            "## Lacunas e perguntas abertas\n"
            "Nenhuma.\n"
        ),
        "skill": "gerar-backlog-azure-boards",
        "companheiras": [],
    },
    {
        "nome": "backlog-vinculado-a-demanda",
        "material": (
            "# Backlog para Azure Boards\n\n"
            "## Metadados e cobertura\n"
            "- Spec de origem: spec gerada a partir da Demanda de Negócio 13959\n\n"
            "## 1.0.0 [Epic] Encerramento de diligência\n\n"
            "### 1.1.0 [Feature] Cancelamento do Pré-TOAF\n"
            "#### Parent\n`1.0.0`\n"
        ),
        "skill": "publicar-backlog-demanda-azure-boards",
        "companheiras": [],
    },
    {
        "nome": "backlog-solto",
        "material": (
            "# Backlog para Azure Boards\n\n"
            "## Metadados e cobertura\n"
            "- Spec de origem: seção 2 da spec de diligências\n"
            "- Modo: Greenfield\n\n"
            "## 1.0.0 [Epic] Reabrir diligências\n\n"
            "### 1.1.0 [Feature] Reabertura dentro do prazo\n"
            "#### Parent\n`1.0.0`\n"
        ),
        "skill": "publicar-backlog-azure-boards",
        "companheiras": [],
    },
    {
        "nome": "historia-com-3w-vago",
        "material": "Como usuário, quero notificações para ficar informado.",
        "skill": "refinar-historias-3w",
        "companheiras": [],
    },
    {
        "nome": "historia-sem-confirmacao",
        "material": (
            "Como auditor fiscal responsável por uma diligência, quero ser impedido de "
            "cancelar um Pré-TOAF que já tem lançamentos de apuração, para não perder o "
            "trabalho já registrado. Ainda não conversamos sobre o que acontece quando o "
            "supervisor tenta cancelar, e não há exemplos acordados do comportamento."
        ),
        "skill": "refinar-historias-3c",
        "companheiras": [],
    },
    {
        "nome": "regras-confirmadas-sem-exemplos",
        "material": (
            "A área já confirmou e assinou as regras: reabertura só até 24 horas após a "
            "conclusão; justificativa obrigatória com no mínimo 20 caracteres; ao reabrir, "
            "o status volta para 'Em análise'. Tudo isso está acordado. Falta escrever os "
            "cenários verificáveis correspondentes."
        ),
        "skill": "refinar-historias-gherkin",
        "companheiras": [],
    },
    {
        "nome": "debito-tecnico",
        "material": (
            "Reparei que a camada de repositório repete a query de saldo em três serviços "
            "diferentes, cada um com um filtro de data ligeiramente distinto. Não tem teste "
            "cobrindo nenhuma delas."
        ),
        "skill": "especificar-debitos-tecnicos",
        "companheiras": [],
    },
    {
        "nome": "pedido-com-tela-e-copy",
        "material": (
            "Ticket do suporte: 'Os analistas pedem uma forma de ver, na consulta de "
            "propostas, quais estão paradas há mais de 5 dias. Hoje precisam abrir uma a "
            "uma. E quando não há nenhuma parada, a mensagem que aparece é "
            '"Nenhum registro.", que eles acham seca demais — queriam algo como '
            '"Tudo em dia! Nenhuma proposta parada."\''
        ),
        "skill": "redigir-spec-pedido-negocio",
        "companheiras": ["especificar-telas-ux-ui", "revisar-textos-requisitos"],
    },
]


def main() -> int:
    chave = carregar_chave()
    acertos_rota = 0
    acertos_comp = 0
    custo = 0.0

    for caso in CASOS:
        resposta = decidir({"material": caso["material"]}, PERGUNTAS, chave)
        r = rotear(resposta["answers"])
        custo += float(resposta.get("usage", {}).get("cost", 0.0))

        obtidas = sorted(s["skill"] for s in r["tambem_considerar"])
        esperadas = sorted(caso["companheiras"])
        ok_rota = r["skill"] == caso["skill"]
        ok_comp = obtidas == esperadas
        acertos_rota += ok_rota
        acertos_comp += ok_comp

        print(f"\n{'=' * 78}")
        print(f"CASO: {caso['nome']}   [{'OK' if ok_rota and ok_comp else 'FALHOU'}]")
        print(f"  tipo detectado : {r['tipo_de_entrada']}  (conf. {r['confianca']:.2f})")
        print(f"  skill esperada : {caso['skill']}")
        print(f"  skill obtida   : {r['skill']}")
        print(f"  porque         : {r['porque']}")
        if esperadas or obtidas:
            print(f"  companheiras esperadas : {esperadas or '—'}")
            print(f"  companheiras obtidas   : {obtidas or '—'}")
        if r["decidir_com_a_pessoa"]:
            print(f"  >> confiança baixa; alternativas: {r['alternativas']}")

    total = len(CASOS)
    print(f"\n{'=' * 78}")
    print(f"rota principal : {acertos_rota}/{total} ({acertos_rota / total:.0%})")
    print(f"companheiras   : {acertos_comp}/{total} ({acertos_comp / total:.0%})")
    print(f"custo total    : US$ {custo:.6f}  |  por roteamento: US$ {custo / total:.6f}")
    return 0 if acertos_rota == total and acertos_comp == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

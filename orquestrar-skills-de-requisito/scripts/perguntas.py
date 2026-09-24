"""Perguntas do roteador de skills, julgadas pelo Jev.

Desenho: o modelo julga APENAS o que o material é e em que estado está. Qual skill
chamar é derivado em `roteamento.py`, a partir do fluxo documentado no README. Esse
fluxo é regra conhecida e acíclica — não pertence ao modelo. Se o pipeline mudar,
muda a tabela em código, sem reexecutar inferência.

As perguntas são independentes sobre o mesmo `state`, então vão numa única
requisição. Várias são especulativas: valem só para alguns tipos de entrada, e o
código consome apenas as aplicáveis (padrão "speculative fan-out").
"""

from __future__ import annotations

from typing import Any

PERGUNTAS: dict[str, Any] = {
    # ---- Pergunta primária: o que é este material? -------------------------
    "tipo_de_entrada": {
        "type": "choice",
        "instructions": {
            "julgamento": (
                "O campo `material` contém o que uma pessoa trouxe para trabalhar em "
                "requisitos de software. Classifique o que esse material É, pela sua forma "
                "e origem — não pelo que se deseja fazer com ele."
            ),
            "desempate": (
                "Decida pela forma do documento, não pelo assunto. Um texto sobre backlog "
                "não é um backlog; um pedido que cita uma tela continua sendo pedido informal."
            ),
        },
        "criteria": {
            "id_demanda_azure_boards": {
                "o_que": (
                    "Uma referência a uma Demanda de Negócio que JÁ existe no Azure Boards, "
                    "tipicamente um número de ID, com pouco ou nenhum texto de requisito junto."
                ),
                "nao_cobre": "Texto de requisito extenso sem nenhum identificador de item remoto.",
                "exemplos": ["Demanda 13959", "preciso trabalhar o item 13959 do board"],
            },
            "pedido_informal_negocio": {
                "o_que": (
                    "Um pedido em linguagem corrente vindo da área de negócio — e-mail, "
                    "ticket, mensagem, ata — que descreve um problema ou necessidade sem "
                    "estrutura de especificação."
                ),
                "nao_cobre": "Documento já organizado em seções de especificação.",
                "exemplos": [
                    "e-mail pedindo que o sistema pare de permitir cancelamento duplicado",
                    "mensagem do gestor relatando retrabalho na conferência",
                ],
            },
            "spec_escrita": {
                "o_que": (
                    "Uma especificação já redigida e estruturada, com seções, requisitos "
                    "numerados ou rastreabilidade — o insumo de quem vai decompor em backlog."
                ),
                "nao_cobre": "Backlog já decomposto em Épico, Feature e História.",
                "exemplos": [
                    "documento com seções '## Requisitos' e '## Lacunas e perguntas abertas'"
                ],
            },
            "backlog_markdown": {
                "o_que": (
                    "Um backlog JÁ decomposto na hierarquia Épico / Feature / História ou Bug, "
                    "normalmente com chaves numéricas como 1.0.0 e campos Parent."
                ),
                "nao_cobre": "Spec que ainda não foi decomposta.",
                "exemplos": ["documento com '## 1.0.0 [Epic]' e '#### Parent'"],
            },
            "historia_individual": {
                "o_que": (
                    "Uma única história de usuário, requisito ou critério de aceitação solto, "
                    "que a pessoa quer refinar — sem a estrutura de uma spec nem de um backlog."
                ),
                "nao_cobre": "Conjunto de requisitos organizados como documento.",
                "exemplos": ["Como usuário, quero exportar o relatório para conferir os valores."],
            },
            "regras_de_negocio_confirmadas": {
                "o_que": (
                    "Um conjunto de regras de negócio JÁ acordadas e confirmadas com a área, "
                    "apresentadas para serem convertidas em exemplos verificáveis."
                ),
                "nao_cobre": (
                    "Regras ainda em discussão, hipóteses, ou pedido para descobrir as regras."
                ),
                "exemplos": ["a área confirmou: reabertura só até 24h, justificativa obrigatória"],
            },
            "debito_tecnico": {
                "o_que": (
                    "A observação de um problema interno de código, arquitetura, teste ou "
                    "infraestrutura, sem demanda de negócio associada."
                ),
                "nao_cobre": "Bug com efeito visível para o usuário, relatado pelo negócio.",
                "exemplos": ["a camada de repositório duplica a query de saldo em três lugares"],
            },
            "outro": {
                "o_que": "Nada acima descreve o material, ou ele não é insumo de requisito.",
                "exemplos": ["uma pergunta sobre como usar a ferramenta"],
            },
        },
    },
    # ---- Especulativas: só algumas rotas as consomem -----------------------
    "tem_lacunas_abertas": {
        "type": "noul",
        "instructions": (
            "Supondo que `material` seja uma especificação escrita: ela contém perguntas, "
            "decisões pendentes ou pontos explicitamente não resolvidos, que precisariam de "
            "resposta de alguém antes de virar backlog? Julgue apenas pelo texto presente."
        ),
        "criteria": {
            "true": (
                "Há pontos em aberto declarados — seção de lacunas, perguntas sem resposta, "
                "marcações do tipo 'a definir', 'a confirmar' ou decisão pendente."
            ),
            "false": ("O material não expõe pendências, ou não é uma especificação escrita."),
        },
    },
    "ja_existe_demanda_no_board": {
        "type": "noul",
        "instructions": (
            "O material indica que já existe uma Demanda de Negócio registrada no Azure Boards "
            "à qual este trabalho pertence — por exemplo citando o número dela ou dizendo que "
            "a demanda foi aberta?"
        ),
        "criteria": {
            "true": "Há referência explícita a um item de Demanda já existente no board.",
            "false": "Nenhuma referência a item já registrado no board.",
        },
    },
    "descreve_interacao_de_tela": {
        "type": "noul",
        "instructions": (
            "O texto de `material` DESCREVE EXPLICITAMENTE uma pessoa interagindo com uma "
            "interface visual — ver uma lista, abrir um registro, preencher um campo, clicar, "
            "navegar entre telas? Julgue o que está escrito, não o que seria necessário "
            "implementar. Quase todo requisito de um sistema web acaba tocando alguma tela; "
            "isso NÃO basta para responder verdadeiro."
        ),
        "criteria": {
            "true": (
                "O texto menciona concretamente a experiência de uso: uma visualização, uma "
                "consulta, um campo, uma listagem, uma navegação ou um passo manual que a "
                "pessoa executa na interface."
            ),
            "false": (
                "O texto trata de regra, cálculo, permissão, processamento, integração, dado "
                "ou estrutura, sem descrever o que a pessoa vê ou faz na interface — ainda "
                "que a implementação venha a exigir tela."
            ),
        },
    },
    "tem_copy_de_interface": {
        "type": "noul",
        "instructions": (
            "O material contém texto que será EXIBIDO ao usuário final no produto — rótulo, "
            "mensagem de erro, aviso, instrução de tela, e-mail transacional?"
        ),
        "criteria": {
            "true": "Há trecho literal destinado a aparecer para o usuário do produto.",
            "false": (
                "Todo o texto é descrição de requisito para a equipe, não conteúdo de interface."
            ),
        },
    },
    "menciona_debito_tecnico": {
        "type": "noul",
        "instructions": (
            "O material relata a ESTRUTURA INTERNA do software como problema — código "
            "duplicado, acoplamento, ausência de teste, dívida de arquitetura, infraestrutura? "
            "Um problema de comportamento relatado pelo negócio é requisito, não débito, ainda "
            "que sua causa seja técnica."
        ),
        "criteria": {
            "true": (
                "O texto aponta a organização interna do código, do teste ou da "
                "infraestrutura como o problema em si."
            ),
            "false": (
                "O texto relata o que o produto faz de errado do ponto de vista de quem o usa, "
                "ou não relata problema técnico algum."
            ),
        },
    },
    # ---- Especulativa: qual rubrica de refinamento falta -------------------
    "lacuna_de_refinamento": {
        "type": "choice",
        "instructions": {
            "julgamento": (
                "Supondo que `material` seja uma história de usuário individual: qual é a "
                "lacuna MAIS limitante para que ela possa ser desenvolvida?"
            ),
            "desempate": (
                "Se mais de uma lacuna existe, escolha a mais básica: sem ator, objetivo ou "
                "valor claros, não adianta discutir exemplos."
            ),
        },
        "criteria": {
            "ator_objetivo_ou_valor_vagos": (
                "Quem vive a necessidade, o que se quer alcançar ou por que isso vale não "
                "estão claros; ou o objetivo está escrito como solução técnica."
            ),
            "falta_conversa_e_confirmacao": (
                "Ator, objetivo e valor estão claros, mas não há registro de decisões "
                "acordadas nem de como o comportamento será confirmado."
            ),
            "regras_confirmadas_sem_exemplos": (
                "As regras de negócio já estão confirmadas e acordadas, faltando apenas "
                "convertê-las em exemplos verificáveis."
            ),
            "nao_aplicavel": "O material não é uma história de usuário individual.",
        },
    },
}

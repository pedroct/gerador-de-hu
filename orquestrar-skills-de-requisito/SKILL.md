---
name: orquestrar-skills-de-requisito
description: Use quando alguém traz material de requisito — ID de Demanda, pedido informal, spec, backlog, história solta, regras acordadas ou observação técnica — e é preciso decidir qual skill do gerador de HU deve ser chamada, ou quando a pessoa pergunta por onde começar.
---

# Orquestrar as skills de requisito

## Objetivo

Decidir qual skill deste repositório atende ao material que a pessoa trouxe, e quais análises
opcionais valem a pena junto. Esta skill **roteia e explica**; não redige spec, não refina história
e não gera nem publica backlog. Ela termina indicando a próxima skill e o porquê.

## Como rotear

O roteamento tem duas partes, e a separação é deliberada:

1. **O que o material é** — julgamento semântico sobre o texto. É a parte que exige leitura.
2. **Qual skill isso implica** — consequência determinística do fluxo do repositório, na tabela
   abaixo. Não é opinião; não renegocie a tabela caso a caso.

| O material é | Rota | Condição |
|---|---|---|
| ID de Demanda de Negócio já no board | `redigir-spec-demanda-azure-boards` | — |
| Pedido informal (e-mail, ticket, mensagem) | `redigir-spec-pedido-negocio` | — |
| Spec escrita **com** pendências em aberto | `entrevistar-lacunas-requisito` | fechar antes de decompor |
| Spec escrita **sem** pendências | `gerar-backlog-azure-boards` | — |
| Backlog Markdown, originado de uma Demanda | `publicar-backlog-demanda-azure-boards` | Épicos nascem filhos da Demanda |
| Backlog Markdown, sem Demanda de origem | `publicar-backlog-azure-boards` | Épicos soltos no projeto |
| História solta com ator, objetivo ou valor vagos | `refinar-historias-3w` | — |
| História com 3W claro, sem conversa nem confirmação | `refinar-historias-3c` | 3C define a prontidão geral |
| Regras de negócio já acordadas | `refinar-historias-gherkin` | só regras confirmadas viram exemplo |
| Observação sobre a estrutura interna do código | `especificar-debitos-tecnicos` | — |

Análises opcionais, sempre **sugestão** e nunca chamada automática — quem decide rodá-las é a
pessoa:

| Sinal no material | Sugira |
|---|---|
| Descreve interação com interface visual | `especificar-telas-ux-ui` |
| Contém texto que será exibido ao usuário final | `revisar-textos-requisitos` |
| Relata problema de estrutura interna, além da necessidade principal | `especificar-debitos-tecnicos` |

## Quando usar o julgamento assistido

Quando o material for ambíguo — ou quando você precisar de um sinal auditável em vez da sua
própria impressão —, rode:

```bash
uv run python orquestrar-skills-de-requisito/scripts/rotear.py caminho/do/material.md
```

O script consulta o modelo Jev, que devolve o tipo do material com distribuição de probabilidade
e confiança, e aplica a tabela acima em código. Requer `JEV_OPENROUTER_API` no `.env`.

Use-o sobretudo nestes três casos, que concentram os erros:

- **Spec ou backlog?** Um texto sobre backlog não é um backlog. Decida pela forma do documento.
- **Pedido informal ou débito técnico?** Um problema de comportamento relatado pelo negócio é
  requisito, ainda que a causa seja técnica. Débito é quando a estrutura interna é o problema.
- **História solta ou regras acordadas?** Regras já confirmadas vão para Gherkin, não para 3W.

## Como tratar a confiança

A confiança diz **quem decide**, não se a resposta está certa.

- **Alta** — siga a rota e diga qual skill e por quê.
- **Abaixo de 0,60** — o script marca `decidir_com_a_pessoa`. Não escolha sozinho: apresente as
  duas ou três alternativas mais prováveis e pergunte. Rota errada custa uma skill inteira rodada
  à toa.
- **Nunca** use a confiança como se fosse qualidade do material. Uma história ruim pode ser
  classificada com confiança 1,00; são coisas diferentes.

## Limite da skill

Roteie e explique. Não execute a skill de destino sem que a pessoa confirme, e não encadeie várias
rotas de uma vez: o fluxo do repositório é deliberadamente manual entre as etapas, com revisão
humana no meio. Publicação nunca é roteada automaticamente — as duas publicadoras exigem frase de
autorização própria.

---
name: publicar-backlog-demanda-azure-boards
description: Use quando um backlog Markdown já revisado precisa ser publicado no Azure Boards vinculado a uma Demanda de Negócio existente, informada por ID, e somente após autorização textual explícita.
---

# Publicar backlog vinculado a uma Demanda de Negócio

## Objetivo

Conduza a validação e a publicação de um backlog Markdown já revisado, pendurando toda a hierarquia
em uma Demanda de Negócio que já existe no Azure Boards. Esta skill coordena a CLI e os componentes
do pacote; ela não inventa regras, campos ou caminhos que não estejam no backlog ou na Demanda, e não
afirma que a publicação acontece automaticamente.

O resultado no board é este:

```text
Demanda de Negócio #13959
└─ [Epic]        01 Gestão do projeto
   └─ [Feature]  01.01 Gestão do projeto
      └─ [Story] 01.01.01 Análise de padrões de stacks
```

## Fluxo obrigatório

1. Carregue o backlog e execute `validar`; a CLI usa sua própria cópia embarcada do contrato
   estrutural (módulo `contrato_backlog.py`) antes de interpretar ou planejar. Essa cópia não depende
   de `gerar-backlog-azure-boards` em tempo de execução e precisa ser ressincronizada manualmente se
   as regras da skill geradora mudarem.
2. Carregue a configuração, incluindo o ID da Demanda. Este é o único comando que **não** precisa de
   credencial: `validar` é conferência estrutural local.
3. Leia a Demanda por `GET` e valide o tipo, o projeto e os campos. A leitura interrompe o fluxo
   quando o work item não existe, é de outro tipo, pertence a outro projeto ou não tem `AreaPath` e
   `IterationPath` — não há de onde herdar o destino.
4. Derive `Area Path` e `Iteration Path` da Demanda e monte o plano. O ID entra no hash, de modo que
   o mesmo backlog sob outra Demanda é outro plano.
5. Execute a verificação preliminar somente leitura: credencial, destino, tipos, campos, relação
   hierárquica e caminhos. Os Épicos são validados com a Demanda como pai, para que
   `--validar-apenas` exercite o vínculo em vez de conferir um Épico órfão.
6. Apresente o plano com a Demanda de origem, destino, mapeamento remoto de tipos, quantidades,
   ordem, relações, quais chaves sobem como filhas diretas da Demanda, manifesto e hash.
   **Se algum item tiver critérios de aceitação e o tipo remoto não expuser o campo, avise antes
   da autorização, nomeando os itens.** A criação omite o campo em vez de falhar, e sem o aviso
   quem autoriza acredita estar publicando critérios que nunca chegam ao Azure Boards. É o caso do
   tipo `Bug` em processos que só oferecem `Microsoft.VSTS.Common.AcceptanceCriteria` na
   `User Story`.
7. Pergunte se a pessoa autoriza o backlog inteiro, por lotes ou o cancelamento. Em lotes, pergunte o
   tamanho e apresente cada lote novamente.
8. Mostre a frase completa e solicite que a pessoa a digite exatamente. A frase começa com
   `AUTORIZAR PUBLICAÇÃO` para o backlog inteiro ou `AUTORIZAR LOTE` para um lote, e **nomeia a
   Demanda**.
9. Só depois da confirmação válida, chame a execução sequencial. O manifesto é atualizado após cada
   criação para permitir retomada com nova autorização.

Confirmação ausente, vaga, incorreta ou vinculada a outro hash resulta em
**zero chamadas de criação**. Uma frase emitida para uma Demanda não autoriza publicar sob outra, e um manifesto de uma
Demanda não retoma sob outra. Após uma falha parcial, preserve o manifesto, corrija a causa e exija
nova autorização. Timeout ou resposta ambígua de criação nunca autoriza repetir o POST: interrompa
com o manifesto bloqueado e exija reconciliação manual no Azure Boards antes de nova escrita. Não use
`--yes`, confirmação implícita, manifesto como autorização, exclusão, rollback ou atualização
automática.

## Comandos

```bash
uv run python scripts/publicar_backlog_demanda.py validar backlog.md
uv run python scripts/publicar_backlog_demanda.py planejar backlog.md --demanda 13959
uv run python scripts/publicar_backlog_demanda.py publicar backlog.md --demanda 13959 --simulacao
uv run python scripts/publicar_backlog_demanda.py publicar backlog.md --demanda 13959 --validar-apenas
uv run python scripts/publicar_backlog_demanda.py publicar backlog.md --demanda 13959
```

`--simulacao` lê a Demanda e produz o plano completo; não solicita autorização e não cria work item
algum. `--validar-apenas` verifica o destino e valida as operações remotamente com
`validateOnly=true`, incluindo a relação com a Demanda, sem POST persistente e sem criar work items.

Toda reconciliação de uma criação ambígua é manual: compare no Azure Boards o ID, a chave documental,
o título, o tipo e os caminhos com o marcador do manifesto. Só corrija o manifesto e retome após essa
conferência e uma nova confirmação vinculada ao hash e ao conjunto pendente.

## Configuração por execução

A precedência é linha de comando, arquivo TOML informado por `--config`, `.env` informado por
`--env-file` e perguntas interativas.

| Dado | Argumento | Variável de ambiente |
|---|---|---|
| Organização | `--organizacao` | `AZURE_DEVOPS_ORGANIZACAO` |
| Projeto | `--projeto` | `AZURE_DEVOPS_PROJETO` |
| Demanda de Negócio | `--demanda` | `AZURE_DEVOPS_DEMANDA` |
| Tipo da Demanda | `--tipo-demanda` | `AZURE_DEVOPS_TIPO_DEMANDA` |
| Tipos de item | `--tipo-epic`, `--tipo-feature`, `--tipo-user-story`, `--tipo-bug` | `AZURE_DEVOPS_TIPO_*` |
| Credencial | — (não existe argumento) | `AZURE_DEVOPS_TOKEN` |

**`Area Path` e `Iteration Path` não aparecem nesta tabela de propósito**: eles são herdados da
Demanda. Publicar sob uma Demanda significa publicar onde ela está.

Use o mapeamento de tipos quando o processo remoto expuser outros nomes, por exemplo
`AZURE_DEVOPS_TIPO_USER_STORY=Product Backlog Item` em processos Scrum. O nome remoto participa do
plano, do payload e do hash; não altera o rótulo documental `[User Story]`. O mesmo vale para
`AZURE_DEVOPS_TIPO_DEMANDA`, cujo padrão é `Demanda de Negócio`.

O token deve vir de variável de ambiente ou mecanismo seguro do sistema operacional. Nunca o
versione, não o coloque no backlog, no manifesto, no plano, em exemplos preenchidos ou em logs.

## Títulos

Os títulos publicados seguem a numeração hierárquica praticada no board, sem prefixo de data:

| Tipo | Chave documental | Título publicado |
|---|---|---|
| Epic | `1.0.0` | `01 Gestão do projeto` |
| Feature | `1.1.0` | `01.01 Gestão do projeto` |
| User Story / Bug | `1.1.1` | `01.01.01 Análise de padrões de stacks` |

A data de geração sai do título, mas continua sendo lida do Markdown, exibida no plano e incluída no
hash: é ela que distingue duas gerações do mesmo backlog.

## MCP

O MCP do Azure DevOps é **opcional** e pode apoiar inspeção interativa de tipos, campos e caminhos. A
publicação usa obrigatoriamente a REST API do pacote para manter ordem, hash, autorização por lote,
manifesto e tratamento determinístico de falhas.

## Limites

- **A Demanda de Negócio nunca é escrita.** O vínculo nasce do lado do Épico, via
  `System.LinkTypes.Hierarchy-Reverse`, no mesmo POST que cria o Épico. Nenhum `PATCH` toca o work
  item da área.
- `Area Path` e `Iteration Path` não são configuráveis: o destino é herdado da Demanda.
- `--simulacao` lê a Demanda e portanto exige token; só `validar` é totalmente offline.
- Não crie work items durante geração ou revisão do backlog.
- Não publique sem a frase exata de confirmação exibida para aquele plano e lote.
- Não transforme `Implementation Evidence` em conteúdo de work item.
- Não invente IDs, prioridades, responsáveis ou datas.
- Não use `bypassRules=true` e não publique work items reais durante testes padrão.
- Não repita POST após timeout, erro de rede ou resposta transitória sem idempotência.
- Não crie Task: a hierarquia publicada vai de Épico a História ou Bug.

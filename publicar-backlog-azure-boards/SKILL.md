---
name: publicar-backlog-azure-boards
description: Use quando um backlog Markdown já revisado precisa ser validado e, somente após autorização textual explícita, publicado no Azure Boards.
---

# Publicar backlog autorizado no Azure Boards

## Objetivo

Conduza a validação e a publicação de um backlog Markdown já revisado. Esta skill coordena a CLI e
os componentes do pacote; ela não inventa regras, campos ou caminhos que não estejam no backlog e
não afirma que a publicação acontece automaticamente.

## Fluxo obrigatório

1. Carregue o backlog e execute `validar`; a CLI usa sua própria cópia embarcada do contrato
   estrutural (módulo `contrato_backlog.py`) antes de interpretar ou planejar. Essa cópia não
   depende de `gerar-backlog-azure-boards` em tempo de execução e precisa ser ressincronizada
   manualmente se as regras da skill geradora
   (`gerar-backlog-azure-boards/scripts/validate_backlog.py`) mudarem.
2. Carregue a configuração, incluindo o `Iteration Path` escolhido para esta execução, e leia o
   manifesto existente.
3. Execute a verificação preliminar somente leitura: credencial, destino, tipos, campos, relação
   hierárquica, Area Path, Iteration Path e consistência do manifesto.
4. Apresente o plano com destino, mapeamento remoto de tipos, quantidades, ordem, relações,
   manifesto e hash. A autorização deve vincular o conteúdo executável completo, a quantidade e o
   conjunto pendente ou a faixa exata do lote; o executor repete essa validação antes da escrita.
5. Pergunte se a pessoa autoriza o backlog inteiro, por lotes ou o cancelamento. Em lotes, pergunte
   o tamanho e apresente cada lote novamente.
6. Mostre a frase completa e solicite que a pessoa a digite exatamente. A frase começa com
   `AUTORIZAR PUBLICAÇÃO` para o backlog inteiro ou `AUTORIZAR LOTE` para um lote.
7. Só depois da confirmação válida, chame a execução sequencial. O manifesto é atualizado após
   cada criação para permitir retomada com nova autorização.

Confirmação ausente, vaga, incorreta ou vinculada a outro hash resulta em **zero chamadas de criação**.
Após uma falha parcial, preserve o manifesto, corrija a causa e exija nova autorização para a
retomada. Timeout ou resposta ambígua de criação nunca autoriza repetir o POST: interrompa com o
manifesto bloqueado e exija reconciliação manual no Azure Boards antes de nova escrita. Não use
`--yes`, confirmação implícita, manifesto como autorização, exclusão, rollback ou atualização
automática.

## Comandos

```bash
uv run python scripts/publicar_backlog.py validar backlog.md
uv run python scripts/publicar_backlog.py planejar backlog.md --iteration-path 'Projeto\\Sprint 18'
uv run python scripts/publicar_backlog.py publicar backlog.md --simulacao
uv run python scripts/publicar_backlog.py publicar backlog.md --validar-apenas
uv run python scripts/publicar_backlog.py publicar backlog.md
```

`--simulacao` executa somente a preparação, a validação local e o planejamento; não solicita token,
não faz chamadas HTTP, não solicita autorização e não realiza chamadas de criação.
`--validar-apenas` também não
solicita autorização: ele verifica o destino e valida as operações remotamente com
`validateOnly=true`, sem POST persistente e sem criar work items.

Toda reconciliação de uma criação ambígua é manual: compare no Azure Boards o ID, a chave
documental, o título, o tipo e os caminhos com o marcador do manifesto. Só corrija o manifesto e
retome após essa conferência e uma nova confirmação vinculada ao hash e ao conjunto pendente.

## Campos de destino no work item

Dois campos não vão para onde o nome do item documental sugere, e a diferença já custou conteúdo em
publicação real:

| Conteúdo documental | Tipo remoto | Campo que recebe |
|---|---|---|
| `Description` | Epic, Feature, User Story | `System.Description` |
| `Description` | Bug | `Microsoft.VSTS.TCM.ReproSteps` |
| `Acceptance Criteria` | tipos que expõem o campo | `Microsoft.VSTS.Common.AcceptanceCriteria` |
| `Acceptance Criteria` | tipos que **não** expõem | nenhum — o conteúdo é descartado, com aviso |

No processo Agile, o formulário do Bug mostra Repro Steps e não Description: gravar a narrativa em
`System.Description` faz o conteúdo existir na API e ficar invisível no work item.

Quando um item tem critérios de aceitação e o tipo remoto não expõe o campo, a criação omite o campo
em vez de falhar. **A verificação preliminar avisa, nomeando os itens afetados, antes de pedir a
autorização** — sem isso, quem digita a frase acredita estar publicando conteúdo que nunca chega.

## Configuração por execução

A precedência é linha de comando, arquivo TOML informado por `--config`, `.env` informado por
`--env-file` e perguntas interativas. O `Iteration Path` muda a cada sprint e deve ser definido em
cada execução; ele não é parte do backlog Markdown.

Quando a configuração informar:

```dotenv
AZURE_DEVOPS_AREA_PATHS=Sustentacao,Projeto
```

e não houver `AZURE_DEVOPS_AREA_PATH` nem argumento `--area-path`, exija uma seleção explícita. Não
escolha silenciosamente entre `Sustentacao` e `Projeto`. Informe também, em cada execução, por
exemplo:

```dotenv
AZURE_DEVOPS_AREA_PATH=Projeto
AZURE_DEVOPS_ITERATION_PATH=Projeto\\Sprint 2026\\Sprint 18
AZURE_DEVOPS_TIPO_USER_STORY=Product Backlog Item
```

Use o mapeamento acima quando o processo remoto expuser `Product Backlog Item`. O nome remoto deve
participar do plano, do payload e do hash; não altere o rótulo documental `[User Story]`.

O token deve vir de variável de ambiente ou mecanismo seguro do sistema operacional. Nunca o
versione, não o coloque no backlog, no manifesto, no plano, em exemplos preenchidos ou em logs.

## MCP

O MCP do Azure DevOps é **opcional** e pode apoiar inspeção interativa de tipos, campos e caminhos.
A publicação usa obrigatoriamente a REST API do pacote para manter ordem, hash, autorização por
lote, manifesto e tratamento determinístico de falhas. A presença de MCP não é necessária para
executar a skill nem substitui a REST API.

## Limites

- Não crie work items durante geração ou revisão do backlog.
- Não publique sem a frase exata de confirmação exibida para aquele plano e lote.
- Não transforme `Implementation Evidence` em conteúdo de work item.
- Não invente Area Path, Iteration Path, IDs, prioridades, responsáveis ou datas.
- Não use `bypassRules=true` e não publique work items reais durante testes padrão.
- Não repita POST após timeout, erro de rede ou resposta transitória sem idempotência.

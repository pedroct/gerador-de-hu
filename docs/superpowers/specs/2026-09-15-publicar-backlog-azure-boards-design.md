# Especificação de design: publicar backlog no Azure Boards

## Contexto

O projeto `gerador-hu` produz um backlog Markdown revisável para Azure Boards por meio da skill
`gerar-backlog-azure-boards`. Atualmente, esse documento é uma saída de preparação: ele não cria nem
altera work items.

Esta especificação define uma nova skill, `publicar-backlog-azure-boards`, e um executor Python para
publicar um backlog aprovado no Azure DevOps Services usando a REST API. A publicação é uma operação
de escrita e nunca pode acontecer sem autorização explícita de quem está executando o fluxo.

## Objetivo

Permitir que um backlog Markdown válido seja convertido em work items do Azure Boards, preservando a
hierarquia documental e oferecendo publicação segura, rastreável, retomável e explicitamente
autorizada.

## Fora de escopo

- Interface web.
- Banco de dados compartilhado.
- Exclusão, destruição ou rollback automático de work items.
- Atualização automática de itens já publicados.
- Alteração automática de Area Paths, Iteration Paths ou processos do Azure DevOps.
- Uso obrigatório do Azure DevOps MCP Server.
- Criação de regras ou critérios que não estejam no backlog de origem.

## Decisões de arquitetura

### Skill e executor separados

A skill conduz o fluxo de entendimento e autorização. O executor Python realiza somente operações
determinísticas descritas pelo plano confirmado.

```text
publicar-backlog-azure-boards/SKILL.md
        |
        +-- valida o backlog
        +-- executa verificação preliminar somente leitura
        +-- apresenta o plano
        +-- coleta a modalidade de autorização
        +-- exige a frase de confirmação
        +-- chama o executor

executor Python
        |
        +-- interpreta o backlog validado
        +-- ordena a criação
        +-- chama a REST API
        +-- cria relações hierárquicas
        +-- atualiza o manifesto
```

A ausência de confirmação, uma confirmação incorreta ou um plano alterado resultam em zero chamadas
de criação.

### Forma inicial e stack

A primeira versão será uma CLI Python autocontida em repositório próprio, chamado
`publicar-backlog-azure-boards`. Este repositório atual continuará produzindo e validando o backlog.

Stack definida conforme `docs/padroes_de_stack.md`:

- Python 3.12 ou superior;
- `uv` para dependências e ambiente;
- `httpx` para a REST API;
- `markdown-it-py` para conversão controlada de Markdown;
- Pydantic e `pydantic-settings` para modelo e configuração;
- `pytest` para testes;
- Ruff e mypy em modo estrito;
- Bandit, pip-audit e Semgrep para segurança e dependências;
- pre-commit para verificações locais;
- python-semantic-release para versão e changelog;
- Docker opcional para execução padronizada.

Não haverá FastAPI, Next.js ou PostgreSQL na primeira versão. Esses componentes ficam reservados
para uma futura aplicação multiusuário que necessite de interface, persistência centralizada,
aprovações remotas ou auditoria compartilhada.

## Modelo do backlog de entrada

O consumidor deve aceitar o contrato produzido por `gerar-backlog-azure-boards`:

- Epic em chave `E.0.0`;
- Feature em chave `E.F.0`;
- User Story ou Bug em chave `E.F.S`;
- `Parent` explícito;
- `Description` com Card e Conversation;
- `Acceptance Criteria` somente com Gherkin confirmado;
- `Implementation Evidence` excluído dos campos enviados ao Azure Boards;
- chave documental tratada como correlação local, nunca como ID Azure.

O executor deve chamar o validador existente antes de planejar a publicação. Um backlog inválido
nunca pode alcançar a fase de autorização.

## Componentes

Os nomes dos componentes criados para o projeto devem permanecer em português brasileiro. Os nomes
oficiais de campos, parâmetros e relações da API permanecem inalterados.

- `SKILL.md`: conduz o fluxo e aplica as regras de autorização.
- `interpretar_markdown.py`: converte o documento em modelo interno.
- `planejar_publicacao.py`: ordena os itens e monta operações sem executar escrita.
- `cliente_azure_devops.py`: encapsula as chamadas REST.
- `manifesto.py`: lê e grava a associação entre chave documental e work item.
- `executar_publicacao.py`: executa apenas um plano previamente autorizado.
- `converter_para_html.py`: converte campos Markdown para HTML.

Cada componente deve ter uma responsabilidade única e interfaces testáveis independentemente.

## Mapeamento para Azure Boards

| Backlog Markdown | Azure Boards |
|---|---|
| `[Epic]` | Tipo de work item configurado para Epic |
| `[Feature]` | Tipo de work item configurado para Feature |
| `[User Story]` | Tipo de requisito configurado no projeto |
| `[Bug]` | Tipo de work item configurado para Bug |
| Título | `System.Title` |
| `Description` copiável | `System.Description` |
| `Acceptance Criteria` | `Microsoft.VSTS.Common.AcceptanceCriteria` |
| `Parent` | Relação hierárquica real |
| `Implementation Evidence` | Não enviado |
| Chave documental | Manifesto de publicação |

Os tipos de work item não devem ser presumidos apenas pelo idioma ou pelo processo padrão. A
verificação preliminar deve consultar os tipos disponíveis no projeto e permitir uma configuração
explícita quando o projeto usar nomes diferentes, como `Product Backlog Item`.

## Fluxo de publicação

### 1. Preparação

1. Receber o caminho do backlog.
2. Validar sua estrutura e semântica mínima.
3. Ler configuração da linha de comando, arquivo de configuração e `.env`.
4. Interpretar os itens e seus pais.
5. Ler o manifesto existente, se houver.

### 2. Verificação preliminar

Executar somente leituras para verificar:

- credencial disponível;
- organização e projeto acessíveis;
- tipos de work item existentes;
- campos necessários disponíveis para cada tipo;
- relações hierárquicas disponíveis;
- Area Path escolhido existente;
- Iteration Path escolhida existente;
- consistência do manifesto;
- itens já publicados e itens pendentes.

Nenhuma chamada de criação, atualização ou exclusão ocorre nesta fase.

### 3. Plano

Apresentar um resumo que inclua:

- organização;
- projeto;
- Area Path;
- Iteration Path;
- quantidade total de itens;
- quantidade de itens novos;
- quantidade já registrada no manifesto;
- quantidade por tipo;
- ordem de criação;
- relações pai-filho;
- arquivo de manifesto;
- identificação do plano.

O plano deve possuir um hash calculado a partir do conteúdo relevante do backlog e da configuração
de destino. Alterar o backlog, o Area Path, a Iteration Path ou o projeto invalida a confirmação
anterior.

### 4. Escolha da modalidade de autorização

A skill deve permitir que a pessoa escolha a modalidade conforme o tamanho do backlog:

```text
Como deseja autorizar a publicação?

[1] Backlog inteiro
[2] Por lotes
[C] Cancelar
```

Na modalidade de backlog inteiro, uma única confirmação autoriza somente os itens novos daquele
plano.

Na modalidade por lotes, a pessoa informa o tamanho do lote. Cada lote é apresentado novamente e
exige sua própria confirmação antes das chamadas de criação daquele lote.

Não haverá opção `--yes`, confirmação implícita por variável de ambiente ou publicação automática
por existência de manifesto.

### 5. Confirmação

A skill deve gerar uma frase específica contendo modalidade, quantidade, destino e código derivado
do plano. Exemplo:

```text
AUTORIZAR PUBLICAÇÃO 12 ITENS PROJETO AREA-PROJETO SPRINT-18 7F3A
```

Na modalidade por lotes, a frase deve identificar também o lote:

```text
AUTORIZAR LOTE 2 4 ITENS PROJETO AREA-PROJETO SPRINT-18 B91C
```

A comparação deve ser exata, sem aceitar prefixos ou respostas vagas. `CANCELAR` encerra o fluxo.

A confirmação é o consentimento operacional de quem executa. A identidade e as permissões efetivas
continuam sendo determinadas pela credencial usada na REST API.

### 6. Criação

Criar sempre na ordem:

```text
Epics → Features → User Stories/Bugs
```

Para cada item:

1. confirmar que ele pertence ao plano cujo hash foi autorizado;
2. ignorar somente itens já registrados e validados no manifesto;
3. criar o work item por JSON Patch;
4. adicionar a relação hierárquica quando o pai já tiver ID;
5. registrar ID, tipo, URL e chave documental no manifesto;
6. seguir para o próximo item.

O cliente deve usar `application/json-patch+json` e preservar as versões da API por operação. A
criação deve usar `validateOnly` durante a fase de validação remota, nunca `bypassRules=true` por
padrão.

## Area Path e Iteration Path

O projeto possui dois Area Paths disponíveis:

```dotenv
AZURE_DEVOPS_AREA_PATHS=Sustentacao,Projeto
```

O caminho usado numa execução deve ser explícito:

```dotenv
AZURE_DEVOPS_AREA_PATH=Projeto
```

Quando houver mais de uma opção, a skill deve solicitar a escolha se ela não tiver sido fornecida
por argumento. Não deve escolher silenciosamente entre `Sustentacao` e `Projeto`.

A primeira versão usará um único Area Path por execução. A distribuição de itens por chave
documental poderá ser adicionada depois por arquivo de configuração, sem alterar o contrato do
backlog.

A Iteration Path muda a cada sprint e não pertence ao backlog Markdown. Deve ser fornecida em cada
execução, por argumento ou pelo `.env` atualizado:

```dotenv
AZURE_DEVOPS_ITERATION_PATH=Projeto\\Sprint 2026\\Sprint 18
```

Antes da autorização, a skill deve mostrar os dois caminhos e incluí-los na frase de confirmação.
Ambos devem ser validados no Azure DevOps antes da publicação.

Precedência da configuração:

```text
linha de comando → arquivo de configuração → .env → pergunta interativa
```

## Manifesto e retomada

O manifesto não concede autorização. Ele apenas permite correlação, prevenção de duplicidade e
retomada:

```json
{
  "versao": 1,
  "origem": "backlog.md",
  "hash_plano": "7f3a...",
  "itens": {
    "1.0.0": {
      "id": 123,
      "tipo": "Epic",
      "url": "https://dev.azure.com/..."
    }
  }
}
```

O manifesto deve ser gravado de forma segura após cada criação bem-sucedida. Uma nova execução
deve exigir nova autorização, mesmo quando continuar um plano parcialmente publicado.

Se um item existir no manifesto, mas divergir em tipo, projeto, título ou hash compatível, a skill
deve interromper e pedir revisão manual.

## Falhas e segurança

- Backlog inválido: encerrar antes de qualquer escrita.
- Credencial inválida: encerrar antes da autorização de publicação.
- Tipo, campo ou caminho inexistente: encerrar na verificação preliminar.
- Erro transitório: realizar poucas novas tentativas com espera progressiva.
- Erro permanente: interromper e informar o item afetado.
- Falha parcial: preservar itens criados, atualizar manifesto e permitir retomada autorizada.
- Plano alterado: invalidar autorização e exigir novo resumo.
- Cancelamento: não realizar novas chamadas de escrita.

Não haverá exclusão, destruição, rollback automático ou `bypassRules=true` na primeira versão.

O token será lido de variável de ambiente ou mecanismo seguro do sistema operacional. Nunca será
exibido em logs, mensagens de erro, plano, backlog ou manifesto. PAT é aceitável para uso local,
mas a camada de autenticação deve permitir futura migração para Microsoft Entra ID.

## Azure DevOps MCP Server

O MCP será opcional e não fará parte do caminho obrigatório de publicação.

Ele pode apoiar uma fase interativa de inspeção, por exemplo para descobrir tipos, campos, Area
Paths, Iteration Paths e exemplos de work items. Porém, a publicação principal continuará usando a
REST API, pois precisa de ordem determinística, hash do plano, confirmação por lote, manifesto,
novas tentativas e tratamento previsível de falhas.

Para Codex e outros clientes não Microsoft, a documentação do Azure DevOps indica limitações de
autenticação no servidor remoto; nesses casos, o servidor local pode ser usado com PAT ou Azure CLI.
Essa integração deve permanecer opcional e não deve impedir a execução da CLI sem MCP.

## Testes e critérios de aceitação

### Testes unitários

- interpretar o contrato Markdown;
- preservar chaves, tipos e relações pai-filho;
- excluir `Implementation Evidence` dos campos enviados;
- converter Description e Acceptance Criteria para HTML;
- gerar payloads JSON Patch;
- calcular e comparar hash do plano;
- aceitar e rejeitar frases de confirmação;
- selecionar backlog inteiro ou lotes;
- impedir escrita sem confirmação;
- impedir escrita quando o plano mudar;
- ler e atualizar o manifesto;
- retomar após falha parcial;
- tratar respostas HTTP de erro.

### Testes de integração

Um teste contra Azure DevOps real será opcional, explícito e direcionado a um projeto de teste. Os
testes padrão usarão respostas simuladas e nunca criarão work items por acidente.

### Critérios de aceitação

1. Um backlog inválido não gera chamadas de escrita.
2. Uma confirmação ausente, vaga ou incorreta não gera chamadas de escrita.
3. A confirmação vale somente para o hash, projeto, Area Path, Iteration Path e quantidade exibidos.
4. A modalidade inteira cria somente itens novos daquele plano.
5. A modalidade por lotes exige confirmação antes de cada lote.
6. Epics, Features e itens de folha são criados na ordem correta.
7. Cada item criado é registrado no manifesto antes do próximo item.
8. Uma falha parcial pode ser retomada sem duplicar itens já registrados.
9. `Implementation Evidence` nunca é enviado como campo do Azure Boards.
10. Nenhum segredo aparece em saída, arquivos de controle ou exceções.

## Evolução futura

Se houver necessidade de uso multiusuário, aprovação remota, auditoria centralizada ou publicação
por navegador, a CLI poderá ser encapsulada por uma aplicação FastAPI com PostgreSQL. Uma interface
Next.js poderá consumir o contrato OpenAPI por tipos TypeScript gerados. Essa evolução deverá ser
tratada como novo subsistema, sem enfraquecer a confirmação explícita exigida nesta especificação.

## Referências

- `docs/padroes_de_stack.md`
- `gerar-backlog-azure-boards/SKILL.md`
- `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`
- [Azure DevOps Work Items - Create](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/create?view=azure-devops-rest-7.2)
- [Azure DevOps Work Items - Update](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/update?view=azure-devops-rest-7.1)
- [Azure DevOps WIQL](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/wiql/query-by-wiql?view=azure-devops-rest-7.2)
- [Azure DevOps MCP Server](https://learn.microsoft.com/en-us/azure/devops/mcp-server/mcp-server-overview?view=azure-devops)

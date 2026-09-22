# Relatório da Task 3 — quarta skill e contrato Markdown

## Status

Concluída. A skill `generating-azure-boards-backlog-from-spec` foi preenchida, o contrato Markdown foi criado e os metadados da interface foram conferidos. Nenhum script, teste ou fixture foi modificado.

## Arquivos

- Modificado: `/Users/pedroct/skills/generating-azure-boards-backlog-from-spec/SKILL.md`
- Conferido e mantido, pois já correspondia exatamente ao brief: `/Users/pedroct/skills/generating-azure-boards-backlog-from-spec/agents/openai.yaml`
- Criado: `/Users/pedroct/skills/generating-azure-boards-backlog-from-spec/references/backlog-markdown-contract.md`
- Criado: `/Users/pedroct/skills/.superpowers/sdd/2026-09-10-azure-boards-backlog-skill/task-3-report.md`

Commits: nenhum. O workspace não é Git e não foi inicializado.

## Conteúdo implementado

### Entrypoint da skill

O `SKILL.md` agora contém:

- frontmatter final com nome e descrição discriminante iniciada por `Use when`;
- outcome limitado a requisitos rastreáveis e distinção entre chave documental e ID do Azure Boards;
- inventário da spec com origem para objetivos, atores, capacidades, regras, restrições, exemplos, conflitos e lacunas;
- decomposição em Epic, Feature e User Story sem criar itens para preencher níveis;
- chamada obrigatória a `refining-user-stories-with-3c` para cada história e consumo do resultado sem recalcular 3W, Conversation, Confirmation ou prontidão;
- numeração `E.0.0`, `E.F.0`, `E.F.S`, preservação de chaves em atualizações e exigência de `Parent` explícito;
- renderização pelo contrato e validação estrutural com `scripts/validate_backlog.py`, incluindo `--update` para backlogs existentes;
- limites de geração somente em Markdown, sem mutação no Azure Boards nem invenção de metadados de planejamento;
- história rastreável porém incompleta como `Não pronta`, com `Acceptance Criteria` vazio;
- requisito sem pai justificável em `Itens não cobertos`.

### Contrato Markdown

O novo `references/backlog-markdown-contract.md` registra:

- definições de Epic, Feature e User Story;
- tabela dos formatos de chave, relação pai-filho e regras para documentos novos e atualizações;
- template completo com cabeçalhos nos níveis esperados e blocos `Parent` explícitos para Feature e User Story;
- conteúdo permitido em `Description` e `Acceptance Criteria`;
- regra de deixar `Acceptance Criteria` sem conteúdo para história incompleta ou sem Confirmation;
- `Refinement Status` como metadado de preparação, fora dos campos Azure, com prontidão exclusivamente recebida da 3C;
- rastreabilidade obrigatória, tratamento de conflitos e composição de `Itens não cobertos`;
- distinção entre Markdown de revisão e os campos HTML `System.Description` e `Microsoft.VSTS.Common.AcceptanceCriteria`;
- os três links oficiais exigidos pelo brief.

### Interface

`agents/openai.yaml` já continha, e continua contendo, exatamente:

```yaml
interface:
  display_name: "Gerar backlog para Azure Boards"
  short_description: "Converte specs em backlog hierárquico revisável"
  default_prompt: "Use $generating-azure-boards-backlog-from-spec para analisar esta spec e gerar um backlog Markdown para Azure Boards."
```

## Influência das falhas RED

As duas falhas reais registradas na Task 1 determinaram correções mínimas e explícitas:

1. **Pai implícito:** o workflow exige que toda relação seja materializada em `Parent`, e o contrato declara que aninhamento visual ou numeração compatível não substituem o pai explícito. O template possui `Parent` tanto para Feature quanto para User Story.
2. **Auditoria apenas proposta promovida a requisito:** uma sugestão ou proposta não confirmada sem evidência suficiente de demanda não pode gerar Epic, Feature ou User Story, nem ser legitimada como história `Não pronta`. Ela permanece em `Itens não cobertos` ou, quando pertinente, na Conversation de uma história sustentada por demanda rastreável, sempre com origem e estado preservados.

Essa segunda regra distingue proposta sem demanda suficiente de demanda rastreável porém incompleta: somente a segunda pode permanecer na hierarquia como `Não pronta`.

## Validação

Comando final executado após todas as alterações:

```bash
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
```

Saída:

```text
Skill is valid!
```

Também foi feita uma verificação textual sem mutação para confirmar ausência de placeholders `TODO`, presença dos dois cabeçalhos `Parent`, das regras para propostas não confirmadas, dos nomes dos campos Azure e dos três links oficiais. Todos foram encontrados e nenhum `TODO` permaneceu.

## Auto-revisão

- Escopo respeitado: somente `SKILL.md`, o novo contrato e este relatório foram alterados; `openai.yaml` foi conferido e não precisava de mudança.
- O corpo mínimo prescrito pelo brief foi preservado; as únicas extensões de decisão fecham diretamente as duas brechas RED.
- A referência concentra o detalhe pesado e é ligada pelo workflow, mantendo o entrypoint curto (267 palavras, abaixo do alvo de 500 palavras do guia `writing-skills`).
- A descrição cobre o gatilho de descoberta sem substituir o workflow.
- Não há dependência circular: esta skill chama apenas a 3C e não chama diretamente 3W ou Gherkin.
- Não há autorização de mutação externa nem campos de planejamento inventados.
- A auto-revisão removeu uma formulação que permitiria critérios em história incompleta, alinhando o contrato à fronteira literal do brief.
- Os testes comportamentais completos não foram executados nesta task, conforme a instrução de que ocorrerão depois; o RED anterior da Task 1 foi usado como evidência de teste antes da escrita.

## Preocupações remanescentes

Nenhuma para o escopo da Task 3. A validação comportamental GREEN/REFACTOR permanece deliberadamente para as tasks posteriores previstas no plano.

## Fix round 1

Esta seção registra e substitui as formulações afetadas pelos findings da primeira revisão.

### Mudanças

1. Em `SKILL.md`, a condição “sem evidência suficiente de demanda” foi removida. Sugestões, propostas ou hipóteses não confirmadas agora nunca podem originar Epic, Feature, User Story ou regra; só podem ser registradas em `Itens não cobertos` ou na Conversation de uma demanda confirmada, com origem e estado.
2. No contrato, `Acceptance Criteria` passou a aceitar exclusivamente zero ou mais blocos cercados `gherkin` retornados pela Confirmation da 3C. Regras narrativas, títulos, listas, comentários, placeholders e texto externo aos blocos são proibidos. Com Confirmation `Ausente` ou `Parcial`, o trecho entre `##### Acceptance Criteria` e `##### Refinement Status` contém apenas espaço em branco; o placeholder do template foi removido.
3. O contrato de `Parent` agora exige que a chave referenciada exista no mesmo documento, tenha o tipo pai correto e prefixo compatível: Feature `E.F.0` → Epic `E.0.0`; User Story `E.F.S` → Feature `E.F.0`.
4. A serialização da história foi tornada determinística. `Description` contém, nesta ordem e exatamente uma vez, `### Card` e `### Conversation`, cada qual com o conteúdo correspondente retornado pela 3C. `Refinement Status` contém uma linha e um único valor recebido da 3C para Card, Conversation, Confirmation e Prontidão; não lista alternativas com barras e não recalcula estados ou gates.
5. `Itens não cobertos` agora usa exatamente `- Itens não cobertos: Nenhum` quando vazio. Quando não vazio, cada entrada possui `Conteúdo`, `Origem`, `Estado` e `Justificativa`.

Nenhum script, teste, fixture ou metadado de interface foi alterado. Git não foi inicializado e nenhum commit foi criado.

### Validação

Comando executado após as correções:

```bash
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
```

Saída:

```text
Skill is valid!
```

A seção vazia do template também foi inspecionada diretamente. O trecho resultante é:

```markdown
##### Acceptance Criteria

##### Refinement Status
```

A busca pela formulação removida, `sem evidência suficiente de demanda`, não encontrou ocorrências em `SKILL.md` nem no contrato. O entrypoint permanece conciso, com 260 palavras.

### Auto-revisão

- Critical 1: regra absoluta presente no entrypoint e no contrato; nenhuma condição residual limita a proibição.
- Critical 2: template sem conteúdo em Acceptance Criteria; contrato limita conteúdo a blocos Gherkin devolvidos pela 3C e esvazia Ausente/Parcial.
- Important 3: existência no mesmo documento, tipo e prefixo do pai estão declarados de forma verificável.
- Important 4: headings e ordem da Description estão explícitos; cada estado tem uma única linha/valor e permanece propriedade da 3C.
- Minor 5: os casos vazio e não vazio de `Itens não cobertos` têm serialização definida e os quatro campos obrigatórios estão presentes.
- Escopo: somente `SKILL.md`, `references/backlog-markdown-contract.md` e este relatório foram modificados nesta rodada; scripts e testes permaneceram intactos.

### Preocupações

Nenhuma para esta rodada. A validação comportamental continua reservada para as tasks posteriores, conforme o plano.

## Fix round 2

### Mudança

O finding NB-1 foi corrigido somente em `references/backlog-markdown-contract.md`:

- no template da User Story, `### Card` passou a `###### Card`;
- no template da User Story, `### Conversation` passou a `###### Conversation`;
- a regra textual da seção `Description` agora exige exatamente os headings `###### Card` e `###### Conversation`.

Assim, Card e Conversation permanecem subordinados a `##### Description` e não ocupam mais o nível `###` reservado às Features. Todo o restante do fix round 1 foi preservado. Nenhum script ou teste foi alterado; Git não foi inicializado e nenhum commit foi criado.

### Validação

Comando executado:

```bash
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
```

Saída:

```text
Skill is valid!
```

A inspeção textual confirmou as três ocorrências esperadas em `######` e nenhuma ocorrência residual dos headings ou da regra em `###`.

### Auto-revisão

- Alteração limitada aos dois headings do template e à regra textual correspondente.
- Hierarquia final: Feature `###` → User Story `####` → Description `#####` → Card/Conversation `######`.
- `Acceptance Criteria`, `Refinement Status`, regras de propostas, `Parent` e `Itens não cobertos` permaneceram inalterados.

### Preocupações

Nenhuma para esta rodada.

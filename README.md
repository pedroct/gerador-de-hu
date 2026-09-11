# Gerador de Histórias de Usuário

Skills para transformar especificações em histórias de usuário refinadas e em um backlog Markdown pronto para revisão e posterior cadastro no Azure Boards.

## O que o projeto faz

O fluxo combina três técnicas complementares:

```text
Spec
 └─ generating-azure-boards-backlog-from-spec
     └─ refining-user-stories-with-3c
         ├─ refining-user-stories-with-3w
         └─ refining-user-stories-with-gherkin
```

- **3W — Who, What, Why:** identifica ator, capacidade/resultado e valor, separando fatos de lacunas.
- **3C — Card, Conversation, Confirmation:** organiza o cartão, registra decisões e coordena a confirmação. É a única skill que define a prontidão geral.
- **Gherkin:** converte apenas regras confirmadas em exemplos verificáveis e classifica a Confirmation como `Ausente`, `Parcial` ou `Completa`.
- **Backlog a partir de spec:** agrupa requisitos rastreáveis em Épicos, Features e Histórias, preserva lacunas e gera o documento final.

As dependências são acíclicas: 3W e Gherkin são folhas; a skill de backlog chama somente 3C.

## Início rápido

1. Forneça uma spec à skill `generating-azure-boards-backlog-from-spec`.
2. Peça um backlog Markdown para Azure Boards.
3. Revise o arquivo gerado e valide sua estrutura:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python scripts/validate_backlog.py caminho/para/backlog.md
```

O validador retorna `Backlog structure is valid` quando a hierarquia, as chaves, os pais e os campos obrigatórios estão corretos.

## Skills disponíveis

| Skill | Use quando | Saída principal |
|---|---|---|
| [`refining-user-stories-with-3w`](refining-user-stories-with-3w/SKILL.md) | Ator, objetivo ou benefício estão vagos | Mapa 3W, história/rascunho, perguntas e estado 3W |
| [`refining-user-stories-with-3c`](refining-user-stories-with-3c/SKILL.md) | A história precisa de conversa e confirmação | Card, Conversation, Confirmation e prontidão 3C |
| [`refining-user-stories-with-gherkin`](refining-user-stories-with-gherkin/SKILL.md) | Regras confirmadas precisam de exemplos BDD | Regras, Gherkin e estado local da Confirmation |
| [`generating-azure-boards-backlog-from-spec`](generating-azure-boards-backlog-from-spec/SKILL.md) | Uma spec precisa virar backlog hierárquico | Documento Markdown de backlog e itens não cobertos |

## Formato do backlog

As chaves são localizadores documentais, não IDs do Azure Boards:

```text
1.0.0 Épico
1.1.0 Feature
1.1.1 História de Usuário
```

Cada Feature declara `Parent` apontando para um Épico existente; cada História declara `Parent` apontando para uma Feature existente. Em atualizações, chaves publicadas são preservadas e lacunas removidas não são reutilizadas.

### Mapeamento para Azure Boards

| Documento Markdown | Campo Azure Boards | Conteúdo |
|---|---|---|
| `Description` da História | `System.Description` | Card 3W e síntese da Conversation, incluindo decisões, propostas não confirmadas e lacunas |
| `Acceptance Criteria` | `Microsoft.VSTS.Common.AcceptanceCriteria` | Somente blocos Gherkin da Confirmation quando o estado for `Completa` |
| `Refinement Status` | Metadado de revisão | Estado de Card, Conversation, Confirmation, prontidão e origem na spec; não é copiado automaticamente |

Com Confirmation `Ausente` ou `Parcial`, `Acceptance Criteria` permanece efetivamente vazio. Regras pendentes, hipóteses e justificativas continuam em `Description`/Conversation. A geração não cria nem altera work items.

## Exemplo mínimo

````markdown
## 1.0.0 [Epic] Reabrir diligências

### Description
Origem na spec: seção 2.

### 1.1.0 [Feature] Reabertura dentro do prazo
#### Parent
`1.0.0`

#### 1.1.1 [User Story] Reabrir uma diligência
##### Parent
`1.1.0`
##### Description
###### Card
Como analista, quero reabrir uma diligência em até 24 horas, para corrigir informações.
###### Conversation
A regra de prazo e o retorno para Em análise foram confirmados.
##### Acceptance Criteria
```gherkin
# language: pt
Funcionalidade: Reabrir diligência
Cenário: Reabertura dentro do prazo
  Dado que a diligência foi concluída há menos de 24 horas
  Quando o analista informa uma justificativa e solicita a reabertura
  Então o status da diligência passa para Em análise
```
````

## Validação e desenvolvimento

Execute a suíte completa da quarta skill:

```bash
uv run python -m unittest discover -s generating-azure-boards-backlog-from-spec/tests -v
```

Valide os quatro pacotes com o utilitário oficial:

```bash
for skill_dir in \
  generating-azure-boards-backlog-from-spec \
  refining-user-stories-with-3c \
  refining-user-stories-with-3w \
  refining-user-stories-with-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```

Ao criar ou alterar uma skill, mantenha o `SKILL.md`, `agents/openai.yaml`, referências e testes correspondentes. Não adicione credenciais, IDs de work items ou metadados Azure sem fonte explícita.

## Referências

- [Processo Agile e hierarquia de Epics, Features e User Stories](https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/define-features-epics)
- [Descrição e Acceptance Criteria no Azure Boards](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow)
- [IDs, títulos e descrições dos campos](https://learn.microsoft.com/en-us/azure/devops/boards/queries/titles-ids-descriptions)
- [Referência oficial do Gherkin](https://cucumber.io/docs/gherkin/reference)
- [Card, Conversation, Confirmation](https://ronjeffries.com/xprog/articles/expcardconversationconfirmation/)

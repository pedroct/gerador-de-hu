# Gerador de Histórias de Usuário

Skills para transformar especificações em histórias de usuário refinadas e em um backlog Markdown pronto para revisão e posterior cadastro no Azure Boards, tanto sem implementação existente quanto comparando a spec com um projeto já implementado.

## O que o projeto faz

O fluxo combina seis capacidades complementares:

```text
Spec
 └─ generating-azure-boards-backlog-from-spec
     └─ refining-user-stories-with-3c
         ├─ refining-user-stories-with-3w
         └─ refining-user-stories-with-gherkin
```

Quando não existe spec escrita — só um pedido informal de negócio, como um e-mail ou ticket — a skill
`drafting-a-spec-from-business-request` investiga o código-fonte já disponível onde está instalada e
produz essa spec como um passo manual anterior:

```text
Pedido informal (e-mail, ticket) + código-fonte
 └─ drafting-a-spec-from-business-request
     └─ Spec (com lacunas documentadas)
```

Se a spec resultante ainda tiver itens em `## Lacunas e perguntas abertas`, a skill
`interviewing-request-gaps` — quando instalada — fecha o máximo possível deles por entrevista em
rodadas, antes de a spec seguir manualmente para o backlog:

```text
Spec (com lacunas)
 └─ interviewing-request-gaps (opcional, se instalada)
     └─ Spec (lacunas fechadas ou adiadas por decisão explícita)
```

Depois da geração, Histórias que ficaram `Não pronta` não bloqueiam a entrega do backlog, mas a skill
sugere a mesma entrevista de lacunas — agora sobre as pendências de Card, Conversation e Confirmation
dessas Histórias — como próximo passo manual, repetido a cada rodada até todas ficarem `Prontas` ou até
o usuário adiar explicitamente uma lacuna:

```text
Backlog (com Histórias "Não pronta")
 └─ sugestão: registrar as lacunas em "## Lacunas e perguntas abertas" da spec
     └─ interviewing-request-gaps (opcional, se instalada)
         └─ Spec atualizada
             └─ generating-azure-boards-backlog-from-spec (nova rodada)
```

- **Drafting a partir de pedido de negócio:** investiga o código-fonte a partir de um pedido informal (e-mail, ticket) e produz a spec inicial, separando o que foi afirmado, evidenciado e lacunas.
- **Entrevista de lacunas:** fecha, por entrevista em rodadas, a seção de lacunas de uma spec já escrita, sem investigar código nem desenhar plano algum; referenciada condicionalmente por Drafting e, após a geração do backlog, como sugestão para fechar Histórias `Não pronta` — nunca obrigatória.
- **3W — Who, What, Why:** identifica ator, capacidade/resultado e valor, separando fatos de lacunas.
- **3C — Card, Conversation, Confirmation:** organiza o cartão, registra decisões e coordena a confirmação. É a única skill que define a prontidão geral.
- **Gherkin:** converte apenas regras confirmadas em exemplos verificáveis e classifica a Confirmation como `Ausente`, `Parcial` ou `Completa`.
- **Backlog a partir de spec:** agrupa requisitos rastreáveis em Épicos, Features e Histórias e sempre gera o documento Markdown revisável, marcando lacunas e Histórias incompletas como `Não pronta` em vez de bloquear a geração ou inventar fechamento só para completar o documento; para essas Histórias, sugere a entrevista de lacunas como próxima rodada.

As dependências são acíclicas: 3W e Gherkin são folhas; a skill de backlog chama somente 3C; `drafting-a-spec-from-business-request` é uma predecessora isolada, que nunca chama nem é chamada pelas outras quatro skills. `interviewing-request-gaps` também é folha e nunca é chamada incondicionalmente nem invocada diretamente por outra skill — é só referenciada, de forma condicional, pelo fluxo de `drafting-a-spec-from-business-request` e, após a geração do backlog, pela sugestão de fechar Histórias `Não pronta` em `generating-azure-boards-backlog-from-spec`; em ambos os casos, quem decide rodá-la é o usuário.

## Instalação

As skills seguem o formato aberto (`SKILL.md` por pasta) suportado pelo [`npx skills`](https://skills.sh), que instala diretamente a partir deste repositório do GitHub — não é necessário publicar em nenhum registro. Funciona tanto para uso com Claude (Claude Code) quanto com agentes da OpenAI (Codex):

```bash
# listar as skills disponíveis no repositório
npx skills add pedroct/gerador-de-hu --list

# instalar todas, no projeto atual, para Claude Code
npx skills add pedroct/gerador-de-hu --all -a claude-code

# instalar todas, no projeto atual, para Codex (OpenAI)
npx skills add pedroct/gerador-de-hu --all -a codex

# instalar só uma skill específica
npx skills add pedroct/gerador-de-hu --skill drafting-a-spec-from-business-request -a claude-code
```

A instalação pode ser por projeto (padrão) ou global:

| Escopo | Flag | Onde fica |
|---|---|---|
| Projeto | *(nenhuma)* | `./<agente>/skills/` — versionado com o projeto, compartilhado com o time |
| Global | `-g` | `~/<agente>/skills/` — disponível em qualquer projeto da máquina |

```bash
# instalar globalmente, disponível em todos os projetos
npx skills add pedroct/gerador-de-hu --all -a claude-code -g
```

Cada skill inclui `agents/openai.yaml` (metadado de exibição específico para agentes OpenAI); o `SKILL.md` é o formato portátil que tanto Claude quanto agentes OpenAI leem diretamente, sem exigir esse arquivo extra.

### Como usar depois de instalado

Abra o agente (Claude Code, Codex etc.) a partir do diretório onde a skill foi instalada — se o projeto tiver múltiplos repositórios irmãos (como api, front e mobile de uma mesma aplicação), abra a partir da raiz que os agrupa, não de dentro de um deles, para que `drafting-a-spec-from-business-request` consiga descobrir os repositórios relevantes.

A partir daí, duas formas funcionam:

1. **Chamando a skill explicitamente**, seguida do texto do pedido:

   ```
   /drafting-a-spec-from-business-request

   <cole aqui o texto do pedido enviado pela área de negócios>
   ```

2. **Deixando a detecção automática funcionar**: basta colar o texto do pedido numa conversa nova, sem digitar comando algum — a `description` do `SKILL.md` já orienta o agente a reconhecer um pedido informal sem spec escrita e acionar a skill sozinho.

## Início rápido

### Fluxo Greenfield

1. Forneça uma spec à skill `generating-azure-boards-backlog-from-spec`.
2. Quando não houver código-fonte relevante disponível, a skill registra `Modo: Greenfield` e decompõe somente os requisitos rastreáveis da spec. Nenhuma inspeção de implementação é exigida.
3. Peça um backlog Markdown para Azure Boards e revise lacunas de 3W, Conversation e Confirmation.

### Fluxo Brownfield

1. Forneça a spec e a raiz do projeto existente. Se a presença de código relevante for ambígua, o fluxo assume Brownfield e registra essa incerteza.
2. A skill inspeciona código, testes e configuração em modo somente leitura antes do refinamento. Ela não executa scripts, testes, builds, servidores, migrações nem a aplicação sem autorização explícita.
3. Cada requisito da spec recebe evidência `caminho:linha`, status, impacto e confiança. O backlog cria trabalho para lacunas, divergências e mudanças; requisitos implementados permanecem na cobertura sem gerar duplicatas por padrão.

Nos dois fluxos, valide a estrutura do arquivo gerado:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python scripts/validate_backlog.py caminho/para/backlog.md
```

O validador retorna `Backlog structure is valid` quando a hierarquia, as chaves, os pais e os campos obrigatórios estão corretos.

### Exemplos de classificação Brownfield

Os status comparam apenas o projeto com um requisito rastreável da spec. Código não cria requisito nem confirma valor ou decisão de negócio.

| Situação observada | Status |
|---|---|
| Serviço e validação aplicam toda a regra de reabertura em até 24 horas | `Implementado` |
| Reabertura existe, mas a janela de 24 horas não é validada | `Parcialmente implementado` |
| Serviço permite reabrir depois de 24 horas, contrariando a spec | `Divergente` |
| Busca concluída no escopo relevante sem encontrar a capacidade | `Não encontrado` |
| Projeto ou arquivos necessários não estão acessíveis, ou o escopo segue ambíguo | `Impossível validar` |

## Skills disponíveis

| Skill | Use quando | Saída principal |
|---|---|---|
| [`drafting-a-spec-from-business-request`](drafting-a-spec-from-business-request/SKILL.md) | Só há um pedido informal de negócio (e-mail, ticket) e nenhuma spec escrita | Documento de spec em Markdown, com repositórios considerados, evidência de código e lacunas |
| [`interviewing-request-gaps`](interviewing-request-gaps/SKILL.md) | Uma spec já escrita tem itens abertos em `## Lacunas e perguntas abertas` | A mesma spec, com lacunas fechadas por decisão do usuário ou registradas como adiamento explícito |
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
| `Implementation Evidence` | Metadado de revisão | Estado atual Brownfield com status e referências `caminho:linha`; nunca é copiado para Acceptance Criteria |
| `Validation Summary` | Metadado de cobertura | Matriz requisito × evidência Brownfield, ou indicação de que não se aplica em Greenfield |
| `Refinement Status` | Metadado de revisão | Estado de Card, Conversation, Confirmation, prontidão e origem na spec; não é copiado automaticamente |

Com Confirmation `Ausente` ou `Parcial`, `Acceptance Criteria` permanece efetivamente vazio. Regras pendentes, hipóteses e justificativas continuam em `Description`/Conversation. A geração não cria nem altera work items.

## Exemplo mínimo

````markdown
# Backlog para Azure Boards

## Metadados e cobertura
- Spec de origem: seção 2 da spec de diligências
- Escopo analisado: seção 2
- Modo: Greenfield
- Raiz analisada: Não se aplica — nenhum código-fonte relevante disponível
- Código-fonte relevante: Ausente
- Incerteza de detecção: Nenhuma
- Itens não cobertos: Nenhum

## Validation Summary

Não se aplica — modo Greenfield; nenhum código-fonte relevante disponível.

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
Como analista,
quero reabrir uma diligência em até 24 horas,
para corrigir informações.
###### Conversation
A regra de prazo e o retorno para Em análise foram confirmados.
##### Implementation Evidence *(metadado de revisão — não é copiado para o Azure Boards; o campo Description termina no fim da Conversation acima)*
Não se aplica — modo Greenfield; nenhum código-fonte relevante disponível.
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

Execute a suíte completa das três skills com teste próprio:

```bash
uv run python -m unittest discover -s generating-azure-boards-backlog-from-spec/tests -v
uv run python -m unittest discover -s drafting-a-spec-from-business-request/tests -v
uv run python -m unittest discover -s interviewing-request-gaps/tests -v
```

Valide os seis pacotes com o utilitário oficial:

```bash
for skill_dir in \
  drafting-a-spec-from-business-request \
  generating-azure-boards-backlog-from-spec \
  interviewing-request-gaps \
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

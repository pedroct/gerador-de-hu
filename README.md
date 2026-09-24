# Gerador de Histórias de Usuário

Skills para transformar especificações em histórias de usuário refinadas e em um backlog Markdown pronto para revisão e posterior cadastro no Azure Boards, tanto sem implementação existente quanto comparando a spec com um projeto já implementado.

## O que o projeto faz

O fluxo combina dez capacidades complementares:

```text
Spec
 └─ gerar-backlog-azure-boards
     └─ refinar-historias-3c
         ├─ refinar-historias-3w
         └─ refinar-historias-gherkin
```

Quando não está claro por onde começar, `orquestrar-skills-de-requisito` decide a rota a partir do
material trazido. Ela classifica o que o material é — ID de Demanda, pedido informal, spec, backlog,
história solta, regras acordadas ou observação técnica — e aplica o fluxo abaixo, sem executar a
skill de destino:

```text
Material qualquer
 └─ orquestrar-skills-de-requisito
     ├─ rota principal (uma das skills abaixo)
     └─ análises opcionais a considerar
```

O julgamento do tipo de material usa o modelo Jev; a tabela de rotas fica em código, transcrita
deste README. Ela roteia e explica — nunca encadeia etapas nem roteia publicação.

Quando não existe spec escrita — só um pedido informal de negócio, como um e-mail ou ticket — a skill
`redigir-spec-pedido-negocio` investiga o código-fonte já disponível onde está instalada e
produz essa spec como um passo manual anterior:

```text
Pedido informal (e-mail, ticket) + código-fonte
 └─ redigir-spec-pedido-negocio
     └─ Spec (com lacunas documentadas)
```

Quando a Demanda de Negócio já existe no Azure Boards, `redigir-spec-demanda-azure-boards` a lê por
ID e usa `System.Title`, `Custom.DemandaAreaSolicitante`, `Custom.DemandaPublicoAlvo`,
`Custom.DemandaValorEsperado`, `Custom.DemandaDoraResolver` e `Custom.DemandaRegraseRestricoes` como
fonte rastreável para redigir a spec:

```text
ID da Demanda de Negócio + Azure Boards + código-fonte
 └─ redigir-spec-demanda-azure-boards
     ├─ Spec-base rastreável
     ├─ Spec de débitos, quando houver evidência
     ├─ Briefing UX-UI, quando aplicável
     └─ Parecer de copy, quando houver texto de interface
```

Se a spec resultante ainda tiver itens em `## Lacunas e perguntas abertas`, a skill
`entrevistar-lacunas-requisito` — quando instalada — fecha o máximo possível deles por entrevista em
rodadas, antes de a spec seguir manualmente para o backlog:

```text
Spec (com lacunas)
 └─ entrevistar-lacunas-requisito (opcional, se instalada)
     └─ Spec (lacunas fechadas ou adiadas por decisão explícita)
```

Depois da geração, Histórias que ficaram `Não pronta` não bloqueiam a entrega do backlog, mas a skill
sugere a mesma entrevista de lacunas — agora sobre as pendências de Card, Conversation e Confirmation
dessas Histórias — como próximo passo manual, repetido a cada rodada até todas ficarem `Prontas` ou até
o usuário adiar explicitamente uma lacuna:

```text
Backlog (com Histórias "Não pronta")
 └─ sugestão: registrar as lacunas em "## Lacunas e perguntas abertas" da spec
     └─ entrevistar-lacunas-requisito (opcional, se instalada)
         └─ Spec atualizada
             └─ gerar-backlog-azure-boards (nova rodada)
```

Antes ou durante a especificação, `revisar-textos-requisitos` pode revisar os textos voltados ao
usuário e apontar dúvidas de clareza, benefício, ação, tom e consistência:

```text
Requisito ou spec
 └─ revisar-textos-requisitos (opcional, se instalada)
     └─ Diagnóstico da copy + sugestões + decisões pendentes
```

Durante o entendimento ou refinamento, débitos técnicos podem ser registrados separadamente antes
de seguirem para o backlog:

```text
Débito técnico identificado
 └─ especificar-debitos-tecnicos
     └─ Spec de débitos priorizada
         └─ gerar-backlog-azure-boards (etapa manual)
```

Antes da geração do backlog, quando um requisito envolve tela nova ou fluxo de tela alterado em
front-end web ou mobile, `especificar-telas-ux-ui` identifica essa necessidade por inspeção de código —
nunca pelo texto de negócio — e anota a spec para consumo opcional do passo seguinte:

```text
Spec
 └─ especificar-telas-ux-ui (opcional, se instalada)
     └─ Spec anotada + Spec: Telas UX-UI — <contexto>
         └─ gerar-backlog-azure-boards (consome como arquivo opcional)
```

- **Orquestração das skills:** decide, a partir do material trazido, qual skill deve tratá-lo e quais análises opcionais considerar; roteia e explica, sem executar a skill de destino.
- **Drafting a partir de pedido de negócio:** investiga o código-fonte a partir de um pedido informal (e-mail, ticket) e produz a spec inicial, separando o que foi afirmado, evidenciado e lacunas.
- **Drafting a partir de Demanda no Azure Boards:** lê por ID, somente com `GET`, uma Demanda de Negócio já registrada, valida o tipo e o contrato de campos, e produz a spec rastreável a cada campo remoto, orquestrando as análises de débitos técnicos, telas UX-UI e copy quando seus gatilhos existirem.
- **Entrevista de lacunas:** fecha, por entrevista em rodadas, a seção de lacunas de uma spec já escrita, sem investigar código nem desenhar plano algum; referenciada condicionalmente por Drafting e, após a geração do backlog, como sugestão para fechar Histórias `Não pronta` — nunca obrigatória.
- **3W — Who, What, Why:** identifica ator, capacidade/resultado e valor, separando fatos de lacunas.
- **3C — Card, Conversation, Confirmation:** organiza o cartão, registra decisões e coordena a confirmação. É a única skill que define a prontidão geral.
- **Gherkin:** converte apenas regras confirmadas em exemplos verificáveis e classifica a Confirmation como `Ausente`, `Parcial` ou `Completa`.
- **Backlog a partir de spec:** agrupa requisitos rastreáveis em Épicos, Features e Histórias e sempre gera o documento Markdown revisável, marcando lacunas e Histórias incompletas como `Não pronta` em vez de bloquear a geração ou inventar fechamento só para completar o documento; para essas Histórias, sugere a entrevista de lacunas como próxima rodada.
- **Spec de débitos técnicos:** registra débitos encontrados no entendimento ou refinamento, classifica-os, prioriza-os e recomenda `User Story` ou `Bug` por item, sem criar work items no Azure Boards.
- **Telas UX-UI:** identifica, por inspeção somente leitura do código de front-end (web e mobile), quais requisitos exigem tela nova ou fluxo alterado; produz um brief em linguagem de UX-UI e uma anotação consumida opcionalmente por `gerar-backlog-azure-boards`, que cria uma User Story de design dependente do item funcional.

As dependências são acíclicas: 3W, Gherkin e a skill de débitos técnicos são folhas; a skill de backlog chama somente 3C; `redigir-spec-pedido-negocio` é uma predecessora isolada, que nunca chama nem é chamada pelas outras skills. `redigir-spec-demanda-azure-boards` é a única predecessora que orquestra as três análises especializadas (`especificar-debitos-tecnicos`, `especificar-telas-ux-ui` e `revisar-textos-requisitos`); ela não chama geração nem publicação de backlog. `entrevistar-lacunas-requisito` também é folha e nunca é chamada incondicionalmente nem invocada diretamente por outra skill — é só referenciada, de forma condicional, pelo fluxo de `redigir-spec-pedido-negocio` e, após a geração do backlog, pela sugestão de fechar Histórias `Não pronta` em `gerar-backlog-azure-boards`; em ambos os casos, quem decide rodá-la é o usuário. A skill de débitos técnicos pode ser chamada opcionalmente por 3C ou Drafting quando um débito for identificado e devolve sua spec separada para a geração manual do backlog. `especificar-telas-ux-ui` também é folha e nunca é chamada incondicionalmente; é referenciada, de forma condicional, por `redigir-spec-pedido-negocio` e consumida por `gerar-backlog-azure-boards` apenas como arquivo opcional, nunca como invocação.

## Instalação e atualização

As skills seguem o formato aberto (`SKILL.md` por pasta) suportado pelo [`npx skills`](https://skills.sh), que instala diretamente a partir deste repositório do GitHub — não é necessário publicar em nenhum registro. Funciona tanto para uso com Claude (Claude Code) quanto com agentes da OpenAI (Codex):

```bash
# listar as skills disponíveis no repositório
npx skills add pedroct/gerador-de-hu --list

# instalar todas, no projeto atual, para Claude Code
npx skills add pedroct/gerador-de-hu --all -a claude-code

# instalar todas, no projeto atual, para Codex (OpenAI)
npx skills add pedroct/gerador-de-hu --all -a codex

# instalar só uma skill específica
npx skills add pedroct/gerador-de-hu --skill redigir-spec-pedido-negocio -a claude-code
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

### Atualização

```bash
# atualizar todas as skills instaladas neste projeto
npx skills update -y

# atualizar só uma
npx skills update refinar-historias-3w -y

# escopo explícito, quando houver instalação nos dois lugares
npx skills update -p -y   # só as do projeto
npx skills update -g -y   # só as globais

# ver o que está instalado e de onde veio
npx skills ls
```

O `add` grava um `skills-lock.json` na raiz do projeto, com a origem e um hash de cada skill:

```json
{
  "version": 1,
  "skills": {
    "refinar-historias-3w": {
      "source": "pedroct/gerador-de-hu",
      "sourceType": "github",
      "skillPath": "refinar-historias-3w/SKILL.md",
      "computedHash": "f840b6b4410fd1ebbd50678cd67ed04dea8ce61feba37fa5a57f56868b190112"
    }
  }
}
```

É esse arquivo que o `update` lê para saber de onde re-buscar cada skill — por isso o comando não
repete o nome do repositório. Ele também **não** aceita `-a/--agent`, ao contrário do `add`: descobre
sozinho para quais agentes a skill está instalada e atualiza todos.

Uma ressalva: o `update` informa `✓ Updated` mesmo quando não havia nada novo a trazer. A mensagem
confirma que a skill foi ressincronizada com a origem, não que o conteúdo mudou. Para saber se algo
de fato mudou, compare o `computedHash` no `skills-lock.json` antes e depois.

### `update` não traz skills novas

**O `update` só ressincroniza o que já está no `skills-lock.json`.** Uma skill nova neste
repositório não é instalada nem mencionada: o comando termina com `✓ Updated N skill(s)` e o
projeto continua sem ela. Não há aviso.

O comando que traz skills novas é o `add` com curinga:

```bash
npx skills add pedroct/gerador-de-hu --skill '*' -a '*' -y
```

Ele é idempotente: repõe o que falta, preserva o que já está instalado e mantém o layout canônico.
Use-o como sincronização periódica, não o `update`.

Duas armadilhas que motivam a forma exata acima:

| Erro | O que acontece |
|---|---|
| `--skill nome1,nome2` | nomes separados por vírgula **não instalam nada**; o comando apenas lista as skills disponíveis |
| `-a claude-code` em vez de `-a '*'` | instala como **cópia** dentro de `.claude/skills/`, em vez do diretório canônico `.agents/skills/` com symlinks por agente. A cópia fica invisível para os outros agentes e não acompanha as atualizações |

Para conferir um projeto antes de sincronizar:

```bash
uv run python scripts/verificar_skills_instaladas.py /caminho/do/projeto
uv run python scripts/verificar_skills_instaladas.py /caminho/do/projeto --aplicar
```

O script aponta o que falta, o que sobra, o que está fora do `skills-lock.json`, quais viraram
cópia em vez de symlink e — o caso mais silencioso — quais estão instaladas com **conteúdo
desatualizado**. A comparação de conteúdo usa `git ls-files`, porque o que se distribui é o que
está versionado: um arquivo local ignorado pelo git, como um `tests/.env`, não existe na instalação
e não é divergência. Sai com código 1 quando há divergência, então serve em verificação
automatizada.

### Como usar depois de instalado

Abra o agente (Claude Code, Codex etc.) a partir do diretório onde a skill foi instalada — se o projeto tiver múltiplos repositórios irmãos (como api, front e mobile de uma mesma aplicação), abra a partir da raiz que os agrupa, não de dentro de um deles, para que `redigir-spec-pedido-negocio` consiga descobrir os repositórios relevantes.

A partir daí, duas formas funcionam:

1. **Chamando a skill explicitamente**, seguida do texto do pedido:

   ```
   /redigir-spec-pedido-negocio

   <cole aqui o texto do pedido enviado pela área de negócios>
   ```

2. **Deixando a detecção automática funcionar**: basta colar o texto do pedido numa conversa nova, sem digitar comando algum — a `description` do `SKILL.md` já orienta o agente a reconhecer um pedido informal sem spec escrita e acionar a skill sozinho.

## Início rápido

### Fluxo a partir de uma Demanda do Azure Boards

O caminho completo, de um ID até work items criados:

```text
ID da Demanda
 └─ 1. redigir-spec-demanda-azure-boards   → Spec rastreável + lacunas
     └─ 2. revisar as lacunas               ← passo humano
         └─ 3. gerar-backlog-azure-boards   → backlog.md
             └─ 4. validar                  → "Backlog válido: N itens"
                 └─ 5. publicar --demanda <id>
```

**1. Ler a Demanda e redigir a Spec.** Rode a partir da raiz da skill, não do repositório
investigado — a CLI resolve `scripts/` em relação a si mesma:

```bash
cd redigir-spec-demanda-azure-boards
uv run python scripts/consultar_demanda.py 13959 --env-file ../.env
```

A consulta é somente `GET`. Ela interrompe o fluxo se o ID não existir, se o tipo não for
`Demanda de Negócio` ou se o contrato de campos estiver inválido. Com o JSON em mãos, a skill
investiga o código em modo somente leitura e escreve a Spec.

**2. Revisar as lacunas — este passo é humano.** A Spec sai com uma seção
`Lacunas e perguntas abertas`, e ela existe por um motivo: gerar o backlog antes de fechá-las
produz Histórias `Não pronta` em massa. Use `entrevistar-lacunas-requisito` para fechar o que
der, ou leve as perguntas à área solicitante. Adiar uma lacuna é uma decisão legítima — desde
que explícita.

**3. Gerar o backlog.** A skill `gerar-backlog-azure-boards` decompõe a Spec em Épicos, Features
e itens de folha, chamando `refinar-historias-3c` para cada História ou Bug.

**4. Validar a estrutura** antes de qualquer chamada remota:

```bash
cd publicar-backlog-demanda-azure-boards
uv run python scripts/publicar_backlog_demanda.py validar ../backlog.md
```

**5. Publicar, em escada.** Cada degrau arrisca um pouco mais que o anterior:

```bash
# offline, sem token                          → confere o documento
uv run python scripts/publicar_backlog_demanda.py validar ../backlog.md

# um GET, nenhuma escrita                     → mostra o plano e o hash
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md   --demanda 13959 --simulacao

# valida no servidor com validateOnly=true    → exercita tipos, campos e o vínculo
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md   --demanda 13959 --validar-apenas

# cria os work items                          → exige a frase exata de autorização
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md   --demanda 13959 --manifesto docs/backlog/manifesto.json
```

> **Ao republicar, apague ou renomeie o manifesto antigo.** Se os work items foram removidos do
> board mas o manifesto continuar lá, a ferramenta compara o backlog com o que está registrado,
> conclui que não há nada pendente e responde `Nenhum item novo para publicar.` — sem criar nada.

### Fluxo Greenfield

1. Forneça uma spec à skill `gerar-backlog-azure-boards`.
2. Quando não houver código-fonte relevante disponível, a skill registra `Modo: Greenfield` e decompõe somente os requisitos rastreáveis da spec. Nenhuma inspeção de implementação é exigida.
3. Peça um backlog Markdown para Azure Boards e revise lacunas de 3W, Conversation e Confirmation.

### Fluxo Brownfield

1. Forneça a spec e a raiz do projeto existente. Se a presença de código relevante for ambígua, o fluxo assume Brownfield e registra essa incerteza.
2. A skill inspeciona código, testes e configuração em modo somente leitura antes do refinamento. Ela não executa scripts, testes, builds, servidores, migrações nem a aplicação sem autorização explícita.
3. Cada requisito da spec recebe evidência `caminho:linha`, status, impacto e confiança. O backlog cria trabalho para lacunas, divergências e mudanças; requisitos implementados permanecem na cobertura sem gerar duplicatas por padrão.

Nos dois fluxos, valide a estrutura do arquivo gerado:

```bash
cd gerar-backlog-azure-boards
uv run python scripts/validate_backlog.py caminho/para/backlog.md
```

O validador retorna `A estrutura do backlog é válida` quando a hierarquia, as chaves, os pais e os campos obrigatórios estão corretos.

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
| [`orquestrar-skills-de-requisito`](orquestrar-skills-de-requisito/SKILL.md) | Não está claro por qual skill começar diante do material trazido | Skill a chamar, motivo e análises opcionais a considerar |
| [`redigir-spec-demanda-azure-boards`](redigir-spec-demanda-azure-boards/SKILL.md) | ID de uma Demanda de Negócio já criada no Azure Boards | Spec rastreável à Demanda e documentos companheiros |
| [`redigir-spec-pedido-negocio`](redigir-spec-pedido-negocio/SKILL.md) | Só há um pedido informal de negócio (e-mail, ticket) e nenhuma spec escrita | Documento de spec em Markdown, com repositórios considerados, evidência de código e lacunas |
| [`entrevistar-lacunas-requisito`](entrevistar-lacunas-requisito/SKILL.md) | Uma spec já escrita tem itens abertos em `## Lacunas e perguntas abertas` | A mesma spec, com lacunas fechadas por decisão do usuário ou registradas como adiamento explícito |
| [`revisar-textos-requisitos`](revisar-textos-requisitos/SKILL.md) | Requisitos ou specs contêm copy voltada ao usuário | Diagnóstico de copy, sugestões de texto e decisões pendentes |
| [`refinar-historias-3w`](refinar-historias-3w/SKILL.md) | Ator, objetivo ou benefício estão vagos | Mapa 3W, história/rascunho, perguntas e estado 3W |
| [`refinar-historias-3c`](refinar-historias-3c/SKILL.md) | A história precisa de conversa e confirmação | Card, Conversation, Confirmation e prontidão 3C |
| [`refinar-historias-gherkin`](refinar-historias-gherkin/SKILL.md) | Regras confirmadas precisam de exemplos BDD | Regras, Gherkin e estado local da Confirmation |
| [`gerar-backlog-azure-boards`](gerar-backlog-azure-boards/SKILL.md) | Uma spec precisa virar backlog hierárquico | Documento Markdown de backlog e itens não cobertos |
| [`especificar-telas-ux-ui`](especificar-telas-ux-ui/SKILL.md) | Um requisito da spec pode exigir tela nova ou fluxo de tela alterado em web e/ou mobile | Anotação de necessidade de tela na spec + `Spec: Telas UX-UI` com Card, roteiro de tela e evidência de código, por plataforma |
| [`especificar-debitos-tecnicos`](especificar-debitos-tecnicos/SKILL.md) | Débitos técnicos foram identificados durante entendimento ou refinamento | Spec priorizada, rastreável e pronta para geração de backlog |

## Formato do backlog

As chaves são localizadores documentais, não IDs do Azure Boards:

```text
1.0.0 Épico
1.1.0 Feature
1.1.1 História de Usuário
```

Cada Feature declara `Parent` apontando para um Épico existente; cada História declara `Parent` apontando para uma Feature existente. Em atualizações, chaves publicadas são preservadas e lacunas removidas não são reutilizadas.

### Mapeamento para Azure Boards

| Documento Markdown | Tipo remoto | Campo Azure Boards | Conteúdo |
|---|---|---|---|
| `Description` | Epic, Feature, User Story | `System.Description` | Card 3W e síntese da Conversation, incluindo decisões, propostas não confirmadas e lacunas |
| `Description` | Bug | `Microsoft.VSTS.TCM.ReproSteps` | o mesmo conteúdo, no campo que o formulário do Bug exibe |
| `Acceptance Criteria` | tipos que expõem o campo | `Microsoft.VSTS.Common.AcceptanceCriteria` | Somente blocos Gherkin da Confirmation quando o estado for `Completa` |
| `Acceptance Criteria` | tipos que **não** expõem | nenhum | o conteúdo é descartado, e a publicação avisa antes de pedir a autorização |
| `Implementation Evidence` | todos | Metadado de revisão | Estado atual Brownfield com status e referências `caminho:linha`; nunca é copiado para Acceptance Criteria |

Com Confirmation `Ausente` ou `Parcial`, `Acceptance Criteria` permanece efetivamente vazio. Regras pendentes, hipóteses e justificativas continuam em `Description`/Conversation. A geração não cria nem altera work items.

**Por que o Bug é diferente.** No processo Agile, o formulário do Bug exibe *Repro Steps* e não
*Description*: gravar a narrativa em `System.Description` faz o conteúdo existir na API e ficar
invisível no work item. Os tipos que expõem `Microsoft.VSTS.TCM.ReproSteps` recebem a narrativa lá.
Pelo mesmo motivo, um tipo que não expõe `Microsoft.VSTS.Common.AcceptanceCriteria` — o `Bug`, em
muitos processos — teria seus critérios descartados em silêncio; as duas skills publicadoras
listam os itens afetados antes de solicitar a frase de autorização. Ambos os comportamentos foram
descobertos em publicação real, não em teste.

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

Origem na spec: seção 2.1.
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

Execute a suíte completa das skills com teste próprio:

```bash
uv run pytest gerar-backlog-azure-boards/tests -v
uv run pytest redigir-spec-pedido-negocio/tests -v
uv run pytest entrevistar-lacunas-requisito/tests -v
uv run pytest especificar-debitos-tecnicos/tests -v
uv run pytest especificar-telas-ux-ui/tests -v
uv run pytest redigir-spec-demanda-azure-boards/tests -v
uv run pytest orquestrar-skills-de-requisito/tests -v
uv run pytest refinar-historias-3w/tests -v
uv run pytest especificar-debitos-tecnicos/tests -v
uv run pytest tests -v
```

Valide os dez pacotes com o utilitário oficial:

```bash
for skill_dir in \
  redigir-spec-pedido-negocio \
  gerar-backlog-azure-boards \
  entrevistar-lacunas-requisito \
  refinar-historias-3c \
  refinar-historias-3w \
  refinar-historias-gherkin \
  especificar-telas-ux-ui \
  especificar-debitos-tecnicos \
  redigir-spec-demanda-azure-boards \
  orquestrar-skills-de-requisito; do
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

## Fluxo de publicação autorizada

O backlog segue o fluxo manual **geração → revisão → autorização → publicação**. A geração continua
produzindo Markdown para revisão; a skill publicadora valida esse documento, apresenta um plano e só
chama a REST API depois de uma frase de confirmação exata. Nenhuma das duas publica automaticamente,
e o manifesto de retomada não equivale a uma autorização.

Existem duas publicadoras, e a diferença entre elas é onde a hierarquia nasce:

| Skill | Publica | Area Path e Iteration Path | Títulos |
|---|---|---|---|
| [`publicar-backlog-azure-boards`](publicar-backlog-azure-boards/SKILL.md) | Épicos soltos no projeto | configurados por execução | `<data> <chave> Título` |
| [`publicar-backlog-demanda-azure-boards`](publicar-backlog-demanda-azure-boards/SKILL.md) | Épicos filhos de uma Demanda de Negócio existente | herdados da Demanda | `01.01.01 Título` |

```text
gerar-backlog-azure-boards
  → backlog Markdown
  → revisão humana
  ├─ publicar-backlog-azure-boards validar/planejar
  │    → AUTORIZAR PUBLICAÇÃO 3 ITENS ...
  │    → Azure Boards (Épicos soltos no projeto)
  └─ publicar-backlog-demanda-azure-boards validar/planejar --demanda <id>
       → AUTORIZAR PUBLICAÇÃO 3 ITENS DEMANDA <id> ...
       → Azure Boards (Épicos filhos da Demanda)
```

Quando a spec nasceu de `redigir-spec-demanda-azure-boards`, o ID da Demanda já é conhecido, e a
segunda publicadora fecha a rastreabilidade: a Demanda que originou a spec passa a listar como
filhos os Épicos gerados a partir dela. A Demanda em si nunca é escrita — o vínculo nasce do lado do
Épico, no mesmo POST que o cria.

### CLI

Vinculada a uma Demanda de Negócio:

```bash
cd publicar-backlog-demanda-azure-boards
uv run python scripts/publicar_backlog_demanda.py validar ../backlog.md
uv run python scripts/publicar_backlog_demanda.py planejar ../backlog.md --demanda 13959
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md --demanda 13959 --simulacao
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md --demanda 13959 --validar-apenas
uv run python scripts/publicar_backlog_demanda.py publicar ../backlog.md --demanda 13959
```

Aqui `Area Path` e `Iteration Path` não são informados: vêm da Demanda. Em compensação, `planejar` e
`--simulacao` exigem token, porque precisam lê-la; só `validar` é totalmente offline.

Solta no projeto:

```bash
cd publicar-backlog-azure-boards
uv run python scripts/publicar_backlog.py validar ../backlog.md
uv run python scripts/publicar_backlog.py planejar ../backlog.md \
  --projeto Projeto --area-path Projeto --iteration-path 'Projeto\\Sprint 18'
uv run python scripts/publicar_backlog.py publicar ../backlog.md --simulacao
uv run python scripts/publicar_backlog.py publicar ../backlog.md --validar-apenas
uv run python scripts/publicar_backlog.py publicar ../backlog.md
```

Na publicação, a ferramenta mostra organização, projeto, Area Path, Iteration Path, quantidades,
ordem, relações, manifesto e hash. Depois pergunta entre backlog inteiro, lotes ou cancelamento e
solicita a frase integral, como `AUTORIZAR PUBLICAÇÃO 3 ITENS Projeto Projeto Projeto\\Sprint 18
7F3A`. Não existe opção `--yes`; confirmação ausente ou incorreta resulta em zero chamadas de
criação.

### Variáveis de ambiente

O roteador, o gate 3W assistido e a priorização de débitos usam o modelo Jev pela Decisions
API do OpenRouter:

```dotenv
JEV_OPENROUTER_API=
```

```dotenv
AZURE_DEVOPS_ORGANIZACAO=minha-organizacao
AZURE_DEVOPS_PROJETO=Projeto
AZURE_DEVOPS_AREA_PATH=Projeto
AZURE_DEVOPS_ITERATION_PATH=Projeto\\Sprint 2026\\Sprint 18
AZURE_DEVOPS_TIPO_USER_STORY=User Story
AZURE_DEVOPS_TOKEN=
```

O `Iteration Path` é definido por execução e não pertence ao backlog Markdown. Se houver:

```dotenv
AZURE_DEVOPS_AREA_PATHS=Sustentacao,Projeto
```

sem `AZURE_DEVOPS_AREA_PATH` ou `--area-path`, a seleção entre `Sustentacao` e `Projeto` deve ser
explícita; a ferramenta não escolhe silenciosamente. Nunca versionar token: mantenha-o vazio nos
arquivos de exemplo e forneça-o apenas por variável de ambiente ou mecanismo seguro do sistema
operacional.

Na publicadora vinculada à Demanda, `AZURE_DEVOPS_AREA_PATH`, `AZURE_DEVOPS_AREA_PATHS` e
`AZURE_DEVOPS_ITERATION_PATH` não existem; no lugar deles entram:

```dotenv
AZURE_DEVOPS_DEMANDA=13959
AZURE_DEVOPS_TIPO_DEMANDA=Demanda de Negócio
```

O ID da Demanda participa do hash do plano, da frase de autorização e do manifesto: uma frase
emitida para uma Demanda não autoriza publicar sob outra.

Em processos Scrum, defina `AZURE_DEVOPS_TIPO_USER_STORY=Product Backlog Item`; esse mapeamento
integra o plano e seu hash. O token digitado interativamente não produz eco. Na publicadora solta, a
simulação é totalmente local, não solicita token e não faz chamadas HTTP; na vinculada à Demanda,
ela faz exatamente um `GET` e nenhuma escrita.

O MCP do Azure DevOps é opcional e pode ajudar na inspeção. A publicação principal usa a REST API,
com validador estrutural antes do planejamento, confirmação vinculada ao plano completo, ordem
determinística e manifesto. Um POST de criação com resultado ambíguo não é repetido: o manifesto
exige reconciliação manual antes de qualquer nova escrita.

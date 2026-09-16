# Design: especificar-telas-ux-ui — necessidade de tela a partir da Spec

## Contexto

O pipeline atual (`redigir-spec-pedido-negocio` → `entrevistar-lacunas-requisito` →
`gerar-backlog-azure-boards` → `refinar-historias-3c` → `refinar-historias-3w`/`refinar-historias-gherkin`
→ `publicar-backlog-azure-boards`) decompõe uma Spec em Épicos, Features e itens de folha (User Story ou
Bug) prontos para o dev fullstack implementar. Nenhuma etapa hoje identifica, separadamente do texto de
negócio, quando um requisito exige que a equipe de UX-UI desenhe uma tela nova ou altere um fluxo de tela
existente antes que a implementação possa começar. O efeito prático observado: um requisito que precisa
de tela nova chega ao dev fullstack misturado ao restante do Card, sem nenhum sinal de que há um trabalho
de design pendente e bloqueante, e sem conteúdo em linguagem acessível para a equipe de UX-UI acompanhar
o que precisa ser construído.

O Design System do produto está no Figma, mas a organização tem licença para apenas dois usuários
simultâneos — não há capacidade de dar a esta skill acesso de leitura ao Figma sem competir com o uso da
própria equipe de design. A skill precisa funcionar inteiramente por texto (Spec e código-fonte),
delegando à equipe de UX-UI a checagem manual contra o Design System real.

O produto tem front-end web e aplicativo mobile, e as duas plataformas podem estar em estágios de
maturidade diferentes: uma pode ter a tela já implementada enquanto a outra ainda não existe.

## Objetivos

1. Criar uma skill nova, `especificar-telas-ux-ui`, que roda sobre uma Spec (antes da geração do
   backlog) e identifica, por requisito e por plataforma (web, mobile), se uma tela nova ou um fluxo de
   tela alterado precisa ser especificado antes que a implementação funcional possa avançar.
2. Decidir essa necessidade por **inspeção somente leitura do código de front-end existente**, nunca por
   interpretação do texto de negócio — a área de negócio não tem como saber se uma tela já cobre o
   requisito ou não.
3. Produzir conteúdo em linguagem acessível à equipe de UX-UI (sem sintaxe Gherkin, sem jargão de
   automação de teste), rastreável ao requisito de origem.
4. Registrar a necessidade de tela como uma anotação na própria Spec, para que
   `gerar-backlog-azure-boards` a consuma como input opcional e crie, para cada (requisito, plataforma)
   sinalizado, uma User Story de design **separada** do item funcional, com uma relação explícita de
   dependência entre os dois.
5. Preservar a arquitetura já testada do repositório: a skill nova é folha, não é `REQUIRED SUB-SKILL` de
   ninguém, não é chamada automaticamente por ninguém, e não altera a exclusividade da 3C sobre a
   prontidão geral de um item.

## Fora de escopo

- **Acesso ao Figma ou a qualquer ferramenta de design externa.** A licença de dois usuários simultâneos
  torna inviável dar acesso de leitura à skill; toda a análise é textual (Spec + código-fonte).
- **Definição do copy final de interface** (título, label, CTA, mensagem de sucesso/erro/vazio, tooltip).
  Isso é escopo de `revisar-textos-requisitos`, indicada como próximo passo manual opcional — nunca
  chamada automaticamente por esta skill.
- **Criar item de tipo Task.** O contrato do backlog já proíbe (`Não gere tarefas técnicas abaixo dos
  itens de folha`); a necessidade de tela sempre vira uma User Story de design nova, nunca uma subtarefa
  do item existente.
- **Criar o link formal Predecessor/Sucessor no Azure Boards.** A dependência entre a User Story de
  design e o item funcional fica registrada como texto em `Depende de`/`Bloqueia` na Description de
  ambos. Criar a relação real na API do Azure Boards é trabalho futuro de `publicar-backlog-azure-boards`,
  que hoje só publica a relação `Parent`.
- **Dividir o item funcional por plataforma.** Esta skill não decide como `gerar-backlog-azure-boards`
  agrupa o trabalho de implementação em si; ela só multiplica os itens de **design** por plataforma
  quando necessário (ver regra de agrupamento).
- **Validar automaticamente a integridade referencial de `Depende de`/`Bloqueia` no validador
  estrutural.** Fica registrado aqui como melhoria desejável para uma iteração futura de
  `scripts/validate_backlog.py`; não é pré-requisito para esta skill funcionar.
- **Qualquer inspeção que não seja somente leitura.** Sem build, testes, servidores, migrações ou
  execução do app — mesma restrição já aplicada a toda inspeção Brownfield no repositório.

## Nome e posição no pipeline

Nome escolhido: `especificar-telas-ux-ui`, seguindo o padrão de nomeação `verbo-objeto` já usado por
`especificar-debitos-tecnicos`.

Estágio pré-backlog, skill-folha, opcional — roda sobre uma Spec já escrita (de
`redigir-spec-pedido-negocio` ou de qualquer outra origem, já que `gerar-backlog-azure-boards` também
aceita spec genérica). É sugerida, nunca chamada automaticamente, por `redigir-spec-pedido-negocio` como
mais um próximo passo manual opcional (mesmo padrão de `entrevistar-lacunas-requisito` e
`revisar-textos-requisitos` hoje).

```text
Spec (com lacunas fechadas, se aplicável)
 └─ especificar-telas-ux-ui (nova, folha, opcional)
     ├─ anota a Spec: "## Necessidade de especificação de tela"
     └─ produz: Spec: Telas UX-UI — <contexto>  (documento separado)
         └─ gerar-backlog-azure-boards (lê a anotação como input opcional, por arquivo)
             ├─ cria a User Story de design (item-irmão, uma por plataforma sinalizada)
             ├─ cria o item funcional (User Story ou Bug, decisão inalterada)
             └─ preenche "Depende de" / "Bloqueia" com as chaves reais E.F.S
                 └─ refinar-historias-3c roda normalmente em AMBOS os itens
                     └─ o roteiro de tela vira insumo da Conversation/Gherkin do item de design
```

O roteiro de tela não substitui a 3C nem a Gherkin — ele é a matéria-prima em linguagem simples que a 3C
formaliza depois, quando a User Story de design entra no fluxo padrão de refinamento. A 3C continua sendo
a única dona da prontidão geral de qualquer item, incluindo o de design.

## Modo, por plataforma

O Modo (Greenfield-UI ou Brownfield-UI) é declarado **separadamente para web e para mobile**, porque as
duas plataformas podem estar em estágios de maturidade diferentes:

- **Greenfield-UI:** nenhum código de front-end relevante acessível para aquela plataforma. Todo
  requisito com faceta de UI aplicável a ela é tratado como "necessita especificação de tela", porque não
  há nada para comparar. Registre a ausência.
- **Brownfield-UI:** há código acessível para aquela plataforma. Inspecione somente leitura — rotas,
  páginas, telas, componentes — em busca de uma tela ou fluxo equivalente ao requisito.
- Presença ambígua em qualquer plataforma → trate como Brownfield-UI conservador para ela, registrando a
  incerteza e os limites da busca, nunca concluindo ausência de tela pela falta de investigação.
- Se o produto genuinamente não tiver uma das plataformas no seu escopo (por exemplo, não existe app
  mobile), registre `Não aplicável` para ela — distinto de `Impossível validar` (a plataforma existe, mas
  não foi possível inspecionar o código correspondente).

A descoberta de repositório segue o mesmo padrão já usado por `redigir-spec-pedido-negocio`: investigar a
partir do diretório onde a skill está instalada e de seus repositórios irmãos, procurando sinais
convencionais de cada stack (por exemplo, front-end web via framework de rotas/páginas; mobile via
projeto React Native, Flutter ou nativo Android/iOS). Repositórios candidatos e descartados são
registrados com o motivo, no mesmo espírito de "Repositórios considerados" daquela skill.

## Classificação por requisito × plataforma

1. **Determine a(s) plataforma(s) aplicável(is)** a cada requisito: se a Spec especificar explicitamente
   uma plataforma, use essa; caso contrário, o requisito se aplica a todas as plataformas que existirem
   no produto (uma plataforma `Não aplicável` fica de fora da análise).
2. **Confirme a faceta de UI** do requisito a partir do texto da Spec. Sem faceta de UI, ignore — não
   inspeciona código nenhum para esse requisito.
3. **Para cada par (requisito, plataforma) com faceta de UI**, inspecione o código daquela plataforma
   somente leitura, buscando tela ou fluxo equivalente, com evidência `caminho:linha`.
4. **Classifique com o vocabulário já estabelecido** no repositório — sem inventar rótulo novo:
   `Implementado`, `Parcialmente implementado`, `Não encontrado`, `Impossível validar`, mais o rótulo
   `Não aplicável` específico desta skill para plataforma inexistente no produto.
5. **Gere um item de design somente quando o status não for `Implementado`** (ou seja, para
   `Parcialmente implementado`, `Não encontrado` ou `Impossível validar`). Ausência de evidência nunca é
   serializada como `Implementado` — mesma disciplina já aplicada em toda inspeção Brownfield do
   repositório.

## Regra de agrupamento em itens de design

**Sempre um item de design por plataforma necessária** — nunca agrupa web e mobile no mesmo item de
design, mesmo quando o item funcional correspondente for único para as duas plataformas. Um requisito que
precisa de tela em web e mobile gera dois itens de design (por exemplo, "Especificar tela web de X" e
"Especificar tela mobile de X"), cada um bloqueando o mesmo item funcional. O item funcional registra
`Depende de` com uma chave por item de design que o bloqueia.

## Formato das saídas

### 1. Anotação na Spec

Nova seção acrescentada ao final da Spec:

```markdown
## Necessidade de especificação de tela
| Requisito | Plataforma | Status de cobertura | Referência |
|---|---|---|---|
| [seção/âncora do requisito] | Web \| Mobile | Não encontrado \| Parcialmente implementado \| Impossível validar | TL-01 |
```

Se nenhum requisito precisar de tela, registre explicitamente `Nenhuma necessidade de tela identificada`
em vez de omitir a seção.

### 2. Documento separado — `Spec: Telas UX-UI — <contexto>`

Mesmo estilo de documento que `especificar-debitos-tecnicos` já produz: um item por (requisito,
plataforma) sinalizado.

```markdown
# Spec: Telas UX-UI — <contexto>

## Contexto e origem
<spec de origem, seção ou demanda relacionada>

## Descoberta de plataformas
| Plataforma | Repositório considerado | Relevante? | Motivo |
|---|---|---|---|
| Web | [nome ou "nenhum encontrado"] | Sim/Não | [justificativa] |
| Mobile | [nome ou "nenhum encontrado"] | Sim/Não | [justificativa] |

## Modo
- Modo Web: Greenfield-UI | Brownfield-UI
- Modo Mobile: Greenfield-UI | Brownfield-UI

## Resumo priorizado
| Item | Requisito de origem | Plataforma | Status de cobertura |
|---|---|---|---|
| TL-01 | ... | Web | Não encontrado |

## TL-01 — <título curto, com a plataforma no nome>
### Título
<título curto, acionável, sem ID do Azure Boards>
### Origem
<seção/âncora da Spec>
### Plataforma
Web ou Mobile
### Card
Como equipe de UX-UI, quero especificar a tela <plataforma> de <resultado>, para permitir a
implementação de <requisito de origem>.
### Evidência de código
- Status: Implementado | Parcialmente implementado | Não encontrado | Impossível validar | Não aplicável
- Referência: `caminho:linha`, ou o motivo quando não houver referência
### Roteiro de tela
Lista numerada, em linguagem simples, sem sintaxe Gherkin: situação → ação do usuário → o que muda na
tela. Cada item rastreável a uma regra ou trecho do requisito de origem.
### Necessidade de copy
Se houver texto voltado ao usuário (label, mensagem, CTA, estado vazio/erro): liste os pontos e indique
`revisar-textos-requisitos` como próximo passo manual opcional. Se não houver, escreva "Não
identificada".
### Referências ao Design System
Componente ou padrão já conhecido pela Spec ou pelo código (ex.: "reaproveitar o componente de tabela
paginada usado em X"). Nunca invente um componente sem essa origem; sem referência confiável, escreva
"Nenhuma referência confiável disponível".
### Bloqueia
Referência ao requisito funcional de origem por seção/âncora da Spec. A chave real `E.F.S` é preenchida
por `gerar-backlog-azure-boards` quando o backlog for gerado.
### Lacunas
Perguntas ou decisões pendentes que impediram uma conclusão mais forte.
```

## Mudanças em `gerar-backlog-azure-boards`

- **`SKILL.md`:** novo passo lendo a seção `## Necessidade de especificação de tela` da Spec e o
  documento `Spec: Telas UX-UI` (quando fornecidos) como input opcional por arquivo — mesmo padrão já
  usado pelo mapa de capacidades. Para cada item sinalizado, cria a User Story de design como item-irmão
  do item funcional, sob a mesma Feature, e preenche `Depende de`/`Bloqueia` com as chaves reais `E.F.S`
  após a numeração. Ambos os itens passam pelo fluxo `refinar-historias-3c` normalmente — o roteiro de
  tela é fornecido como contexto rotulado de entrada para a Conversation/Gherkin do item de design, não
  para o item funcional.
- **`references/backlog-markdown-contract.md`:** documenta um novo campo opcional, `Depende de` (no item
  funcional, uma ou mais chaves) e `Bloqueia` (no item de design, uma chave), presentes apenas quando o
  item nasceu do fluxo de telas. Não altera `Parent`, não altera a regra de prontidão da 3C, e não é
  tratado como novo nível hierárquico — é texto informativo dentro de `Description`, na mesma seção da
  Conversation.
- **`tests/test_skill_integration.py`:** novas asserções confirmando que o campo `Depende de`/`Bloqueia`
  é opcional, que só aparece quando a Spec traz a seção de telas, e que não substitui `Parent` nem afeta
  o cálculo de prontidão.

## Boundaries da skill nova

- Não acessa Figma nem qualquer ferramenta de design externa; toda a análise é Spec + código-fonte.
- Não decide nem escreve copy final de interface; indica `revisar-textos-requisitos` como revisão manual
  opcional quando o roteiro de tela envolve texto voltado ao usuário.
- Não executa build, testes, servidores ou o aplicativo; inspeção somente leitura, mesma restrição já
  aplicada a toda investigação Brownfield do repositório.
- Não inventa componente ou padrão de Design System sem origem confirmada na Spec ou no código.
- Não decide prontidão nem substitui a 3C/Gherkin; o roteiro de tela é insumo, não veredito.
- Não cria, atualiza ou publica work items no Azure Boards.
- Nunca serializa `Implementado` por ausência de evidência de código.
- Não divide o item funcional por plataforma — só multiplica o item de design quando necessário.
- Não é `REQUIRED SUB-SKILL` de ninguém e não invoca nenhuma outra skill do repositório; é folha.

## Arquitetura de skills (pipeline atualizado)

```text
Pedido informal (e-mail, ticket) + código-fonte
        |
        v
redigir-spec-pedido-negocio                 (inalterada, com nova sugestão opcional)
        |
        |  Spec (com lacunas documentadas)
        v
entrevistar-lacunas-requisito                (opcional, inalterada)
        |
        |  Spec com lacunas fechadas
        v
especificar-telas-ux-ui                      (NOVA, folha, opcional)
        |
        |  Spec anotada + Spec: Telas UX-UI
        v
gerar-backlog-azure-boards                   (lê a anotação como input opcional)
        |
        |  REQUIRED SUB-SKILL
        v
refinar-historias-3c                          (→ 3w, gherkin, inalteradas)
        |
        v
publicar-backlog-azure-boards                 (inalterada nesta iteração)
```

`especificar-telas-ux-ui` não é chamada por ninguém automaticamente e não chama ninguém. Quem instalar
apenas `gerar-backlog-azure-boards` continua funcionando sem ela — a seção de telas na Spec e o documento
companheiro são inputs opcionais, não uma dependência obrigatória.

## Arquivos previstos

```text
especificar-telas-ux-ui/
├── SKILL.md
├── references/
│   └── ui-brownfield-validation.md
├── agents/openai.yaml
└── tests/test_skill_integration.py
```

Também modificados:

| Arquivo | Mudança |
|---|---|
| `gerar-backlog-azure-boards/SKILL.md` | Novo passo: input opcional da anotação de telas; pareamento de item-irmão de design; preenchimento de `Depende de`/`Bloqueia` |
| `gerar-backlog-azure-boards/references/backlog-markdown-contract.md` | Novo campo opcional `Depende de`/`Bloqueia`, documentado sem alterar `Parent` nem a regra de prontidão |
| `gerar-backlog-azure-boards/tests/test_skill_integration.py` | Asserções novas sobre o campo opcional |
| `redigir-spec-pedido-negocio/SKILL.md` | Sugestão opcional de `especificar-telas-ux-ui` como próximo passo manual, quando a Spec tiver faceta de UI |
| `README.md` | Nova linha na tabela de skills; diagrama de fluxo atualizado com o novo estágio |
| `pyproject.toml` | `testpaths` da skill nova |

`gerar-backlog-azure-boards/scripts/validate_backlog.py` não é alterado nesta iteração — a validação da
integridade referencial de `Depende de`/`Bloqueia` fica registrada em *Fora de escopo* como melhoria
futura.

## Ordem de implementação

1. **Skill nova isolada** (`especificar-telas-ux-ui/` completa, com `SKILL.md`,
   `references/ui-brownfield-validation.md`, `agents/openai.yaml` e teste de isolamento). Não depende de
   nenhuma mudança em `gerar-backlog-azure-boards` para existir e ser útil sozinha (produz as duas
   saídas mesmo que ninguém as consuma ainda).
2. **Consumo em `gerar-backlog-azure-boards`** (novo passo no `SKILL.md`, campo `Depende de`/`Bloqueia`
   no contrato, testes estendidos). Depende de (1) para saber o formato exato da anotação na Spec e do
   documento `Spec: Telas UX-UI`.
3. **Sugestão em `redigir-spec-pedido-negocio`** e atualização de `README.md`/`pyproject.toml`. Depende
   de (1) existir para ser referenciável; independente de (2).

## Estratégia de testes

1. Teste estático próprio de `especificar-telas-ux-ui`, no padrão das outras skills-folha: confirma que é
   folha (não invoca nenhuma outra skill do repositório), que nunca cria item do tipo Task ou Bug para
   necessidade de tela, que o Modo é declarado por plataforma, que `Não aplicável` e `Impossível validar`
   nunca são confundidos com `Implementado`, e que o formato de saída cobre as seções descritas acima.
2. Teste confirmando a regra de agrupamento: um requisito sinalizado em duas plataformas produz dois
   itens de design distintos, nunca um único item combinado.
3. Teste confirmando a delegação de copy: um roteiro de tela com texto voltado ao usuário aponta
   `revisar-textos-requisitos` como próximo passo manual, sem definir o texto final.
4. Teste estendido em `gerar-backlog-azure-boards/tests/test_skill_integration.py`: confirma que o campo
   `Depende de`/`Bloqueia` é opcional, aparece apenas quando a Spec traz a seção de telas, e não altera o
   cálculo de prontidão feito pela 3C.
5. `uv run pytest -v` completo, sem regressão nas skills existentes.

## Critérios de conclusão

- `especificar-telas-ux-ui` existe, com `SKILL.md`, `references/ui-brownfield-validation.md`,
  `agents/openai.yaml` e teste de isolamento, e produz as duas saídas no formato acima.
- A necessidade de tela é decidida por inspeção de código, nunca por interpretação do texto de negócio.
- Web e mobile têm Modo declarado separadamente, e um requisito que precisa de tela nas duas plataformas
  gera dois itens de design distintos.
- `gerar-backlog-azure-boards` consome a anotação de telas como input opcional, cria o item-irmão de
  design e preenche `Depende de`/`Bloqueia`, sem alterar `Parent` nem a exclusividade da 3C sobre a
  prontidão.
- Nenhuma copy final de interface é definida por `especificar-telas-ux-ui`; a skill sempre delega a
  `revisar-textos-requisitos` quando há texto voltado ao usuário.
- Nenhum work item é criado por qualquer skill; a proibição segue intacta.
- `uv run pytest -v` passa por completo, sem regressão.

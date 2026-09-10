# Design: geração de backlog do Azure Boards a partir de uma spec

## Contexto

O fluxo atual possui três skills:

- `refining-user-stories-with-3w`: estrutura Who, What e Why;
- `refining-user-stories-with-3c`: orquestra Card, Conversation e Confirmation e mapeia os campos do Azure Boards;
- `refining-user-stories-with-gherkin`: transforma regras confirmadas em exemplos verificáveis.

O próximo passo é analisar uma especificação inteira, decompor seu conteúdo na hierarquia do processo Agile do Azure Boards e gerar um documento Markdown revisável antes da inserção dos work items.

## Objetivos

1. Criar a skill `generating-azure-boards-backlog-from-spec`.
2. Gerar um Markdown hierárquico no formato Épico → Feature → História de Usuário.
3. Aplicar 3W, 3C e Gherkin em cada história sem duplicar suas regras.
4. Produzir `Description` e `Acceptance Criteria` prontos para transferência ao Azure Boards.
5. Preservar rastreabilidade até a spec e explicitar lacunas sem fabricar requisitos.
6. Eliminar dependências circulares e centralizar a prontidão geral na 3C.

## Fora de escopo

- Criar ou modificar work items no Azure Boards.
- Definir Area Path, Iteration Path, Story Points, prioridade, responsável ou datas sem fonte explícita.
- Converter automaticamente qualquer formato binário de spec; quando necessário, a skill apropriada ao formato deve extrair o conteúdo antes da decomposição.
- Tratar a numeração do documento como ID atribuído pelo Azure Boards.
- Criar tarefas técnicas abaixo das histórias.

## Hierarquia e numeração

No processo Agile do Azure Boards, histórias são filhas de Features e Features são filhas de Épicos. A numeração do Markdown será uma chave documental:

| Nível | Formato | Exemplo |
|---|---|---|
| Épico | `E.0.0` | `1.0.0` |
| Feature | `E.F.0` | `1.1.0` |
| História | `E.F.S` | `1.1.1` |

Regras:

- `E`, `F` e `S` são inteiros positivos sequenciais.
- Cada Feature referencia exatamente um Épico pai.
- Cada história referencia exatamente uma Feature pai.
- Em um documento novo, a sequência começa em 1 em cada nível.
- Ao atualizar um backlog existente, preserve chaves já publicadas e acrescente novas chaves ao final do respectivo pai; não reutilize chaves removidas.
- A chave documental nunca é apresentada como Azure work item ID.

## Decomposição da spec

1. Inventariar objetivos, atores, capacidades, regras, restrições, exemplos e dúvidas com suas seções de origem.
2. Identificar Épicos como iniciativas ou objetivos amplos que agrupam múltiplas capacidades.
3. Identificar Features como capacidades significativas que entregam valor e agrupam histórias relacionadas.
4. Identificar histórias como resultados coesos para um ator, passíveis de refinamento independente.
5. Aplicar `refining-user-stories-with-3c` a cada história candidata.
6. Não criar um item apenas para preencher um nível. Requisito sem evidência suficiente permanece na seção de lacunas.
7. Registrar requisitos da spec não cobertos por nenhum item e itens sem origem rastreável.

## Arquitetura de skills

O fluxo canônico será acíclico:

```text
generating-azure-boards-backlog-from-spec
  -> refining-user-stories-with-3c
       -> refining-user-stories-with-3w
       -> Conversation
       -> refining-user-stories-with-gherkin
```

Contratos de retorno:

- 3W é uma skill-folha: retorna apenas mapa 3W, história/rascunho e estado `Completo` ou `Incompleto`; nunca chama 3C ou Gherkin.
- 3C recebe o retorno da 3W, registra Conversation, chama Gherkin quando houver regras confirmadas e emite a única prontidão geral `Pronta` ou `Não pronta`.
- Gherkin é uma skill-folha: consome a história e as decisões fornecidas, sem chamar 3W ou 3C, e retorna apenas estado da Confirmation e exemplos.
- Pedidos que combinam Card, Conversation e Confirmation são responsabilidade da 3C; as skills-folha não redirecionam entre si.
- A quarta skill consome a saída final da 3C por história e não recalcula os gates.

## Contrato do documento Markdown

```markdown
# Backlog para Azure Boards

## Metadados e cobertura
- Spec de origem: ...
- Escopo analisado: ...
- Itens não cobertos: ...

## 1.0.0 [Epic] Título do épico

### Description
Objetivo, valor, escopo e referências à spec.

### 1.1.0 [Feature] Título da feature

#### Parent
`1.0.0`

#### Description
Capacidade, resultado, limites de escopo e referências à spec.

#### 1.1.1 [User Story] Título da história

##### Parent
`1.1.0`

##### Description
Card 3W e síntese da Conversation produzidos pela 3C.

##### Acceptance Criteria
Regras confirmadas e Gherkin produzidos pela Confirmation.

##### Refinement Status
- Card: Estruturado | Incompleto
- Conversation: Pendente | Em andamento | Suficiente para o escopo
- Confirmation: Ausente | Parcial | Completa
- Prontidão: Pronta | Não pronta
- Origem na spec: seção/âncora/localização disponível
```

O bloco `Refinement Status` é metadado do documento de preparação e não integra automaticamente os campos do Azure Boards. Para uma história sem Confirmation, `Acceptance Criteria` fica sem conteúdo; o motivo permanece em `Description` e em `Refinement Status`.

## Conteúdo por tipo de work item

### Épico

- Título orientado ao objetivo ou iniciativa.
- `Description`: problema/oportunidade, resultado esperado, escopo e origem na spec.
- Não recebe critérios Gherkin de histórias agregadas.

### Feature

- Título orientado à capacidade entregue.
- `Description`: capacidade, valor, fronteiras e origem na spec.
- Não duplica as histórias filhas nem seus critérios.

### História de Usuário

- Título curto que diferencia o resultado.
- `Description`: Card e Conversation conforme o contrato da 3C.
- `Acceptance Criteria`: somente Confirmation acordada em Gherkin.
- Lacunas mantêm a história `Não pronta`; não impedem sua presença no backlog quando a demanda é rastreável.

## Formato Azure Boards

O documento é Markdown para revisão humana. Na inserção posterior:

- `Description` corresponde a `System.Description`.
- `Acceptance Criteria` corresponde a `Microsoft.VSTS.Common.AcceptanceCriteria`.
- Como ambos são campos HTML, uma etapa posterior de importação deve converter o conteúdo preservando títulos, listas e blocos Gherkin.
- A geração do Markdown não autoriza mutação externa.

## Validação determinística

A skill incluirá `scripts/validate_backlog.py`, executado com `uv run`, para verificar somente invariantes estruturais:

- chaves únicas e no formato correto;
- sequência e relação pai-filho;
- presença de `Description` em Épicos, Features e histórias;
- presença do cabeçalho `Acceptance Criteria` em histórias;
- presença de `Refinement Status` e origem na spec;
- ausência de conteúdo confirmatório em `Acceptance Criteria` quando o status for `Confirmation: Ausente`.

O script não decidirá se a decomposição, o valor de negócio ou os cenários estão semanticamente corretos; essas decisões permanecem nas skills.

## Tratamento de lacunas e conflitos

- Informação explícita na spec é evidência, não necessariamente decisão confirmada; respeitar o status indicado pela própria fonte.
- Conflitos são registrados com ambas as fontes e encaminhados à Conversation.
- Ausência de ator, valor ou regra não é preenchida por plausibilidade.
- Uma história pode aparecer como `Não pronta`, com `Acceptance Criteria` vazio, quando há demanda rastreável mas faltam decisões.
- Conteúdo sem pai justificável entra em `Itens não cobertos`, não em uma hierarquia artificial.

## Arquivos previstos

```text
generating-azure-boards-backlog-from-spec/
├── SKILL.md
├── agents/openai.yaml
├── references/backlog-markdown-contract.md
└── scripts/validate_backlog.py
```

Também serão atualizados:

- `refining-user-stories-with-3w/SKILL.md` para remover chamadas a outras skills e retornar apenas o artefato 3W local;
- `refining-user-stories-with-gherkin/SKILL.md` para remover a chamada à 3W e retornar apenas o estado local da Confirmation;
- `refining-user-stories-with-3c/SKILL.md` para ser a única dona da prontidão geral e oferecer saída consumível pela quarta skill.

## Estratégia de testes

1. RED comportamental sem a quarta skill: fornecer uma spec com dois objetivos, regras incompletas e requisitos técnicos misturados; observar achatamento da hierarquia, numeração inconsistente, perda de rastreabilidade ou critérios fabricados.
2. RED do validador: criar fixtures inválidas para chave duplicada, pai inexistente e Confirmation ausente com critérios preenchidos.
3. GREEN: implementar instruções mínimas, contrato Markdown e validador.
4. REFACTOR: repetir o cenário original e uma variação com histórias prontas e não prontas no mesmo backlog.
5. Executar `quick_validate.py` nas quatro skills e os testes do validador.

## Critérios de conclusão

- As quatro skills têm dependências acíclicas e papéis não sobrepostos.
- O Markdown segue `E.0.0`, `E.F.0`, `E.F.S` e explicita os pais.
- Cada história contém os dois cabeçalhos de campo do Azure Boards.
- `Description` contém Card e Conversation; `Acceptance Criteria` contém somente Confirmation.
- Itens e regras são rastreáveis à spec.
- Histórias incompletas não recebem Gherkin fabricado.
- O validador detecta violações estruturais previstas.
- Nenhuma operação é executada no Azure Boards.

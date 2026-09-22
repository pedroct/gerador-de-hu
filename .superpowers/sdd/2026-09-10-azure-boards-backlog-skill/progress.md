# SDD ledger — plan: docs/superpowers/plans/2026-09-10-azure-boards-backlog-skill.md

## Preflight

Ruling: executar no workspace atual sem Git — o workspace não é repositório e o plano proíbe inicializá-lo; usar snapshots e diffs de filesystem para revisão — se estiver errado, não haverá commits locais para rollback e a reversão dependerá dos snapshots durante a sessão.

Ruling: preservar este ledger ao final — sem histórico Git, ele é o único registro durável das decisões e revisões — se estiver errado, ficará um artefato operacional adicional em `.superpowers/sdd/`.

| Escopo | Produz / consome | Resultado do preflight |
|---|---|---|
| Task 1 | Baseline comportamental que orienta a Task 3 | Coerente; resultado deve permanecer em relatório, sem artefato de produto. |
| Task 2 | Validador, testes e fixture consumidos por Tasks 3, 5 e 6 | Coerente; TDD RED/GREEN explícito. |
| Task 3 | Skill e contrato consumidos por Tasks 4, 5 e 6 | Coerente; o design aprovado é a autoridade para o conteúdo resumido do contrato. |
| Task 4 | Contratos acíclicos das quatro skills consumidos por Tasks 5 e 6 | Coerente; altera a skill da Task 3 e as três skills existentes após o teste RED. |
| Task 5 | Evidência comportamental das integrações produzidas em Tasks 2–4 | Coerente; não persiste backlog gerado como produto. |
| Task 6 | Verificação agregada de Tasks 2–5 | Coerente; contagem esperada de 22 testes corresponde a 14 do validador e 8 de integração. |
| Tasks 1 → 3 | Falhas observadas → instruções mínimas da quarta skill | Interface compatível. |
| Tasks 1 → 5 | Mesmo cenário RED → GREEN comportamental | Interface compatível. |
| Tasks 2 → 3 | CLI do validador → workflow da nova skill | Interface compatível. |
| Tasks 2 → 6 | Testes/fixture → verificação final | Interface compatível. |
| Tasks 3 ↔ 4 | `SKILL.md` da quarta skill → teste do DAG | Compartilhamento intencional e ordenado. |
| Tasks 3 → 5 | Skill/contrato → cenários comportamentais | Interface compatível. |
| Tasks 3 → 6 | Pacote da skill → quick validation | Interface compatível. |
| Tasks 4 → 5 | DAG acíclico → uso comportamental das quatro skills | Interface compatível. |
| Tasks 4 → 6 | Teste estático e skills ajustadas → suíte final | Interface compatível. |

Ruling: no validador, detectar somente itens reconhecíveis pelo contrato e as invariantes explicitamente previstas; a revisão semântica continua nas skills — ampliar o parser para lint genérico de Markdown ultrapassaria o design — se estiver errado, títulos severamente malformados podem exigir revisão humana em vez de erro automático específico.

## Progress

Task 1: Ruling: o brief original combinou leitura do design com exigência de contexto fresco — separar geração cega e avaliação informada, pois o design aprovado exige um RED comportamental sem a quarta skill — se estiver errado, a rodada adicional apenas aumenta o custo do teste sem mudar o produto.

Task 1: fix round 1/5 iniciado — finding aberto: baseline contaminado pelo design futuro.

Task 1: fix round 1/5 (1 addressed, 0 open — baseline cego separado da avaliação; commits não aplicáveis).

Task 1: complete (sem commits, review clean).

Task 2: Ruling: ampliar o parser além do regex literal do plano para rejeitar documento sem itens e headings reconhecíveis malformados — a spec exige chaves no formato correto e o código prescrito não cobria entradas descartadas — se estiver errado, o validador será ligeiramente mais estrito que o exemplo do plano.

Task 2: Ruling: exigir conteúdo não vazio após `Origem na spec:` — a rastreabilidade obrigatória exige localização, não apenas o rótulo — se estiver errado, documentos com marcador propositalmente vazio deixarão de validar.

Task 2: Ruling: aceitar aumento da contagem de testes causado pelas regressões — evidência dos findings tem precedência sobre a estimativa de 13 testes do plano — se estiver errado, somente a contagem esperada da verificação final precisará ser atualizada.

Task 2: minor (deferred): remover dois arquivos `__pycache__/*.pyc` gerados durante os testes antes da verificação final.

Task 2: fix round 1/5 iniciado — findings abertos: documentos sem itens/headings malformados aceitos; origem vazia aceita.

Task 2: fix round 1/5 (2 addressed, 0 open — validação de headings/itens e origem efetiva; commits não aplicáveis).

Task 2: complete (sem commits, review clean; 14 testes focados).

Task 3: Ruling: reforçar a proibição de propostas e hipóteses não confirmadas como itens ou regras, sem condicioná-la à existência de evidência de demanda — a especificação aprovada é inequívoca — se estiver errado, poderá haver menos itens candidatos no backlog de revisão.

Task 3: Ruling: definir `Acceptance Criteria` como vazio sem Confirmation completa e, quando preenchido, como apenas blocos Gherkin retornados pela 3C — o mapeamento Azure e o contrato aprovado exigem essa separação — se estiver errado, regras narrativas confirmadas fora de Gherkin ficarão apenas em Description/Conversation.

Task 3: Ruling: tornar o contrato explícito sobre pai existente/tipo compatível, estados únicos da 3C e representação de itens não cobertos — o validador já apoia parte dessas garantias e o contrato precisa ser executável por si — se estiver errado, o contrato ficará mais prescritivo do que o mínimo planejado.

Task 3: fix round 1/5 iniciado — findings abertos: proposta não confirmada pode virar item; AC aceita conteúdo não-Gherkin/placeholder; contrato incompleto para Parent/estados/itens não cobertos.

Task 3: fix round 1/5 (3 addressed, 1 open — headings Card/Conversation quebram a hierarquia Markdown; commits não aplicáveis).

Task 3: fix round 2/5 iniciado — finding aberto: `### Card` e `### Conversation` precisam ser filhos de `##### Description`.

Task 3: fix round 2/5 (1 addressed, 0 open — Card e Conversation ajustados para nível `######`; commits não aplicáveis).

Task 3: complete (sem commits, review clean).

Task 4: Ruling: remover `Possíveis divisões` como saída independente da 3W e incorporar apenas perguntas de divisão no estado/local de perguntas — o contrato de skill-folha aprovado limita o retorno a 3W, história/rascunho, perguntas e estado — se estiver errado, uma sugestão de divisão ficará menos visível.

Task 4: Ruling: exigir que a 3C encaminhe à Gherkin a história/Card, fatos e decisões da Conversation, além das regras decididas — Gherkin precisa desse contexto para detectar lacunas sem chamar outra skill — se estiver errado, a interface ficará mais detalhada que o mínimo inicial.

Task 4: Ruling: ampliar o teste estático para proibir referências de chamada nas folhas e confirmar ausência de prontidão geral/estados locais da Confirmation — o teste por uma única literal não protege o DAG e o contrato que o plano exige — se estiver errado, a suíte final terá testes adicionais.

Task 4: fix round 1/5 iniciado — findings abertos: retorno 3W contraditório; payload 3C→Gherkin ambíguo; teste de integração frágil.

Task 4: fix round 1/5 (3 addressed, 0 open — contratos de folha/payload e teste de integração reforçados; commits pendentes).

Task 4: complete (review clean; 22 testes no discovery com `-s tests`).

Task 5: Ruling: executar cenário adicional em agente novo e registrar payload bruto 3C antes da renderização — a evidência atual não demonstra `Confirmation: Parcial`, não prova transcrição sem recálculo e não explicita o contexto fresco — se estiver errado, o relatório ficará mais extenso sem alterar o produto.

Task 5: fix round 1/5 iniciado — findings abertos: ausência de caso Parcial; ausência de comparação 3C/backlog; contexto fresco não evidenciado.

Task 5: fix round 1/5 (3 addressed, 0 open — caso Parcial, comparação de estados e contexto novo documentados; commits não aplicáveis).

Task 5: complete (review clean; nenhum arquivo de produto alterado).

Ruling: atualizar as expectativas numéricas do plano para 14 testes do validador, 8 de integração e 22 no discovery — regressões aprovadas pelos revisores ampliaram a cobertura — se estiver errado, somente a documentação do plano estará superestimada.

Task 6: complete (verificação final aprovada; 22 testes, 4 skills válidas, CLI válida).

Final review: 4 findings importantes corrigidos e re-revisados; nenhum finding aberto ou parked.

Ruling: manter `.superpowers` e caches `.pyc` fora do commit via `.gitignore`, preservando os relatórios localmente — são artefatos operacionais, não produto — se estiver errado, os relatórios não estarão no histórico Git, mas continuam disponíveis neste workspace.

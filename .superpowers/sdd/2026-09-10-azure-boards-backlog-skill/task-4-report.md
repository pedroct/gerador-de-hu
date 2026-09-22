# Task 4 — integração estritamente acíclica

Data: 2026-09-10

## Status

Implementação concluída sem commit. A integração agora forma o grafo `generating-azure-boards-backlog-from-spec → refining-user-stories-with-3c → {refining-user-stories-with-3w, refining-user-stories-with-gherkin}`. 3W e Gherkin são folhas e emitem apenas estados locais; 3C é a única dona da prontidão geral.

## Escopo realizado

- Adicionado o teste estático de integração prescrito pelo brief.
- Removida da 3W a chamada direta a Gherkin e a emissão de prontidão geral.
- Definido na 3W o contrato de skill-folha, com Card/artefatos 3W e estado 3W retornados ao chamador.
- Removida de Gherkin a chamada obrigatória a 3W e o veredito de prontidão geral.
- Definido em Gherkin o contrato de skill-folha, com regras, exemplos e estado local da Confirmation.
- Mantidas na 3C as chamadas obrigatórias a 3W e Gherkin.
- Declarada na 3C a propriedade exclusiva da prontidão geral e o caráter apenas local dos estados das folhas.

## Arquivos

Criado:

- `generating-azure-boards-backlog-from-spec/tests/test_skill_integration.py`

Modificados:

- `refining-user-stories-with-3w/SKILL.md`
- `refining-user-stories-with-gherkin/SKILL.md`
- `refining-user-stories-with-3c/SKILL.md`

Não modificados, conforme restrição do brief:

- `generating-azure-boards-backlog-from-spec/scripts/validate_backlog.py`
- `generating-azure-boards-backlog-from-spec/references/backlog-markdown-contract.md`
- `generating-azure-boards-backlog-from-spec/SKILL.md`

## Evidência RED

Comando executado após criar somente o teste:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest tests/test_skill_integration.py -v
```

Resultado: exit code 1; 3 testes executados; 2 falhas.

- `test_leaf_skills_do_not_require_subskills`: falhou porque 3W ainda continha `REQUIRED SUB-SKILL`.
- `test_three_c_is_the_refinement_orchestrator`: falhou porque 3C ainda não continha `única prontidão geral`.
- `test_backlog_calls_only_three_c`: já passou, confirmando o contrato existente da quarta skill.

As falhas foram causadas pelas arestas cíclicas e pela propriedade de prontidão ainda não explicitada, não por erro de importação ou de infraestrutura.

## Evidência GREEN

Após a edição das três skills, a primeira execução focal deixou 1 falha: o texto contratual exato do brief, `A 3C é a única dona da prontidão geral`, não contém literalmente a substring testada `única prontidão geral`. A frase do contrato foi preservada e foi explicitado, na mesma regra, que a única prontidão geral é a consolidada pela 3C.

Comando focal final:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest tests/test_skill_integration.py -v
```

Resultado: exit code 0; 3 testes executados; `OK`.

Discovery completo:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest discover -s tests -v
```

Resultado: exit code 0; 17 testes executados; `OK` — 14 testes do validador e 3 testes de integração.

O comando `uv run python -m unittest discover -v`, sem `-s tests`, foi testado e retornou exit code 5 com `Ran 0 tests`: neste layout, `tests` não é pacote e o discovery padrão não desce nela. O `-s tests` é necessário para o discovery completo e reproduzível.

## Validação das skills

O `quick_validate.py` não tem bit executável e o ambiente do repositório não traz `PyYAML`. Sem alterar permissões ou dependências do projeto, foi executado de forma efêmera:

```bash
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py refining-user-stories-with-3w
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py refining-user-stories-with-gherkin
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py refining-user-stories-with-3c
```

Resultado: exit code 0; `Skill is valid!` para as três skills.

## Auto-revisão

- O teste foi criado antes das mudanças nas skills e observado falhando pelo motivo esperado.
- 3W e Gherkin não contêm `REQUIRED SUB-SKILL`.
- 3C contém exatamente as duas dependências obrigatórias esperadas: 3W para Card e Gherkin para Confirmation.
- A skill de backlog contém somente a dependência obrigatória a 3C e continua instruindo o consumo sem recalcular 3W, Conversation, Confirmation ou prontidão.
- Os estados `Completo/Incompleto` da 3W e `Ausente/Parcial/Completa` de Gherkin permanecem locais; somente 3C emite `Pronta/Não pronta` implicitamente pelo gate geral existente.
- `git diff --check` não encontrou erros de whitespace.
- Nenhum arquivo fora do escopo funcional foi alterado, além deste relatório exigido.
- O teste estático é intencionalmente acoplado às strings do contrato porque esse formato e essas strings foram exigidos pelo brief, apesar da preferência geral por testes comportamentais para skills.

## Preocupações e observações

- Para executar todos os testes por discovery neste layout, deve-se usar `-s tests`; o comando sem start directory reporta zero testes.
- Há uma pequena redundância semântica necessária entre a frase contratual prescrita e a substring literal exigida pelo teste de prontidão; a redação foi mantida legível e inequívoca.
- Não foi necessário alterar o validador, o contrato Markdown da quarta skill nem a skill de backlog.
- Nenhum commit foi criado, conforme instrução do controller.

## Fix round 1

### Mudanças

- A 3W deixou de expor `Possíveis divisões` como saída independente. Uma hipótese de divisão agora é registrada nas perguntas priorizadas e depende de confirmação.
- O limite da 3W agora usa a formulação solicitada: `Quando for invocada por outra skill, devolva esses artefatos ao chamador`.
- O exemplo da 3W não menciona produzir ou encaminhar Gherkin.
- A 3C agora encaminha à Gherkin a história ou Card, os fatos e as decisões registradas na Conversation, incluindo as regras decididas.
- Gherkin declara o consumo desse payload, aponta lacunas e permanece proibida de chamar outra skill.
- Os testes de integração passaram de 3 para 8 casos. Além dos marcadores obrigatórios, verificam chamadas nomeadas com verbos de invocação, os limites de prontidão, os estados locais da Confirmation, o payload 3C→Gherkin, as saídas exclusivas da 3W e a ausência de chamadas diretas do backlog às folhas.

### RED

Após modificar somente `tests/test_skill_integration.py`:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest tests/test_skill_integration.py -v
```

Resultado: exit code 1; 8 testes executados; 3 falhas esperadas.

- `test_three_w_returns_only_its_leaf_outputs`: encontrou `Possíveis divisões` e a formulação antiga do retorno ao chamador.
- `test_three_c_passes_complete_payload_to_gherkin`: o payload completo ainda não estava declarado na 3C.
- `test_gherkin_consumes_payload_without_calling_another_skill`: Gherkin ainda declarava apenas história, fatos e decisões genéricos.

### GREEN

Teste focal após as mudanças e após o reforço final da garantia do backlog:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest tests/test_skill_integration.py -v
```

Resultado: exit code 0; 8 testes executados; `OK`.

Discovery completo:

```bash
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest discover -s tests -v
```

Resultado: exit code 0; 22 testes executados; `OK` — 14 testes do validador e 8 testes de integração.

Validação estrutural:

```bash
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py refining-user-stories-with-3w
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py refining-user-stories-with-gherkin
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py refining-user-stories-with-3c
```

Resultado: exit code 0; `Skill is valid!` para cada uma das três skills.

### Auto-revisão do round

- `git diff --check`: exit code 0, sem erros de whitespace.
- 3W e Gherkin continuam sem `REQUIRED SUB-SKILL` e sem instruções de chamada que nomeiem as demais skills.
- A 3W entrega somente mapa, história/rascunho, perguntas e estado 3W; divisões aparecem apenas como hipótese dentro das perguntas.
- Gherkin declara os estados locais `Ausente`, `Parcial` e `Completa` e não emite prontidão geral.
- A 3C preserva exatamente suas duas sub-skills e é a única dona da prontidão geral.
- A skill de backlog continua chamando apenas 3C, inclusive contra instruções de chamada sem o marcador formal.
- O validador, o contrato Markdown e a skill de backlog não foram alterados.
- Nenhum commit foi criado.

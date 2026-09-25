# Relatório — Tarefa 3: O gerador de backlog ganha o atalho por pasta

## O que foi implementado

1. **`gerar-backlog-azure-boards/SKILL.md`** (Workflow, passo 2): a busca pelos documentos
   companheiros (`Spec: Telas UX-UI`, débitos técnicos, revisão de textos) agora tenta primeiro o
   atalho por pasta — se a spec está em `DN-<id>-<slug>/`, procura ali pelo vocabulário fechado
   `telas-ux-ui.md`, `debitos-tecnicos.md` e `revisao-textos.md`. Fora desse caso, cai na busca por
   título, explicitamente marcada como **fallback permanente**, não etapa de transição — é o que
   mantém funcionando toda spec escrita antes da convenção de pastas.

2. **`gerar-backlog-azure-boards/references/backlog-markdown-contract.md`** (fim da linha 169, campo
   `Demanda de Negócio de origem`): o contrato agora proíbe nominalmente o nome da pasta como fonte do
   ID (`Isso inclui **o nome da pasta**...`), explicando o cenário de risco — pasta renomeada à mão,
   copiada de outra Demanda ou criada por engano produziria backlog publicado sob a Demanda errada.

3. **`README.md`** (bullet `Drafting a partir de Demanda no Azure Boards`): acrescentado ao fim da
   frase, antes do ponto final, que a orquestradora "grava tudo numa pasta `DN-<id>-<slug>/` sob
   `docs/specs/`, com nomes de arquivo de vocabulário fechado". Nenhum bullet novo foi criado — a
   contagem de capacidades em "O fluxo combina dez capacidades" permanece consistente
   (`test_readme_conta_capacidades_de_acordo_com_a_propria_lista` continua passando).

4. **`gerar-backlog-azure-boards/tests/test_skill_integration.py`**: dois métodos novos na classe
   `SkillIntegrationTests` (o arquivo é `unittest.TestCase`, não módulo com `SKILL`/`CONTRATO` como o
   brief sugeria — usei os atributos já carregados em `setUpClass`, conforme a decisão dada no
   prompt):
   - `test_atalho_por_pasta_nao_substitui_a_busca_por_titulo` — usa `self.backlog`.
   - `test_contrato_proibe_o_nome_da_pasta_como_fonte_do_id` — usa `self.backlog_contract`.

   Os literais das asserções são verbatim do brief. A docstring do segundo teste precisou ser
   quebrada em duas linhas (resumo + corpo, no mesmo estilo já usado por
   `test_backlog_carrega_a_demanda_de_origem_nos_metadados` no mesmo arquivo) porque a linha única
   tinha 105 caracteres e o hook `ruff-check` do projeto limita a 100 (`E501`). O texto da docstring
   em si não foi alterado, só reparticionado na quebra de linha (`distância,` termina a primeira
   linha, `e ele parece uma resposta.` continua na segunda) — nenhuma palavra foi trocada.

## O que foi testado e resultados

- Testes focados (`gerar-backlog-azure-boards/tests -k "atalho_por_pasta or proibe_o_nome"`): 2 PASS.
- Suíte completa do módulo `gerar-backlog-azure-boards/tests`: 57 passed, 2 subtests passed.
- Suíte inteira do repositório (`uv run pytest -q`, Passo 6 do brief): 301 passed, 109 subtests
  passed. Saída limpa, sem warnings.

## Evidência de TDD

### RED

Comando:
```
uv run pytest gerar-backlog-azure-boards/tests -v -k "atalho_por_pasta or proibe_o_nome"
```

Saída relevante:
```
gerar-backlog-azure-boards/tests/test_skill_integration.py::SkillIntegrationTests::test_atalho_por_pasta_nao_substitui_a_busca_por_titulo FAILED [ 50%]
gerar-backlog-azure-boards/tests/test_skill_integration.py::SkillIntegrationTests::test_contrato_proibe_o_nome_da_pasta_como_fonte_do_id FAILED [100%]

=================================== FAILURES ===================================
_ SkillIntegrationTests.test_atalho_por_pasta_nao_substitui_a_busca_por_titulo _
>       self.assertIn("DN-<id>-<slug>", self.backlog)
E       AssertionError: 'DN-<id>-<slug>' not found in '---\nname: gerar-backlog-azure-boards\n...'
gerar-backlog-azure-boards/tests/test_skill_integration.py:250: AssertionError
_ SkillIntegrationTests.test_contrato_proibe_o_nome_da_pasta_como_fonte_do_id __
>       self.assertIn("nome da pasta", self.backlog_contract)
E       AssertionError: 'nome da pasta' not found in '# Contrato do backlog Markdown...'
gerar-backlog-azure-boards/tests/test_skill_integration.py:257: AssertionError

======================= 2 failed, 55 deselected in 0.02s =======================
```

Falha esperada: nem `SKILL.md` nem `backlog-markdown-contract.md` continham ainda o texto do atalho
por pasta, do vocabulário fechado ali aplicado, do rótulo "fallback permanente" ou da proibição
nominal do nome da pasta — todos introduzidos só nos Passos 3 e 4.

### GREEN

Comando (testes focados):
```
uv run pytest gerar-backlog-azure-boards/tests -v -k "atalho_por_pasta or proibe_o_nome"
```
Saída:
```
gerar-backlog-azure-boards/tests/test_skill_integration.py::SkillIntegrationTests::test_atalho_por_pasta_nao_substitui_a_busca_por_titulo PASSED [ 50%]
gerar-backlog-azure-boards/tests/test_skill_integration.py::SkillIntegrationTests::test_contrato_proibe_o_nome_da_pasta_como_fonte_do_id PASSED [100%]

======================= 2 passed, 55 deselected in 0.01s =======================
```

Comando (suíte inteira, Passo 6 do brief):
```
uv run pytest -q
```
Saída:
```
...................................................................... [ 23%]
............................................................................................. [ 54%]
........................................................................ [ 78%]
..................................................................       [100%]
301 passed, 109 subtests passed in 0.33s
```

## Arquivos alterados

- `gerar-backlog-azure-boards/SKILL.md`
- `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`
- `README.md`
- `gerar-backlog-azure-boards/tests/test_skill_integration.py`

Commit: `ef597b5` — "feat: gerador de backlog acha companheiros pela pasta da Demanda"
(`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`, mensagem idêntica à do brief). Apenas
`gerar-backlog-azure-boards` e `README.md` foram adicionados ao stage; `.superpowers/sdd/` ficou de
fora, como instruído.

## Achados da auto-revisão

- O commit inicial (com a mensagem exata do brief) foi rejeitado pelo hook `pre-commit` na etapa
  `ruff-check` por causa da linha longa (105 > 100) na docstring do segundo teste novo. Corrigi
  quebrando a docstring em duas linhas (mesmo padrão já usado alhures no arquivo), sem alterar
  nenhuma palavra do texto, e recommitei com a mesma mensagem. Isso é uma adaptação mecânica exigida
  pelo linter do projeto, não uma mudança de requisito — os literais das asserções (`assertIn`)
  permanecem verbatim do brief.
- Revisei o diff completo (`git diff` antes do commit): as quatro mudanças batem exatamente com os
  Passos 3, 4, 5 e 1 do brief, sem nenhuma alteração fora do escopo pedido.
- Conferi manualmente que nenhum bullet novo foi criado no README e que a contagem de capacidades
  ("dez capacidades") continua batendo com a lista — o teste correspondente já estava verde antes e
  depois.

## Problemas ou preocupações

Nenhum. Status: DONE.

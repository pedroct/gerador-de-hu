# Relatório — Tarefa 7: A entrevista ganha escopo de audiência

## O que foi implementado

Em `entrevistar-lacunas-requisito/SKILL.md`:

1. **Frontmatter `description`**: acrescentada a frase `Aceita um escopo de audiência para separar
   o refinamento de negócio do técnico.` ao final da descrição existente, exatamente como o brief
   especifica.
2. **`## Objetivo`**: a frase `tipicamente produzida por \`redigir-spec-pedido-negocio\`` virou
   `tipicamente produzida por \`redigir-spec-demanda-azure-boards\` ou \`redigir-spec-pedido-negocio\``,
   citando as duas skills de origem possíveis.
3. **Passo 1 do `## Fluxo`**: acrescentado o reconhecimento do formato rotulado
   `- **N3 · Negócio** — <pergunta>` (letra do ID + rótulo indicam audiência) e a regra explícita de
   que spec sem rótulos de audiência é o caso normal de specs antigas — pergunta-se tudo, como antes
   — e que o escopo é filtro opcional, nunca requisito de formato.
4. **Passo 2 do `## Fluxo`**: acrescentada a regra de composição do escopo com a fronteira: uma
   lacuna `Técnico` que depende de uma `Negócio` ainda aberta fica fora da fronteira mesmo na rodada
   técnica; o bloqueio deve ser relatado, não forçado. Também documentado que na rodada de escopo
   `negócio` o material de leitura é `negocio.md`, mas as decisões são sempre gravadas em `spec.md`.
5. **Passo 4 do `## Fluxo`**: acrescentado um terceiro desfecho de resposta — quando ela cria uma
   decisão que gera uma lacuna nova, essa lacuna é registrada em `## Lacunas e perguntas abertas` com
   ID e audiência próprios, citando a lacuna que a originou, com o exemplo do brief
   ("a diligência deve expirar sozinha" → "como a rotina de expiração é disparada").
6. **`## Boundaries`**: acrescentado o limite contra reclassificar a audiência de uma lacuna
   existente para encaixá-la na rodada atual — se o rótulo estiver errado, avisar o usuário e seguir
   sem perguntá-la.

Em `entrevistar-lacunas-requisito/tests/test_skill_integration.py`:

- Acrescentada a função de módulo `sem_quebras()`, copiada de
  `redigir-spec-demanda-azure-boards/tests/test_skill_integration.py:142-144`.
- Acrescentados os 5 testes do Passo 1 do brief, convertidos para métodos de
  `InterviewingSkillIsolationTests` usando `self.interviewing` e `self.assertIn`/`self.assertTrue`
  no lugar de `SKILL`/`assert` de nível de módulo — decisão já resolvida na tarefa recebida. Nomes e
  docstrings mantidos verbatim: `test_escopo_filtra_por_audiencia`,
  `test_escopo_compoe_com_a_fronteira_em_vez_de_substitui_la`, `test_spec_sem_rotulos_pergunta_tudo`,
  `test_resposta_pode_criar_lacuna_nova`, `test_description_nao_fixa_uma_unica_skill_de_origem` (esse
  último com `SKILL[: SKILL.index("---", 4)]` convertido para
  `self.interviewing[: self.interviewing.index("---", 4)]`, conforme instruído).

Nenhum teste pré-existente foi alterado.

## Evidência de TDD

**RED** — comando rodado antes da implementação (só com os testes novos já escritos):

```bash
uv run pytest entrevistar-lacunas-requisito/tests -v
```

Saída (5 falhas, exatamente como o Passo 2 do brief previa; 9 testes pré-existentes passaram):

```
FAILED .../test_skill_integration.py::...test_description_nao_fixa_uma_unica_skill_de_origem
  AssertionError: False is not true
FAILED .../test_skill_integration.py::...test_escopo_compoe_com_a_fronteira_em_vez_de_substitui_la
  AssertionError: 'compõe com a fronteira' not found in '...'
FAILED .../test_skill_integration.py::...test_escopo_filtra_por_audiencia
  AssertionError: 'Negócio' not found in '...'
FAILED .../test_skill_integration.py::...test_resposta_pode_criar_lacuna_nova
  AssertionError: 'registrar uma lacuna nova' not found in '...'
FAILED .../test_skill_integration.py::...test_spec_sem_rotulos_pergunta_tudo
  AssertionError: 'Spec sem rótulos de audiência' not found in '...'
5 failed, 9 passed in 0.03s
```

As falhas eram esperadas: nenhum dos textos novos (escopo, composição com a fronteira, regra da
spec sem rótulos, lacuna nova, segunda skill de origem no Objetivo) existia ainda no `SKILL.md`
antigo.

**GREEN** — depois da implementação (Passos 3, 4 e 5 do brief):

```bash
uv run pytest entrevistar-lacunas-requisito/tests -v
```

```
14 passed in 0.02s
```

**Suíte inteira (Passo 6 do brief):**

```bash
uv run pytest -q
```

```
331 passed, 109 subtests passed in 0.33s
```

## Quebras de linha movidas

1. Parágrafo do `## Objetivo` (linhas ~11–17 do arquivo final): ao inserir
   `\`redigir-spec-demanda-azure-boards\` ou` antes de `\`redigir-spec-pedido-negocio\``, o reflow
   original deixou "O mecanismo de rodada/fronteira" numa linha e "usado aqui é adaptado..." na
   seguinte, e mais adiante "da skill \`grilling\` do" separado de "repositório [...]" no meio da
   URL. Reformatei os pontos de quebra desse parágrafo (sem alterar nenhuma palavra) para manter as
   frases fluindo normalmente: `"...O mecanismo de rodada/fronteira usado aqui é adaptado, com
   atribuição MIT completa em [NOTICE.md](NOTICE.md), da skill \`grilling\` do repositório [...]"`.
   Nenhuma asserção dependia dessa frase especificamente (nem antes nem depois), mas o texto ficava
   com um corte visualmente estranho no meio de "rodada/fronteira usado" e decidi corrigir já que
   estava editando esse trecho.

Nenhuma outra quebra de linha precisou ser movida: as duas frases protegidas por `sem_quebras()`
("compõe com a fronteira" / "fica fora da fronteira" no passo 2, e "Spec sem rótulos de audiência" /
"pergunte todas as lacunas" no passo 1, e "registrar uma lacuna nova" no passo 4) já nasceram sem
quebra no meio da frase-alvo, porque escrevi essas frases-chave como uma unidade contígua ao
redigir cada parágrafo, evitando o problema encontrado na Tarefa 6.

## Lint

```bash
uv run ruff check entrevistar-lacunas-requisito
```

Na primeira rodada, `ruff` acusou `E501` (linha > 100 colunas) nas docstrings de
`test_spec_sem_rotulos_pergunta_tudo` e `test_resposta_pode_criar_lacuna_nova` (docstrings verbatim
do brief, mas longas demais numa linha só). Quebrei cada docstring em duas linhas dentro das aspas
triplas, sem alterar nenhuma palavra:

```python
"""Toda spec já escrita não tem rótulos; o escopo é filtro opcional, não requisito de
formato."""
```

```python
"""Decisão de negócio que gera trabalho técnico não pode virar descoberta na
implementação."""
```

Depois da correção:

```
All checks passed!
```

Suíte inteira re-rodada após o ajuste de lint: `331 passed, 109 subtests passed in 0.29s`.

No `git commit`, o hook `ruff-format` do pre-commit reformatou automaticamente
`test_description_nao_fixa_uma_unica_skill_de_origem` (uniu o `or (...)` em uma linha só, dentro do
limite de 100 colunas, sem alterar nenhuma lógica). Rodei a suíte de novo, re-adicionei os dois
arquivos e commitei em seguida — o commit final (`c30bb2d`) já reflete essa formatação.

## Arquivos alterados

- `entrevistar-lacunas-requisito/SKILL.md`
- `entrevistar-lacunas-requisito/tests/test_skill_integration.py`

## Achados da auto-revisão

- Reli o `git diff` completo dos dois arquivos. O texto novo do `SKILL.md` bate com o brief
  palavra por palavra (fora a reformatação de quebra de linha documentada acima, que não altera
  nenhuma palavra).
- Verifiquei que a regra "spec sem rótulos pergunta tudo" está no passo 1 (onde a spec é lida e
  mapeada), coerente com o resto do fluxo — não duplica nem contradiz a regra de composição do
  escopo do passo 2.
- Verifiquei que o terceiro desfecho do passo 4 (lacuna nova) não colide com os dois desfechos
  existentes (decisão registrada / adiamento explícito): os três são mutuamente exclusivos por
  resposta, unidos por "ou".
- Conferi que nenhuma asserção nova já passaria contra o `SKILL.md` antigo — todas as 5 falharam no
  RED antes da implementação, confirmando que pinam o texto novo.
- Conferi que os 9 testes pré-existentes continuam passando sem alteração — não precisei tocar em
  nenhum teste fora dos 5 listados no brief.
- `test_description_nao_fixa_uma_unica_skill_de_origem` merece nota: a condição
  `"redigir-spec-demanda-azure-boards" in frontmatter` é falsa (a segunda skill de origem só aparece
  no `## Objetivo`, não no frontmatter), então o teste passa pelo segundo ramo do `or` — a frase
  fixa antiga `"tipicamente produzida por \`redigir-spec-pedido-negocio\`"` (sem a segunda skill)
  não existe mais no texto, porque agora há um `ou` entre as duas. Confirmei isso lendo o texto
  final: a substring exata do teste antigo não ocorre mais, só a versão com as duas skills.
- Nenhuma linha do `## Escopo` foi tocada (fora do escopo da tarefa) — mantém a menção isolada a
  `redigir-spec-pedido-negocio` como origem da investigação de código-fonte, o que é consistente:
  a Tarefa 5/6 trabalham só em `redigir-spec-demanda-azure-boards`, e este trecho específico do
  `## Escopo` fala de investigação de código, que é exclusiva daquela skill original — não fazia
  parte do que o brief pediu para alterar.

## Problemas ou preocupações

Nenhum. O arquivo `SKILL.md` permanece de tamanho razoável (80 linhas) e a estrutura do fluxo
continua legível após as três inserções.

## Relatório de correção — Achado 1 (revisão pós-implementação)

**Achado:** `test_escopo_filtra_por_audiencia` continha `self.assertIn("escopo", self.interviewing)`,
literal copiado do brief. A palavra "escopo" (minúscula) já existia no `SKILL.md` antes da Tarefa 7,
na frase pré-existente "...para um escopo mais estreito, não traduzido literalmente." — essa
asserção passaria contra o arquivo anterior à minha mudança e não pinava nada específico da Tarefa 7.
As duas asserções seguintes do mesmo método (`"Negócio"`, `"Técnico"`) já pinavam corretamente.

**Decisão do controlador:** substituir o literal por `"escopo de audiência"`, que é específico do
texto novo (aparece na `description` do frontmatter: "Aceita um escopo de audiência para separar o
refinamento de negócio do técnico.").

**Correção aplicada** em
`entrevistar-lacunas-requisito/tests/test_skill_integration.py:107`:

```diff
-        self.assertIn("escopo", self.interviewing)
+        self.assertIn("escopo de audiência", self.interviewing)
```

**Comprovação pedida pelo controlador** — a string nova não existe na base (commit `933df99`,
antes da Tarefa 7) e existe no arquivo atual:

```bash
git show 933df99:entrevistar-lacunas-requisito/SKILL.md | grep -c 'escopo de audiência'
```
```
0
```

```bash
grep -c 'escopo de audiência' entrevistar-lacunas-requisito/SKILL.md
```
```
1
```

**Teste focado:**

```bash
uv run pytest entrevistar-lacunas-requisito/tests -v
```
```
14 passed in 0.02s
```
(`test_escopo_filtra_por_audiencia` entre eles, `PASSED`.)

**Lint:**

```bash
uv run ruff check entrevistar-lacunas-requisito
```
```
All checks passed!
```

**Suíte inteira:**

```bash
uv run pytest -q
```
```
331 passed, 109 subtests passed in 0.32s
```

**Commit:** `9f0dda3` — `fix: teste do escopo de audiencia pina a frase inteira`. Apenas
`entrevistar-lacunas-requisito/tests/test_skill_integration.py` foi adicionado (1 arquivo alterado,
1 inserção, 1 remoção).

**Outcome do achado:** fixed.

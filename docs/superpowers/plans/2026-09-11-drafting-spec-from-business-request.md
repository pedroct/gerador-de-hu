# Drafting A Spec From Business Request Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fifth, independent skill — `drafting-a-spec-from-business-request` — that turns an informal business request (email, ticket, chat) plus read-only inspection of the local application source into a spec document compatible with the existing `generating-azure-boards-backlog-from-spec` input, without touching any of the four existing skills.

**Architecture:** A single new skill directory (`SKILL.md`, `agents/openai.yaml`, `references/business-request-investigation.md`, `tests/test_skill_integration.py`) that is a pure predecessor in the skill graph — it never calls, and is never called by, the four existing skills. Its own static test enforces that isolation the same way `generating-azure-boards-backlog-from-spec/tests/test_skill_integration.py` already enforces the acyclic graph among the other four. `pyproject.toml` and `README.md` are updated (project-level files, not skill files) so the new skill is discoverable and its tests run under the existing `pytest`/`quick_validate.py` conventions.

**Tech Stack:** Prompt-only skill authoring (Markdown + YAML), Python 3.12 `unittest`/`pytest` for the static isolation test, `uv run` for execution, the repo's existing `skill-creator` (`~/.codex/skills/.system/skill-creator/scripts/init_skill.py` and `quick_validate.py`) for scaffolding and structural validation — the same tool already used to bootstrap the other four skills in this repo.

**Spec:** docs/superpowers/specs/2026-09-11-drafting-spec-from-business-request-design.md

## Global Constraints

- None of the four existing skills (`refining-user-stories-with-3w`, `refining-user-stories-with-3c`, `refining-user-stories-with-gherkin`, `generating-azure-boards-backlog-from-spec`) may be created, removed, or modified.
- Every business request is treated as a single unit of scope; the new skill never splits it into multiple items.
- The new skill takes no project-path parameter; it discovers sibling repositories from wherever it is installed.
- Code investigation is read-only; scripts, tests, builds, servers, migrations, or the application itself are never executed without explicit authorization.
- The generated spec is saved to a file and the skill stops there; it never chains automatically into backlog generation.
- SKILL.md frontmatter `description` ≤ 1024 chars, no `<`/`>`; `agents/openai.yaml` `short_description` is 25–64 chars (the skill-creator's own constraint, already followed by the other four skills).

---

### Task 1: Scaffold and author the `drafting-a-spec-from-business-request` skill

**Files:**
- Create: `drafting-a-spec-from-business-request/SKILL.md`
- Create: `drafting-a-spec-from-business-request/agents/openai.yaml`
- Create: `drafting-a-spec-from-business-request/references/business-request-investigation.md`
- Test: `drafting-a-spec-from-business-request/tests/test_skill_integration.py`

**Interfaces:**
- Consumes: nothing from other tasks (first task).
- Produces: the skill directory itself, at the fixed path `drafting-a-spec-from-business-request/`, which Task 2 references by path (for `pyproject.toml` `testpaths`) and Task 3 references by path (for `README.md` links). No code-level interface — this is a prompt-only skill; downstream tasks depend only on the directory/file paths listed above, not on any function signature.

- [ ] **Step 1: Scaffold the skill directory with the repo's existing skill-creator tool**

Run from the repo root (`/Volumes/DOCK/Projetos/pessoal/gerador-hu`):

```bash
uv run --with pyyaml python \
  /Users/pedroct/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  drafting-a-spec-from-business-request \
  --path /Volumes/DOCK/Projetos/pessoal/gerador-hu \
  --resources references \
  --interface display_name='Redigir spec a partir de pedido de negócio' \
  --interface short_description='Investiga código e redige spec a partir de pedido informal' \
  --interface default_prompt='Use $drafting-a-spec-from-business-request para transformar este pedido de negócio em uma spec antes de gerar o backlog.'
```

Expected output: `[OK] Skill 'drafting-a-spec-from-business-request' initialized successfully...`. This creates `SKILL.md` (with `[TODO: ...]` placeholders — expected, replaced in Step 4), `agents/openai.yaml` (final content, no further edits needed), and an empty `references/` directory.

- [ ] **Step 2: Write the failing test**

Create `drafting-a-spec-from-business-request/tests/test_skill_integration.py`:

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class DraftingSkillIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drafting = (
            ROOT / "drafting-a-spec-from-business-request" / "SKILL.md"
        ).read_text()
        cls.investigation = (
            ROOT
            / "drafting-a-spec-from-business-request"
            / "references"
            / "business-request-investigation.md"
        ).read_text()
        cls.three_w = (ROOT / "refining-user-stories-with-3w" / "SKILL.md").read_text()
        cls.three_c = (ROOT / "refining-user-stories-with-3c" / "SKILL.md").read_text()
        cls.gherkin = (
            ROOT / "refining-user-stories-with-gherkin" / "SKILL.md"
        ).read_text()
        cls.backlog = (
            ROOT / "generating-azure-boards-backlog-from-spec" / "SKILL.md"
        ).read_text()

    def assert_has_no_named_skill_invocation(self, text, other_skill_names):
        invocation_words = (
            r"\b(?:use|chame|chamar|invoque|invocar|encaminhe|encaminhar|"
            r"passe|execute|aplique|carregue)\b"
        )
        for line in text.splitlines():
            for skill_name in other_skill_names:
                if skill_name in line.lower():
                    self.assertNotRegex(
                        line.lower(),
                        invocation_words,
                        msg=f"drafting skill calls {skill_name!r}: {line}",
                    )

    def test_drafting_skill_does_not_call_existing_skills(self):
        self.assertNotIn("REQUIRED SUB-SKILL", self.drafting)
        self.assert_has_no_named_skill_invocation(
            self.drafting,
            (
                "refining-user-stories-with-3w",
                "refining-user-stories-with-3c",
                "refining-user-stories-with-gherkin",
                "generating-azure-boards-backlog-from-spec",
            ),
        )

    def test_existing_skills_do_not_reference_drafting_skill(self):
        for text in (self.three_w, self.three_c, self.gherkin, self.backlog):
            self.assertNotIn("drafting-a-spec-from-business-request", text)

    def test_drafting_skill_treats_request_as_single_scope(self):
        self.assertIn(
            "Trate o pedido inteiro como uma única unidade de escopo; "
            "nunca o divida em múltiplos itens.",
            self.drafting,
        )

    def test_drafting_skill_stops_after_saving_the_spec(self):
        self.assertIn(
            "Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.",
            self.drafting,
        )

    def test_drafting_skill_discovers_repos_without_a_path_argument(self):
        self.assertIn(
            "A skill não recebe caminho de projeto como parâmetro",
            self.drafting,
        )

    def test_investigation_reference_is_read_only_without_authorization(self):
        for command in ("`rg`", "`find`", "`git status`"):
            self.assertIn(command, self.investigation)
        self.assertIn(
            "Não execute scripts, testes, builds, servidores, migrações ou a aplicação",
            self.investigation,
        )
        self.assertIn("sem autorização explícita", self.investigation)

    def test_investigation_reference_separates_request_evidence_and_gaps(self):
        self.assertIn("Afirmado pelo pedido", self.investigation)
        self.assertIn("Evidenciado pelo código", self.investigation)
        self.assertIn("Lacuna", self.investigation)
        self.assertIn(
            "Código existente não cria requisito nem confirma decisão de negócio",
            self.investigation,
        )

    def test_investigation_reference_never_invents_path_or_line(self):
        self.assertIn("Nenhuma evidência encontrada", self.investigation)
        self.assertIn("Evidência indisponível:", self.investigation)
        self.assertIn("Nunca invente caminho ou linha", self.investigation)

    def test_investigation_reference_registers_divergence_without_choosing_a_side(self):
        self.assertIn(
            "Quando o pedido e o código divergirem, registre as duas leituras",
            self.investigation,
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest drafting-a-spec-from-business-request/tests/test_skill_integration.py -v`
Expected: FAIL — the placeholder `SKILL.md` from Step 1 doesn't contain any of the asserted strings, and `references/business-request-investigation.md` doesn't exist yet (`FileNotFoundError` in `setUpClass`).

- [ ] **Step 4: Write the real SKILL.md content**

Overwrite `drafting-a-spec-from-business-request/SKILL.md` completely with:

```markdown
---
name: drafting-a-spec-from-business-request
description: Use when a business request such as an email, ticket, or chat message describes a problem or demand informally, without a written spec, and the local application source code is available to ground it before backlog generation.
---

# Drafting A Spec From Business Request

## Objetivo

Transformar um pedido informal de negócio (e-mail, ticket, mensagem) em uma spec em Markdown, apoiada
em investigação somente leitura do código-fonte já presente onde esta skill está instalada. A spec
resultante é a entrada que `generating-azure-boards-backlog-from-spec` já aceita hoje; esta skill não
decompõe em Épico, Feature ou História e não gera Acceptance Criteria.

## Escopo

Trate o pedido inteiro como uma única unidade de escopo; nunca o divida em múltiplos itens. Isso vale
mesmo quando o pedido parecer pequeno demais ou incompleto.

## Fluxo

1. **Leia o pedido por completo**, preservando a formulação original ao citá-lo na spec.
2. **Descubra os repositórios candidatos.** A skill não recebe caminho de projeto como parâmetro:
   investigue a partir do diretório onde está instalada e de seus repositórios irmãos. Registre quais
   parecem relevantes ao vocabulário do pedido e quais foram descartados, com o motivo.
3. **Antes de investigar, leia e aplique**
   [references/business-request-investigation.md](references/business-request-investigation.md):
   inspeção somente leitura, formato de evidência `caminho:linha` e separação entre afirmação do
   pedido, evidência de código e lacuna.
4. **Redija a spec** no template abaixo, preenchendo cada seção só com o que foi confirmado pelo
   pedido ou evidenciado pelo código.
5. **Salve o documento em arquivo e pare. Não invoque nenhuma outra skill.** Informe ao usuário o
   caminho salvo e um resumo das lacunas e perguntas encontradas.

## Ausência de repositório relevante

Se nenhum repositório candidato tiver relação com o pedido, registre essa ausência e produza a spec
apenas com o conteúdo do pedido, equivalente ao modo Greenfield da quarta skill — sem travar a entrega
do documento.

## Template da spec

```markdown
# Spec: <título curto>

## Fonte do pedido
Texto original (citado ou anexado) e canal de origem.

## Escopo
Tratado como item único; nenhuma decomposição foi aplicada.

## Repositórios considerados
| Repositório | Relevante? | Motivo |
|---|---|---|
| [nome] | Sim/Não | [justificativa] |

## Problema relatado
Síntese fiel do que o pedido descreve, sem inferências.

## Comportamento atual (evidência no código)
| Afirmação/observação | Evidência `caminho:linha` | Confiança |
|---|---|---|
| ... | ... | Alta/Média/Baixa |

## Comportamento esperado
- Afirmado explicitamente pelo pedido: ...
- Inferido (marcado como inferência, não fato confirmado): ...

## Atores e vocabulário identificados no código
Lista de atores, entidades e termos de domínio encontrados, com evidência.

## Lacunas e perguntas abertas
Tudo que não pôde ser confirmado nem pelo pedido nem pelo código.
```

## Boundaries

- Somente leitura; não execute scripts, testes, build, servidores, migrações ou a aplicação sem
  autorização explícita.
- Nunca decomponha o pedido em múltiplos itens.
- Nunca invente ator, regra, critério de aceite ou decisão de negócio a partir do código; código
  existente não cria requisito nem confirma decisão de negócio.
- Não produza Épico, Feature, História, Description nem Acceptance Criteria; isso continua sendo
  responsabilidade de `generating-azure-boards-backlog-from-spec` e da 3C.
- Não encadeie automaticamente a geração do backlog; a spec fica pronta para uso manual do usuário.
```

Note the fenced template block is nested inside the file using four backticks conceptually — in the
actual file use a single set of triple backticks for the outer `## Template da spec` fence (as shown);
do not double-fence it.

- [ ] **Step 5: Write the investigation reference**

Create `drafting-a-spec-from-business-request/references/business-request-investigation.md`:

```markdown
# Investigação de código a partir de um pedido de negócio

Leia esta referência antes de investigar o código para redigir a spec. O objetivo é descobrir
vocabulário, atores e comportamento atual com evidência verificável — não validar um requisito que
ainda não existe.

## Descoberta de repositórios

Como a skill roda a partir do diretório onde foi instalada, trate esse diretório e seus repositórios
irmãos como universo de busca. Para cada um, registre se é relevante ao vocabulário do pedido (nomes
de entidades, telas, endpoints citados ou implícitos) e o motivo — inclusive para os descartados.

## Inspeção segura

1. Registre a raiz analisada e qualquer incerteza sobre qual repositório implementa o comportamento
   descrito no pedido.
2. Faça somente leitura segura: inventário com `rg` (incluindo `rg --files`) ou `find`, estado do
   repositório com `git status`, leitura de arquivos de código e testes e leitura de arquivos de
   configuração. Use a ferramenta menos abrangente que responda à pergunta.
3. Não execute scripts, testes, builds, servidores, migrações ou a aplicação sem autorização
   explícita. Não altere arquivos, dependências, banco de dados, serviços nem configuração como parte
   da investigação.
4. Inspecione pontos de entrada, regras de domínio, atores e vocabulário somente quando forem
   relevantes ao pedido. O nome de um arquivo, símbolo ou teste isolado não prova o comportamento
   completo.

Se nenhum repositório puder ser localizado ou lido com segurança, registre o limite e prossiga com a
spec baseada apenas no pedido; não preencha lacunas com plausibilidade.

## Três categorias de conteúdo

Separe sempre:

- **Afirmado pelo pedido**: o que o texto original declara, citado ou parafraseado fielmente.
- **Evidenciado pelo código**: cite cada evidência como caminho relativo à raiz e linha inicial, por
  exemplo `src/diligencias/reopen_service.py:42`. Registre `Nenhuma evidência encontrada` quando a
  busca relevante estiver concluída, ou `Evidência indisponível: [motivo]` quando não foi possível
  investigar. Nunca invente caminho ou linha.
- **Lacuna**: o que não pôde ser confirmado nem pelo pedido nem pelo código; permanece como pergunta
  aberta.

Código existente não cria requisito nem confirma decisão de negócio; ele só descreve o estado atual.
Propostas, hipóteses e comportamentos encontrados sem relação com o pedido ficam fora da spec.

Quando o pedido e o código divergirem, registre as duas leituras em Lacunas e perguntas abertas, sem
escolher qual prevalece — a divergência em si é a informação relevante para quem for decidir depois.

## Confiança

Qualifique cada linha de evidência com `Alta`, `Média` ou `Baixa`. Confiança descreve o quanto a
evidência sustenta a observação; não substitui a distinção entre afirmado, evidenciado e lacuna.

## Handoff

Entregue a spec com as três categorias claramente identificadas. Quem for rodar
`generating-azure-boards-backlog-from-spec` sobre esse arquivo trata "Evidenciado pelo código" como
contexto Brownfield de estado atual, nunca como confirmação de valor ou decisão de negócio.
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `uv run pytest drafting-a-spec-from-business-request/tests/test_skill_integration.py -v`
Expected: PASS — 9 tests, 0 failures.

- [ ] **Step 7: Validate the skill structure**

Run: `uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py drafting-a-spec-from-business-request`
Expected: `Skill is valid!`

- [ ] **Step 8: Commit**

```bash
git add drafting-a-spec-from-business-request/
git commit -m "$(cat <<'EOF'
feat: add drafting-a-spec-from-business-request skill

Turns an informal business request (email, ticket) plus read-only
source inspection into a spec compatible with
generating-azure-boards-backlog-from-spec, without altering any of
the four existing skills.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Wire the new skill's tests into the repo's pytest/coverage setup

**Files:**
- Modify: `pyproject.toml:47-51` (`[tool.pytest.ini_options]` `testpaths`)

**Interfaces:**
- Consumes: `drafting-a-spec-from-business-request/tests/test_skill_integration.py` from Task 1 (by path only).
- Produces: a `pytest` run from the repo root that discovers both the existing skill's tests and the new skill's tests, for Task 3's verification step to rely on.

- [ ] **Step 1: Write the failing check**

Run: `uv run pytest -v` from the repo root.
Expected (before the edit): only the 2 existing test files under
`generating-azure-boards-backlog-from-spec/tests/` run; `drafting-a-spec-from-business-request/tests/test_skill_integration.py` is NOT collected (it sits outside the configured `testpaths`), even though it passes when run directly. This confirms the wiring gap.

- [ ] **Step 2: Add the new tests directory to testpaths**

In `pyproject.toml`, find:

```toml
[tool.pytest.ini_options]
testpaths = [
  "generating-azure-boards-backlog-from-spec/tests",
]
addopts = "-ra"
```

Replace with:

```toml
[tool.pytest.ini_options]
testpaths = [
  "generating-azure-boards-backlog-from-spec/tests",
  "drafting-a-spec-from-business-request/tests",
]
addopts = "-ra"
```

- [ ] **Step 3: Run the full suite to verify it passes**

Run: `uv run pytest -v` from the repo root.
Expected: PASS — the existing tests plus the new 9 isolation/content tests all collected and green (no regressions in the four existing skills, since none of their files changed).

- [ ] **Step 4: Re-run quick_validate.py across all five skills**

Run:

```bash
for skill_dir in \
  drafting-a-spec-from-business-request \
  generating-azure-boards-backlog-from-spec \
  refining-user-stories-with-3c \
  refining-user-stories-with-3w \
  refining-user-stories-with-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```

Expected: `Skill is valid!` printed five times.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "$(cat <<'EOF'
test: discover drafting-a-spec-from-business-request tests in pytest

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Document the new skill in README.md

**Files:**
- Modify: `README.md` (three separate, non-adjacent edits — see below)

**Interfaces:**
- Consumes: the skill name and path from Task 1 (`drafting-a-spec-from-business-request/SKILL.md`), the validation-loop pattern already in the file.
- Produces: nothing consumed by later tasks — this is the last content task.

- [ ] **Step 1: Add the informal-request entry point after the existing pipeline diagram**

Find this exact block (currently lines 9–23 of `README.md`):

```markdown
```text
Spec
 └─ generating-azure-boards-backlog-from-spec
     └─ refining-user-stories-with-3c
         ├─ refining-user-stories-with-3w
         └─ refining-user-stories-with-gherkin
```

- **3W — Who, What, Why:** identifica ator, capacidade/resultado e valor, separando fatos de lacunas.
```

Insert a new paragraph and diagram immediately after the closing ` ``` ` of the pipeline diagram and before the `- **3W...` bullet list:

```markdown
Quando não existe spec escrita — só um pedido informal de negócio, como um e-mail ou ticket — a skill
`drafting-a-spec-from-business-request` investiga o código-fonte já disponível onde está instalada e
produz essa spec como um passo manual anterior:

```text
Pedido informal (e-mail, ticket) + código-fonte
 └─ drafting-a-spec-from-business-request
     └─ Spec
```
```

- [ ] **Step 2: Add a row to the "Skills disponíveis" table**

Find:

```markdown
| Skill | Use quando | Saída principal |
|---|---|---|
| [`refining-user-stories-with-3w`](refining-user-stories-with-3w/SKILL.md) | Ator, objetivo ou benefício estão vagos | Mapa 3W, história/rascunho, perguntas e estado 3W |
```

Replace with:

```markdown
| Skill | Use quando | Saída principal |
|---|---|---|
| [`drafting-a-spec-from-business-request`](drafting-a-spec-from-business-request/SKILL.md) | Só há um pedido informal de negócio (e-mail, ticket) e nenhuma spec escrita | Documento de spec em Markdown, com repositórios considerados, evidência de código e lacunas |
| [`refining-user-stories-with-3w`](refining-user-stories-with-3w/SKILL.md) | Ator, objetivo ou benefício estão vagos | Mapa 3W, história/rascunho, perguntas e estado 3W |
```

- [ ] **Step 3: Add the new skill to the validation loop and the pytest command list**

Find:

```markdown
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
```

Replace with:

```markdown
Execute a suíte completa da quarta e da quinta skill:

```bash
uv run python -m unittest discover -s generating-azure-boards-backlog-from-spec/tests -v
uv run python -m unittest discover -s drafting-a-spec-from-business-request/tests -v
```

Valide os cinco pacotes com o utilitário oficial:

```bash
for skill_dir in \
  drafting-a-spec-from-business-request \
  generating-azure-boards-backlog-from-spec \
  refining-user-stories-with-3c \
  refining-user-stories-with-3w \
  refining-user-stories-with-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```
```

- [ ] **Step 4: Verify the diff touches only README.md, pyproject.toml, and the new skill directory**

Run: `git status`
Expected: modified `README.md`; the new directory `drafting-a-spec-from-business-request/` (already committed in Task 1); `pyproject.toml` (already committed in Task 2). No file under `refining-user-stories-with-3w/`, `refining-user-stories-with-3c/`, `refining-user-stories-with-gherkin/`, or `generating-azure-boards-backlog-from-spec/` appears as modified — this confirms the Global Constraint that no existing skill was altered.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs: document drafting-a-spec-from-business-request in README

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Manual acceptance check against the Diligência repository

This task is a verification exercise, not a code change to `gerador-hu` — its output is a judgment call
recorded in the conversation with the user, not a commit. It exists because the design's testing
strategy requires validating the skill against the real motivating example (the duplicate pre-toaf
cancellation request) before considering the feature done.

- [ ] **Step 1: Install (or symlink for a dry run) the skill where it will actually run**

The skill is meant to live inside the target application's own directory. For this check, either copy
`drafting-a-spec-from-business-request/` into a `.claude/skills/` (or equivalent) location at
`/Users/pedroct/Projetos/sefaz/diligencia/` (the workspace root containing `diligencia-api`,
`diligencia-front`, `diligencia-mobile` as siblings), or run the skill's instructions manually against
that path if no install mechanism is configured yet. Confirm `git status` in `diligencia` beforehand so
nothing uncommitted is at risk of being overwritten.

- [ ] **Step 2: Run the skill against the real P1 request**

Provide the skill with this business request text verbatim:

```text
P1 - Título: Cancelamento do pre-toaf duplicado
O sistema esta permitindo dois cancelamentos seguidos do mesmo pre-toaf. Isso acontece quando o
usuário está trabalhando nas duas plataformas simultaneamente e esquece de atualizar a página. Nesse
cenário, ele pode cancelar um pre-toaf que já havia sido cancelado na outra plataforma sem que o
sistema gere um aviso. Nessa situação, o sistema deveria emitir uma mensagem de erro informando que o
pre-toaf já está cancelado, impedindo que o documento seja cancelado duas vezes. Após o fechamento da
mensagem o sistema deveria atualizar a página para que o usuário não consiga repetir a ação de
cancelamento.
```

- [ ] **Step 3: Check the produced spec against this acceptance checklist**

- [ ] The spec treats the request as one scope — no splitting.
- [ ] `## Repositórios considerados` lists at least `diligencia-api` as relevant (the cancellation
      logic lives in `ToafService`/`DiligenciaController` per the earlier `grep` in this
      conversation), with a stated reason; `diligencia-front`/`diligencia-mobile` are either included
      with a reason or explicitly marked not relevant.
- [ ] `## Comportamento atual (evidência no código)` cites at least one real `caminho:linha` inside
      `diligencia-api/src/main/java/br/gov/ce/sefaz/diligencia/...` (e.g., in `ToafService.java` or
      `DiligenciaController.java`), not a fabricated path.
- [ ] `## Comportamento esperado` clearly separates what the email explicitly states (error message on
      duplicate cancel; page refresh after the message closes) from anything inferred.
- [ ] `## Lacunas e perguntas abertas` surfaces the genuinely undefined details (e.g., exact error
      message text, which actor role(s) are affected, whether "atualizar a página" means a full reload
      or a partial re-fetch) rather than inventing them.
- [ ] Nothing in the file resembles an Épico/Feature/História breakdown or `Acceptance Criteria` — that
      stays out of scope for this skill.

- [ ] **Step 4: Report the outcome to the user**

Summarize, in the conversation, whether the checklist passed and — if the request turns out to reveal
more repositories or ambiguity than expected — whether that changes the "always single scope" decision
made during brainstorming. Do not silently reinterpret that decision; if it needs revisiting, flag it
explicitly and get the user's call before changing the skill.

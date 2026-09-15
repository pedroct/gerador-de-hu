# Azure Boards Backlog Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar uma skill que converta uma spec em um backlog Markdown hierárquico para Azure Boards, reutilizando 3C, 3W e Gherkin sem ciclos.

**Architecture:** A nova skill é a orquestradora do documento e chama apenas `refinar-historias-3c` para cada história. A 3C chama as skills-folha 3W e Gherkin. Um validador Python sem dependências externas verifica a estrutura e a numeração do Markdown; a qualidade semântica continua sendo responsabilidade das skills.

**Tech Stack:** Codex Agent Skills em Markdown/YAML, Python 3.14 da Homebrew executado via `uv run`, `unittest` da biblioteca padrão.

**Spec:** `docs/superpowers/specs/2026-09-10-azure-boards-backlog-skill-design.md`

## Global Constraints

- Hierarquia do processo Agile: Épico → Feature → História de Usuário.
- Chaves documentais: `E.0.0`, `E.F.0`, `E.F.S`; nunca tratá-las como Azure work item IDs.
- `Description` da história contém Card 3W e Conversation.
- `Acceptance Criteria` contém somente Confirmation em Gherkin.
- 3W e Gherkin são skills-folha; 3C é a única orquestradora do refinamento e dona da prontidão geral.
- A nova skill gera Markdown e não cria nem altera work items.
- O workspace `/Users/pedroct/skills` não é um repositório Git; não inicializar Git nem executar commits durante este plano.
- Toda edição manual de arquivos deve usar `apply_patch`.

---

### Task 1: Registrar o comportamento RED sem a quarta skill

**Files:**
- Read: `docs/superpowers/specs/2026-09-10-azure-boards-backlog-skill-design.md`
- Read: `refinar-historias-3c/SKILL.md`
- Read: `refinar-historias-3w/SKILL.md`
- Read: `refinar-historias-gherkin/SKILL.md`
- Create: nenhum; o agente de teste retorna o artefato somente em sua mensagem final

**Interfaces:**
- Consumes: uma spec textual com dois objetivos, regras confirmadas, propostas técnicas e decisões pendentes.
- Produces: baseline observado para orientar a forma mínima da quarta skill.

- [ ] **Step 1: Executar o cenário sem a quarta skill**

Despachar um agente em contexto fresco, proibindo o uso de qualquer skill de geração de backlog e fornecendo este pedido:

```text
Analise a spec abaixo e gere um backlog Markdown para Azure Boards na hierarquia
1.0.0 Épico, 1.1.0 Feature e 1.1.1 História. Use as skills 3C, 3W e
Gherkin existentes, mas nenhuma skill de geração de backlog.

Spec:
- Objetivo A: reduzir correções manuais de diligências.
- O analista responsável pode reabrir uma diligência em até 24 horas, com
  justificativa; o status volta para Em análise; essas regras foram confirmadas.
- Auditoria detalhada foi sugerida por compliance, mas os campos ainda não foram decididos.
- Objetivo B: permitir consulta gerencial de diligências atrasadas.
- O gerente precisa decidir redistribuição de trabalho, mas atraso, filtros e
  resultados observáveis ainda não foram definidos.
- Um desenvolvedor sugeriu dois endpoints; isso não foi aprovado como requisito.

Produza um único documento Markdown. Não faça perguntas e não invente regras.
```

- [ ] **Step 2: Avaliar o baseline**

Registrar na conversa de execução se ocorrer qualquer um destes sintomas:

```text
- hierarquia achatada ou pai implícito;
- numeração duplicada ou inconsistente;
- endpoint promovido a requisito;
- perda da origem na spec;
- história gerencial marcada pronta apesar das lacunas;
- Acceptance Criteria preenchido com hipóteses;
- Description sem Card/Conversation;
- formato não reutilizável nos campos do Azure Boards.
```

- [ ] **Step 3: Fixar os critérios GREEN**

Usar somente falhas observadas para ajustar o conteúdo inicialmente planejado da nova skill. Não criar arquivos da skill antes de concluir esta leitura do baseline.

---

### Task 2: Criar o validador estrutural com TDD

**Files:**
- Create: `gerar-backlog-azure-boards/tests/test_validate_backlog.py`
- Create: `gerar-backlog-azure-boards/tests/fixtures/valid-backlog.md`
- Create: `gerar-backlog-azure-boards/scripts/validate_backlog.py`

**Interfaces:**
- Produces: `parse_backlog(text: str) -> list[BacklogItem]`
- Produces: `validate_backlog(text: str, update_mode: bool = False) -> list[str]`
- Produces: CLI `uv run python scripts/validate_backlog.py PATH [--update]`, com saída 0 para válido, 1 para violações e 2 para erro de uso/arquivo.

- [ ] **Step 1: Inicializar o diretório da skill após o RED comportamental**

Run:

```bash
/opt/homebrew/bin/python3 /Users/pedroct/.codex/skills/.system/skill-creator/scripts/init_skill.py gerar-backlog-azure-boards --path /Users/pedroct/skills --resources scripts,references --interface 'display_name=Gerar backlog para Azure Boards' --interface 'short_description=Converte specs em backlog hierárquico revisável' --interface 'default_prompt=Use $gerar-backlog-azure-boards para analisar esta spec e gerar um backlog Markdown para Azure Boards.'
mkdir -p /Users/pedroct/skills/gerar-backlog-azure-boards/tests
```

Expected: scaffold criado e diretório `tests/` existente.

- [ ] **Step 2: Escrever testes que falham porque o módulo ainda não existe**

Criar `tests/test_validate_backlog.py` com `unittest`. O teste importa o script por caminho para não exigir empacotamento:

````python
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_backlog.py"
SPEC = importlib.util.spec_from_file_location("validate_backlog", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

VALID = """# Backlog para Azure Boards

## 1.0.0 [Epic] Corrigir diligências
### Description
Origem na spec: seção 2.

### 1.1.0 [Feature] Reabrir diligência
#### Parent
`1.0.0`
#### Description
Origem na spec: seção 2.1.

#### 1.1.1 [User Story] Reabrir dentro do prazo
##### Parent
`1.1.0`
##### Description
### Card
História confirmada.
### Conversation
Regra confirmada.
##### Acceptance Criteria
```gherkin
# language: pt
Funcionalidade: Reabrir diligência
```
##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: seção 2.1.1
"""


class ValidateBacklogTests(unittest.TestCase):
    def test_accepts_valid_hierarchy(self):
        self.assertEqual([], MODULE.validate_backlog(VALID))

    def test_rejects_duplicate_key(self):
        text = VALID + "\n#### 1.1.1 [User Story] Duplicada\n"
        self.assertIn("duplicate key: 1.1.1", MODULE.validate_backlog(text))

    def test_rejects_wrong_parent(self):
        text = VALID.replace("`1.1.0`", "`1.2.0`")
        self.assertIn("1.1.1 expected parent 1.1.0, got 1.2.0", MODULE.validate_backlog(text))

    def test_rejects_acceptance_content_when_confirmation_absent(self):
        text = VALID.replace("Confirmation: Completa", "Confirmation: Ausente")
        self.assertIn(
            "1.1.1 has Acceptance Criteria while Confirmation is Ausente",
            MODULE.validate_backlog(text),
        )

    def test_requires_story_origin(self):
        text = VALID.replace("- Origem na spec: seção 2.1.1\n", "")
        self.assertIn("1.1.1 is missing Origem na spec", MODULE.validate_backlog(text))

    def test_requires_epic_origin(self):
        text = VALID.replace("Origem na spec: seção 2.\n", "")
        self.assertIn("1.0.0 is missing Origem na spec", MODULE.validate_backlog(text))

    def test_requires_all_refinement_status_fields(self):
        text = VALID.replace("- Card: Estruturado\n", "")
        self.assertIn("1.1.1 is missing refinement field Card", MODULE.validate_backlog(text))

    def test_rejects_missing_parent_item(self):
        text = VALID.replace("### 1.1.0 [Feature]", "### 2.1.0 [Feature]")
        text = text.replace("`1.0.0`", "`2.0.0`", 1)
        self.assertIn("1.1.1 parent 1.1.0 does not exist", MODULE.validate_backlog(text))

    def test_new_mode_requires_contiguous_story_numbers(self):
        text = VALID.replace("1.1.1", "1.1.2")
        self.assertIn("stories under 1.1.0 must start at 1", MODULE.validate_backlog(text))

    def test_update_mode_allows_numbering_gaps(self):
        text = VALID.replace("1.1.1", "1.1.2")
        errors = MODULE.validate_backlog(text, update_mode=True)
        self.assertNotIn("stories under 1.1.0 must start at 1", errors)


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 3: Executar e confirmar RED**

Run:

```bash
cd /Users/pedroct/skills/gerar-backlog-azure-boards
uv run python -m unittest tests/test_validate_backlog.py -v
```

Expected: FAIL durante importação porque `scripts/validate_backlog.py` não existe.

- [ ] **Step 4: Implementar o modelo e parser mínimos**

Criar `scripts/validate_backlog.py` com:

```python
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ITEM_RE = re.compile(
    r"^(?P<marks>#{2,4}) (?P<key>[1-9]\d*\.\d+\.\d+) "
    r"\[(?P<kind>Epic|Feature|User Story)\] (?P<title>\S.*)$"
)
SECTION_NAMES = {"Parent", "Description", "Acceptance Criteria", "Refinement Status"}


@dataclass
class BacklogItem:
    key: str
    kind: str
    title: str
    level: int
    sections: dict[str, list[str]] = field(default_factory=dict)

    def section(self, name: str) -> str:
        return "\n".join(self.sections.get(name, [])).strip()


def parse_backlog(text: str) -> list[BacklogItem]:
    items: list[BacklogItem] = []
    current: BacklogItem | None = None
    section: str | None = None
    in_fence = False
    for raw in text.splitlines():
        if raw.startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else ITEM_RE.match(raw)
        if match:
            current = BacklogItem(
                key=match.group("key"),
                kind=match.group("kind"),
                title=match.group("title"),
                level=len(match.group("marks")),
            )
            items.append(current)
            section = None
            continue
        if current and not in_fence:
            prefix = "#" * (current.level + 1) + " "
            if raw.startswith(prefix) and raw[len(prefix):] in SECTION_NAMES:
                section = raw[len(prefix):]
                current.sections.setdefault(section, [])
                continue
        if current and section:
            current.sections[section].append(raw)
    return items
```

- [ ] **Step 5: Implementar as invariantes e a CLI**

No mesmo arquivo, adicionar:

```python
def _parts(key: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in key.split("."))


def _parent_value(item: BacklogItem) -> str:
    return item.section("Parent").strip().strip("`")


def validate_backlog(text: str, update_mode: bool = False) -> list[str]:
    items = parse_backlog(text)
    errors: list[str] = []
    seen: set[str] = set()
    keys = {item.key for item in items}
    groups: dict[tuple[str, str], list[int]] = {}
    expected = {"Epic": (2, "epics"), "Feature": (3, "features"), "User Story": (4, "stories")}

    for item in items:
        if item.key in seen:
            errors.append(f"duplicate key: {item.key}")
        seen.add(item.key)
        marks, label = expected[item.kind]
        if item.level != marks:
            errors.append(f"{item.key} has wrong heading level for {item.kind}")
        e, f, s = _parts(item.key)
        if item.kind == "Epic":
            if (f, s) != (0, 0):
                errors.append(f"{item.key} is not a valid Epic key")
            groups.setdefault((label, "root"), []).append(e)
        elif item.kind == "Feature":
            if f == 0 or s != 0:
                errors.append(f"{item.key} is not a valid Feature key")
            expected_parent = f"{e}.0.0"
            actual = _parent_value(item)
            if actual != expected_parent:
                errors.append(f"{item.key} expected parent {expected_parent}, got {actual or '<missing>'}")
            if expected_parent not in keys:
                errors.append(f"{item.key} parent {expected_parent} does not exist")
            groups.setdefault((label, expected_parent), []).append(f)
        else:
            if f == 0 or s == 0:
                errors.append(f"{item.key} is not a valid User Story key")
            expected_parent = f"{e}.{f}.0"
            actual = _parent_value(item)
            if actual != expected_parent:
                errors.append(f"{item.key} expected parent {expected_parent}, got {actual or '<missing>'}")
            if expected_parent not in keys:
                errors.append(f"{item.key} parent {expected_parent} does not exist")
            groups.setdefault((label, expected_parent), []).append(s)
            status = item.section("Refinement Status")
            for field_name in ("Card", "Conversation", "Confirmation", "Prontidão"):
                if f"{field_name}:" not in status:
                    errors.append(f"{item.key} is missing refinement field {field_name}")
            if "Confirmation: Ausente" in status and item.section("Acceptance Criteria"):
                errors.append(f"{item.key} has Acceptance Criteria while Confirmation is Ausente")
            if "Acceptance Criteria" not in item.sections:
                errors.append(f"{item.key} is missing Acceptance Criteria heading")
            if "Refinement Status" not in item.sections:
                errors.append(f"{item.key} is missing Refinement Status")
        if not item.section("Description"):
            errors.append(f"{item.key} has empty Description")
        origin_text = item.section("Description") + "\n" + item.section("Refinement Status")
        if "Origem na spec:" not in origin_text:
            errors.append(f"{item.key} is missing Origem na spec")

    for (label, parent), numbers in groups.items():
        if numbers != sorted(numbers):
            errors.append(f"{label} under {parent} must be ascending")
        if not update_mode:
            ordered = sorted(set(numbers))
            if ordered and ordered != list(range(1, len(ordered) + 1)):
                if ordered[0] != 1:
                    errors.append(f"{label} under {parent} must start at 1")
                else:
                    errors.append(f"{label} under {parent} must be contiguous")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an Azure Boards backlog Markdown file")
    parser.add_argument("path", type=Path)
    parser.add_argument("--update", action="store_true", help="allow numbering gaps in an updated backlog")
    args = parser.parse_args(argv)
    try:
        text = args.path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors = validate_backlog(text, update_mode=args.update)
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("Backlog structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Executar e confirmar GREEN**

Run:

```bash
cd /Users/pedroct/skills/gerar-backlog-azure-boards
uv run python -m unittest tests/test_validate_backlog.py -v
```

Expected: 14 tests, `OK`.

- [ ] **Step 7: Criar a fixture válida e testar a CLI**

Criar `tests/fixtures/valid-backlog.md`:

````markdown
# Backlog para Azure Boards

## 1.0.0 [Epic] Corrigir diligências
### Description
Origem na spec: seção 2.

### 1.1.0 [Feature] Reabrir diligência
#### Parent
`1.0.0`
#### Description
Origem na spec: seção 2.1.

#### 1.1.1 [User Story] Reabrir dentro do prazo
##### Parent
`1.1.0`
##### Description
### Card
História confirmada.
### Conversation
Regra confirmada.
##### Acceptance Criteria
```gherkin
# language: pt
Funcionalidade: Reabrir diligência
```
##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: seção 2.1.1
````

Executar:

```bash
cd /Users/pedroct/skills/gerar-backlog-azure-boards
uv run python scripts/validate_backlog.py tests/fixtures/valid-backlog.md
```

Expected: `Backlog structure is valid` e exit code 0.

---

### Task 3: Criar a quarta skill e seu contrato Markdown

**Files:**
- Modify: `gerar-backlog-azure-boards/SKILL.md`
- Modify: `gerar-backlog-azure-boards/agents/openai.yaml`
- Create: `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`

**Interfaces:**
- Consumes: conteúdo de uma spec e, opcionalmente, backlog Markdown existente.
- Consumes: resultado completo de `refinar-historias-3c` por história.
- Produces: um arquivo Markdown conforme `references/backlog-markdown-contract.md`.

- [ ] **Step 1: Escrever `SKILL.md` mínimo orientado pelas falhas RED**

O corpo deve conter estas decisões concretas:

```markdown
---
name: gerar-backlog-azure-boards
description: Use when a product or software specification must be decomposed into an Azure Boards Epic, Feature, and User Story hierarchy or rendered as a reviewable backlog Markdown document.
---

# Generating Azure Boards Backlog From Spec

## Outcome
Transforme somente requisitos rastreáveis em Épicos, Features e Histórias. A numeração é documental; não é ID do Azure Boards.

## Workflow
1. Leia a spec inteira e crie um inventário de objetivos, atores, capacidades, regras, restrições, exemplos, conflitos e lacunas com suas origens.
2. Agrupe objetivos amplos em Épicos; capacidades significativas em Features; resultados coesos para um ator em Histórias. Não crie itens para preencher níveis.
3. Para cada história, **REQUIRED SUB-SKILL:** use refinar-historias-3c. Consuma seu resultado sem recalcular 3W, Conversation, Confirmation ou prontidão.
4. Numere `E.0.0`, `E.F.0`, `E.F.S`; preserve chaves existentes em atualizações.
5. Renderize conforme [references/backlog-markdown-contract.md](references/backlog-markdown-contract.md).
6. Execute `uv run python scripts/validate_backlog.py CAMINHO`; com backlog existente, acrescente `--update`. Corrija violações estruturais e revise semanticamente rastreabilidade, agrupamento e ausência de regras fabricadas.

## Boundaries
- Gere Markdown; não crie work items.
- Não invente Area Path, Iteration Path, Story Points, prioridade, responsável ou datas.
- História rastreável mas incompleta permanece `Não pronta` e sem conteúdo em Acceptance Criteria.
- Requisito sem pai justificável entra em `Itens não cobertos`.
```

- [ ] **Step 2: Escrever o contrato de referência**

Criar `references/backlog-markdown-contract.md` copiando do design:

```text
- definição de Epic, Feature e User Story;
- tabela de numeração e regras de atualização;
- template Markdown completo;
- conteúdo permitido em Description e Acceptance Criteria;
- Refinement Status fora dos campos Azure;
- rastreabilidade e Itens não cobertos;
- diferença entre Markdown de revisão e campos HTML do Azure Boards.
```

Incluir links oficiais:

```text
https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/define-features-epics
https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow
https://learn.microsoft.com/en-us/azure/devops/boards/queries/titles-ids-descriptions
```

- [ ] **Step 3: Conferir metadados da interface**

`agents/openai.yaml` deve ser exatamente compatível com:

```yaml
interface:
  display_name: "Gerar backlog para Azure Boards"
  short_description: "Converte specs em backlog hierárquico revisável"
  default_prompt: "Use $gerar-backlog-azure-boards para analisar esta spec e gerar um backlog Markdown para Azure Boards."
```

- [ ] **Step 4: Validar a skill**

Run:

```bash
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/pedroct/skills/gerar-backlog-azure-boards
```

Expected: `Skill is valid!`.

---

### Task 4: Tornar a integração estritamente acíclica

**Files:**
- Create: `gerar-backlog-azure-boards/tests/test_skill_integration.py`
- Modify: `refinar-historias-3w/SKILL.md`
- Modify: `refinar-historias-gherkin/SKILL.md`
- Modify: `refinar-historias-3c/SKILL.md`

**Interfaces:**
- 3W produces: Card local e estado 3W; nenhuma chamada de sub-skill.
- Gherkin produces: regras, exemplos e estado local da Confirmation; nenhuma chamada de sub-skill.
- 3C consumes: 3W e Gherkin; produces prontidão geral.
- Backlog skill consumes: 3C; não chama 3W/Gherkin diretamente.

- [ ] **Step 1: Escrever teste estático que falha no estado atual**

Criar `tests/test_skill_integration.py`:

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SkillIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.three_w = (ROOT / "refinar-historias-3w" / "SKILL.md").read_text()
        cls.gherkin = (ROOT / "refinar-historias-gherkin" / "SKILL.md").read_text()
        cls.three_c = (ROOT / "refinar-historias-3c" / "SKILL.md").read_text()
        cls.backlog = (ROOT / "gerar-backlog-azure-boards" / "SKILL.md").read_text()

    def test_leaf_skills_do_not_require_subskills(self):
        self.assertNotIn("REQUIRED SUB-SKILL", self.three_w)
        self.assertNotIn("REQUIRED SUB-SKILL", self.gherkin)

    def test_three_c_is_the_refinement_orchestrator(self):
        self.assertIn("REQUIRED SUB-SKILL:** use refinar-historias-3w", self.three_c)
        self.assertIn("REQUIRED SUB-SKILL:** refinar-historias-gherkin", self.three_c)
        self.assertIn("única prontidão geral", self.three_c)

    def test_backlog_calls_only_three_c(self):
        self.assertIn("REQUIRED SUB-SKILL:** use refinar-historias-3c", self.backlog)
        self.assertNotIn("REQUIRED SUB-SKILL:** use refinar-historias-3w", self.backlog)
        self.assertNotIn("REQUIRED SUB-SKILL:** use refinar-historias-gherkin", self.backlog)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Executar e confirmar RED**

Run:

```bash
cd /Users/pedroct/skills/gerar-backlog-azure-boards
uv run python -m unittest tests/test_skill_integration.py -v
```

Expected: FAIL porque 3W e Gherkin ainda contêm `REQUIRED SUB-SKILL` e a 3C não declara textualmente a propriedade exclusiva da prontidão.

- [ ] **Step 3: Ajustar a skill 3W**

Remover o encaminhamento direto a Gherkin. O contrato final deve dizer:

```markdown
## Limite da skill

Esta é uma skill-folha. Entregue somente mapa 3W, história ou rascunho, perguntas e estado 3W. Não produza Conversation, Gherkin ou prontidão geral. Quando outra skill a invocar, devolva esses artefatos ao chamador.

Para Azure Boards, o conteúdo 3W pertence a `Description`, nunca a `Acceptance Criteria`.
```

- [ ] **Step 4: Ajustar a skill Gherkin**

Remover a chamada obrigatória a 3W e a prontidão geral. O contrato final deve dizer:

```markdown
## Entrada e limite da skill

Consuma a história, os fatos e as decisões fornecidos. Se o ator, o valor ou uma regra necessária estiver ausente, reporte a lacuna sem chamar outra skill.

Esta é uma skill-folha. Retorne regras confirmadas, exemplos e estado da Confirmation (`Ausente`, `Parcial` ou `Completa`). Não emita prontidão geral. Sob a 3C, aceite como confirmadas somente decisões da Conversation.
```

- [ ] **Step 5: Ajustar a skill 3C**

Preservar as duas chamadas de sub-skill e acrescentar:

```markdown
A 3C é a única dona da prontidão geral. Estados locais da 3W e Gherkin são insumos; não os trate como vereditos concorrentes.
```

- [ ] **Step 6: Executar e confirmar GREEN**

Run:

```bash
cd /Users/pedroct/skills/gerar-backlog-azure-boards
uv run python -m unittest tests/test_skill_integration.py -v
```

Expected: 8 tests, `OK`.

---

### Task 5: Verificar o comportamento da quarta skill

**Files:**
- Read: `gerar-backlog-azure-boards/SKILL.md`
- Read: `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`
- Test: `gerar-backlog-azure-boards/scripts/validate_backlog.py`
- Create: nenhum artefato persistente; agentes retornam resultados em mensagens finais

**Interfaces:**
- Consumes: cenário da Task 1 e uma variação totalmente confirmada.
- Produces: evidência comportamental GREEN e REFACTOR.

- [ ] **Step 1: Reexecutar o cenário original com a quarta skill**

Usar um agente em contexto fresco com acesso explícito à quarta skill e à spec do cenário RED.

Expected:

```text
- pelo menos dois Épicos quando os objetivos não puderem compartilhar justificadamente o mesmo pai;
- cada Feature e história com Parent explícito;
- origem na spec em cada história;
- endpoint somente em propostas da Conversation;
- história de reabertura com Confirmation baseada nas regras confirmadas;
- história gerencial Não pronta e sem conteúdo em Acceptance Criteria;
- Estado 3C preservado, sem recálculo pela quarta skill.
```

- [ ] **Step 2: Testar uma spec totalmente confirmada**

Fornecer uma spec com um objetivo, duas capacidades e duas histórias confirmadas por Feature. Verificar numeração `1.0.0`, `1.1.0`, `1.1.1`, `1.1.2`, `1.2.0`, `1.2.1`, `1.2.2`, além de Gherkin somente nas histórias.

- [ ] **Step 3: Testar atualização de backlog existente**

Fornecer um backlog com chaves `1.1.1` e `1.1.3`, informar que `1.1.2` foi removida e pedir uma nova história. Expected: preservar as chaves e atribuir `1.1.4`; nunca reutilizar `1.1.2`.

- [ ] **Step 4: Revisar manualmente os três resultados**

Confirmar:

```text
- nenhum requisito sem origem;
- nenhuma regra inventada;
- nenhum conteúdo de Conversation em Acceptance Criteria;
- nenhum Gherkin em Épico ou Feature;
- nenhuma chave chamada de Azure ID;
- nenhuma mutação externa sugerida como já executada.
```

Se surgir uma falha nova, alterar somente a instrução que fecha a brecha e repetir o mesmo cenário em contexto fresco.

---

### Task 6: Verificação final das quatro skills

**Files:**
- Verify: `gerar-backlog-azure-boards/**`
- Verify: `refinar-historias-3c/SKILL.md`
- Verify: `refinar-historias-3w/SKILL.md`
- Verify: `refinar-historias-gherkin/SKILL.md`

**Interfaces:**
- Produces: evidência final estrutural, automatizada e comportamental.

- [ ] **Step 1: Executar todos os testes Python**

Run:

```bash
cd /Users/pedroct/skills/gerar-backlog-azure-boards
uv run python -m unittest discover -s tests -v
```

Expected: 22 tests, `OK`.

- [ ] **Step 2: Validar os quatro pacotes de skill**

Run:

```bash
for skill_dir in \
  /Users/pedroct/skills/gerar-backlog-azure-boards \
  /Users/pedroct/skills/refinar-historias-3c \
  /Users/pedroct/skills/refinar-historias-3w \
  /Users/pedroct/skills/refinar-historias-gherkin; do
  uv run --with pyyaml python \
    /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$skill_dir"
done
```

Expected: quatro ocorrências de `Skill is valid!`.

- [ ] **Step 3: Verificar scaffolds e links internos**

Run:

```bash
! rg -n '\[TODO|TODO:|TBD' \
  /Users/pedroct/skills/gerar-backlog-azure-boards \
  /Users/pedroct/skills/refinar-historias-3c \
  /Users/pedroct/skills/refinar-historias-3w \
  /Users/pedroct/skills/refinar-historias-gherkin

test -f /Users/pedroct/skills/gerar-backlog-azure-boards/references/backlog-markdown-contract.md
test -f /Users/pedroct/skills/gerar-backlog-azure-boards/scripts/validate_backlog.py
```

Expected: exit 0 e nenhuma ocorrência de scaffold inacabado.

- [ ] **Step 4: Executar o validador em um exemplo final**

Usar a fixture válida criada na Task 2 e executar:

```bash
uv run python /Users/pedroct/skills/gerar-backlog-azure-boards/scripts/validate_backlog.py /Users/pedroct/skills/gerar-backlog-azure-boards/tests/fixtures/valid-backlog.md
```

Expected: `Backlog structure is valid`.

- [ ] **Step 5: Relatar o estado real**

Informar arquivos criados e modificados, contagem de testes, resultado do `quick_validate.py`, cenários comportamentais executados e a ausência de operações no Azure Boards. Não alegar commit, pois o workspace não possui repositório Git.

### Task 2: Criar o validador estrutural com TDD

**Files:**
- Create: `generating-azure-boards-backlog-from-spec/tests/test_validate_backlog.py`
- Create: `generating-azure-boards-backlog-from-spec/tests/fixtures/valid-backlog.md`
- Create: `generating-azure-boards-backlog-from-spec/scripts/validate_backlog.py`

**Interfaces:**
- Produces: `parse_backlog(text: str) -> list[BacklogItem]`
- Produces: `validate_backlog(text: str, update_mode: bool = False) -> list[str]`
- Produces: CLI `uv run python scripts/validate_backlog.py PATH [--update]`, com saída 0 para válido, 1 para violações e 2 para erro de uso/arquivo.

- [ ] **Step 1: Inicializar o diretório da skill após o RED comportamental**

Run:

```bash
/opt/homebrew/bin/python3 /Users/pedroct/.codex/skills/.system/skill-creator/scripts/init_skill.py generating-azure-boards-backlog-from-spec --path /Users/pedroct/skills --resources scripts,references --interface 'display_name=Gerar backlog para Azure Boards' --interface 'short_description=Converte specs em backlog hierárquico revisável' --interface 'default_prompt=Use $generating-azure-boards-backlog-from-spec para analisar esta spec e gerar um backlog Markdown para Azure Boards.'
mkdir -p /Users/pedroct/skills/generating-azure-boards-backlog-from-spec/tests
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
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
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
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python -m unittest tests/test_validate_backlog.py -v
```

Expected: 10 tests, `OK`.

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
cd /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
uv run python scripts/validate_backlog.py tests/fixtures/valid-backlog.md
```

Expected: `Backlog structure is valid` e exit code 0.

---

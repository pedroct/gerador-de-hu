from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_backlog.py"
SPEC = importlib.util.spec_from_file_location("validate_backlog", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None
assert SPEC.loader is not None
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
###### Card
História confirmada.
###### Conversation
Regra confirmada.
##### Acceptance Criteria
```gherkin
# language: pt
Funcionalidade: Reabrir diligência

  Cenário: Reabrir uma diligência dentro do prazo
    Dado que uma diligência pode ser reaberta dentro do prazo
    Quando o analista responsável a reabre com uma justificativa
    Então o status da diligência deve voltar para "Em análise"
```
##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: seção 2.1.1
"""


class ValidateBacklogTests(unittest.TestCase):
    def test_rejects_empty_document(self):
        self.assertIn(
            "o backlog deve conter pelo menos um item de trabalho",
            MODULE.validate_backlog(""),
        )

    def test_rejects_work_item_with_invalid_key(self):
        text = "## 123 [Epic] Chave inválida\n"
        errors = MODULE.validate_backlog(text)
        self.assertTrue(
            any(error.startswith("título de item de trabalho inválido:") for error in errors)
        )

    def test_rejects_work_item_with_invalid_heading_level(self):
        text = "##### 1.1.1 [User Story] Nível inválido\n"
        self.assertIn(
            "1.1.1 tem nível de título incorreto para User Story",
            MODULE.validate_backlog(text),
        )

    def test_rejects_empty_origin_reference(self):
        text = VALID.replace("- Origem na spec: seção 2.1.1\n", "- Origem na spec:\n")
        self.assertIn("1.1.1 não possui Origem na spec", MODULE.validate_backlog(text))

    def test_accepts_valid_hierarchy(self):
        self.assertEqual([], MODULE.validate_backlog(VALID))

    def test_rejects_duplicate_key(self):
        text = VALID + "\n#### 1.1.1 [User Story] Duplicada\n"
        self.assertIn("chave duplicada: 1.1.1", MODULE.validate_backlog(text))

    def test_rejects_wrong_parent(self):
        text = VALID.replace("`1.1.0`", "`1.2.0`")
        self.assertIn(
            "1.1.1 esperava o pai 1.1.0, recebeu 1.2.0", MODULE.validate_backlog(text)
        )

    def test_rejects_acceptance_content_when_confirmation_is_not_complete(self):
        for confirmation in ("Ausente", "Parcial"):
            with self.subTest(confirmation=confirmation):
                text = VALID.replace("Confirmation: Completa", f"Confirmation: {confirmation}")
                self.assertIn(
                    f"1.1.1 possui Acceptance Criteria enquanto Confirmation está {confirmation}",
                    MODULE.validate_backlog(text),
                )

    def test_requires_story_origin(self):
        text = VALID.replace("- Origem na spec: seção 2.1.1\n", "")
        self.assertIn("1.1.1 não possui Origem na spec", MODULE.validate_backlog(text))

    def test_requires_epic_origin(self):
        text = VALID.replace("Origem na spec: seção 2.\n", "")
        self.assertIn("1.0.0 não possui Origem na spec", MODULE.validate_backlog(text))

    def test_requires_all_refinement_status_fields(self):
        text = VALID.replace("- Card: Estruturado\n", "")
        self.assertIn(
            "1.1.1 não possui o campo de refinamento Card", MODULE.validate_backlog(text)
        )

    def test_rejects_missing_parent_item(self):
        text = VALID.replace("### 1.1.0 [Feature]", "### 2.1.0 [Feature]")
        text = text.replace("`1.0.0`", "`2.0.0`", 1)
        self.assertIn("1.1.1 não possui o pai 1.1.0", MODULE.validate_backlog(text))

    def test_new_mode_requires_contiguous_story_numbers(self):
        text = VALID.replace("1.1.1", "1.1.2")
        self.assertIn("histórias sob 1.1.0 deve começar em 1", MODULE.validate_backlog(text))

    def test_update_mode_allows_numbering_gaps(self):
        text = VALID.replace("1.1.1", "1.1.2")
        errors = MODULE.validate_backlog(text, update_mode=True)
        self.assertNotIn("histórias sob 1.1.0 deve começar em 1", errors)


if __name__ == "__main__":
    unittest.main()

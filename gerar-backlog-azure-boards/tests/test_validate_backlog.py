from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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

VALID_WITH_BUG = (
    VALID
    + """
#### 1.1.2 [Bug] Reabertura falha sem mensagem de erro
##### Parent
`1.1.0`
##### Description
###### Card
Comportamento incorreto confirmado.
###### Conversation
Divergência confirmada.
##### Acceptance Criteria
```gherkin
# language: pt
Funcionalidade: Reabrir diligência

  Cenário: Falha silenciosa ao reabrir fora do prazo
    Dado que uma diligência não pode mais ser reaberta
    Quando o analista tenta reabri-la
    Então o sistema deve informar o motivo da rejeição
```
##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: seção 2.1.2
"""
)


def _com_tags(text: str, conteudo: str) -> str:
    """Declara `Tags` na primeira folha, entre `Parent` e `Description`."""
    return text.replace(
        "##### Parent\n`1.1.0`\n", f"##### Parent\n`1.1.0`\n##### Tags\n{conteudo}\n", 1
    )


def _com_depende_de(text: str, conteudo: str) -> str:
    """Declara `Depende de` na primeira folha, entre `Parent` e `Description`."""
    return text.replace(
        "##### Parent\n`1.1.0`\n", f"##### Parent\n`1.1.0`\n##### Depende de\n{conteudo}\n", 1
    )


def _com_id_no_epic(text: str, conteudo: str = "`4721`") -> str:
    return text.replace(
        "## 1.0.0 [Epic] Corrigir diligências\n",
        f"## 1.0.0 [Epic] Corrigir diligências\n### Azure Boards ID\n{conteudo}\n",
        1,
    )


def _com_id_na_feature(text: str, conteudo: str = "`4722`") -> str:
    return text.replace(
        "#### Parent\n`1.0.0`\n", f"#### Parent\n`1.0.0`\n#### Azure Boards ID\n{conteudo}\n", 1
    )


class ValidateBacklogTests(unittest.TestCase):
    def test_parse_backlog_ignores_headings_inside_fences(self):
        text = """## 1.0.0 [Epic] Épico
Texto fora de seção.
### Description
Texto da descrição.
```markdown
## 9.0.0 [Epic] Exemplo
```
"""
        items = MODULE.parse_backlog(text)
        self.assertEqual(["1.0.0"], [item.key for item in items])
        self.assertIn("Texto da descrição.", items[0].section("Description"))

    def test_rejects_invalid_epic_key(self):
        text = "## 1.1.0 [Epic] Épico inválido\n"
        self.assertIn("1.1.0 não é uma chave Epic válida", MODULE.validate_backlog(text))

    def test_rejects_invalid_feature_key(self):
        text = """## 1.0.0 [Epic] Épico
### 1.1.1 [Feature] Feature inválida
#### Parent
`1.0.0`
#### Description
Origem na spec: seção 1.
"""
        self.assertIn("1.1.1 não é uma chave Feature válida", MODULE.validate_backlog(text))

    def test_rejects_invalid_story_key(self):
        text = """## 1.0.0 [Epic] Épico
### 1.1.0 [Feature] Feature
#### Parent
`1.0.0`
#### Description
Origem na spec: seção 1.
#### 1.1.0 [User Story] História inválida
##### Parent
`1.1.0`
##### Description
Origem na spec: seção 1.1.
"""
        self.assertIn("1.1.0 não é uma chave User Story válida", MODULE.validate_backlog(text))

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

    def test_accepts_backlog_without_refinement_status(self):
        slim = VALID.split("##### Refinement Status", maxsplit=1)[0].rstrip() + "\n"
        slim = slim.replace(
            "Regra confirmada.\n",
            "Regra confirmada.\nOrigem na spec: seção 2.1.1.\n",
        )
        self.assertEqual([], MODULE.validate_backlog(slim))

    def test_rejects_duplicate_key(self):
        text = VALID + "\n#### 1.1.1 [User Story] Duplicada\n"
        self.assertIn("chave duplicada: 1.1.1", MODULE.validate_backlog(text))

    def test_rejects_wrong_parent(self):
        text = VALID.replace("`1.1.0`", "`1.2.0`")
        self.assertIn("1.1.1 esperava o pai 1.1.0, recebeu 1.2.0", MODULE.validate_backlog(text))

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
        self.assertIn("1.1.1 não possui o campo de refinamento Card", MODULE.validate_backlog(text))

    def test_rejects_missing_parent_item(self):
        text = VALID.replace("### 1.1.0 [Feature]", "### 2.1.0 [Feature]")
        text = text.replace("`1.0.0`", "`2.0.0`", 1)
        self.assertIn("1.1.1 não possui o pai 1.1.0", MODULE.validate_backlog(text))

    def test_new_mode_requires_contiguous_story_numbers(self):
        text = VALID.replace("1.1.1", "1.1.2")
        self.assertIn("itens sob 1.1.0 deve começar em 1", MODULE.validate_backlog(text))

    def test_update_mode_allows_numbering_gaps(self):
        text = VALID.replace("1.1.1", "1.1.2")
        errors = MODULE.validate_backlog(text, update_mode=True)
        self.assertNotIn("itens sob 1.1.0 deve começar em 1", errors)

    def test_reports_unordered_group(self):
        errors = MODULE._validate_groups({("histórias", "1.1.0"): [2, 1]}, update_mode=True)
        self.assertIn("histórias sob 1.1.0 deve estar em ordem crescente", errors)

    def test_reports_non_contiguous_group(self):
        errors = MODULE._validate_groups({("histórias", "1.1.0"): [1, 3]}, update_mode=False)
        self.assertIn("histórias sob 1.1.0 deve ser contíguo", errors)

    def test_empty_group_has_no_errors(self):
        self.assertEqual([], MODULE._validate_groups({}, update_mode=False))

    def test_main_returns_success_for_valid_backlog(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "backlog.md"
            path.write_text(VALID, encoding="utf-8")
            self.assertEqual(0, MODULE.main([str(path)]))

    def test_main_returns_one_for_invalid_backlog(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "backlog.md"
            path.write_text("", encoding="utf-8")
            self.assertEqual(1, MODULE.main([str(path)]))

    def test_main_returns_two_for_unreadable_backlog(self):
        self.assertEqual(2, MODULE.main(["/caminho/que/nao/existe/backlog.md"]))

    def test_accepts_bug_as_sibling_leaf_of_user_story(self):
        self.assertEqual([], MODULE.validate_backlog(VALID_WITH_BUG))

    def test_rejects_invalid_bug_key(self):
        text = VALID_WITH_BUG.replace("#### 1.1.2 [Bug]", "#### 1.1.0 [Bug]")
        self.assertIn("1.1.0 não é uma chave Bug válida", MODULE.validate_backlog(text))

    def test_rejects_bug_with_wrong_parent(self):
        text = VALID_WITH_BUG.replace(
            "#### 1.1.2 [Bug] Reabertura falha sem mensagem de erro\n##### Parent\n`1.1.0`",
            "#### 1.1.2 [Bug] Reabertura falha sem mensagem de erro\n##### Parent\n`1.2.0`",
        )
        self.assertIn("1.1.2 esperava o pai 1.1.0, recebeu 1.2.0", MODULE.validate_backlog(text))

    def test_bug_requires_refinement_status_fields(self):
        text = VALID_WITH_BUG.replace(
            "- Card: Estruturado\n- Conversation: Suficiente para o escopo\n"
            "- Confirmation: Completa\n- Prontidão: Pronta\n- Origem na spec: seção 2.1.2\n",
            "- Conversation: Suficiente para o escopo\n"
            "- Confirmation: Completa\n- Prontidão: Pronta\n- Origem na spec: seção 2.1.2\n",
        )
        self.assertIn("1.1.2 não possui o campo de refinamento Card", MODULE.validate_backlog(text))

    def test_bug_rejects_acceptance_content_when_confirmation_is_not_complete(self):
        text = VALID_WITH_BUG.replace(
            "- Confirmation: Completa\n- Prontidão: Pronta\n- Origem na spec: seção 2.1.2\n",
            "- Confirmation: Ausente\n- Prontidão: Pronta\n- Origem na spec: seção 2.1.2\n",
        )
        self.assertIn(
            "1.1.2 possui Acceptance Criteria enquanto Confirmation está Ausente",
            MODULE.validate_backlog(text),
        )

    def test_user_story_and_bug_share_the_same_sequence_group(self):
        # 1.1.1 [User Story] e 1.1.2 [Bug] juntos devem contar como uma sequência
        # contígua única sob a Feature, não como duas sequências separadas por tipo.
        self.assertEqual([], MODULE.validate_backlog(VALID_WITH_BUG))
        text = VALID_WITH_BUG.replace("1.1.2", "1.1.3")
        self.assertIn(
            "itens sob 1.1.0 deve ser contíguo",
            MODULE.validate_backlog(text),
        )

    def test_malformed_bug_heading_is_flagged(self):
        text = "## 123 [Bug] Chave inválida\n"
        errors = MODULE.validate_backlog(text)
        self.assertTrue(
            any(error.startswith("título de item de trabalho inválido:") for error in errors)
        )

    # --- Campos novos do contrato: Tags, Depende de e Azure Boards ID ---------------
    # Este script é a cópia canônica do contrato. Sem estes casos, acrescentar os nomes a
    # SECTION_NAMES destravaria o gate sem validar nada — confiança falsa, pior que recusar.

    def test_accepts_tags_on_leaf_item(self):
        text = _com_tags(VALID, "debito-tecnico, dt-restricao")
        self.assertEqual([], MODULE.validate_backlog(text))

    def test_rejects_tag_with_semicolon(self):
        text = _com_tags(VALID, "debito-tecnico; dt-restricao")
        self.assertIn(
            "1.1.1: a tag 'debito-tecnico; dt-restricao' contém ';', "
            "que o Azure Boards usa como separador",
            MODULE.validate_backlog(text),
        )

    def test_rejects_empty_tags_section(self):
        text = _com_tags(VALID, "")
        self.assertIn("1.1.1 possui a seção Tags presente e vazia", MODULE.validate_backlog(text))

    def test_accepts_dependency_between_sibling_leaves(self):
        text = _com_depende_de(VALID_WITH_BUG, "`1.1.2`")
        self.assertEqual([], MODULE.validate_backlog(text))

    def test_rejects_dependency_on_missing_key(self):
        text = _com_depende_de(VALID, "`9.9.9`")
        self.assertIn(
            "1.1.1 depende de 9.9.9, que não existe no backlog", MODULE.validate_backlog(text)
        )

    def test_rejects_dependency_on_non_leaf_item(self):
        text = _com_depende_de(VALID, "`1.1.0`")
        self.assertIn(
            "1.1.1 depende de 1.1.0, que não é item de folha", MODULE.validate_backlog(text)
        )

    def test_rejects_dependency_declared_outside_leaf(self):
        text = VALID_WITH_BUG.replace(
            "#### Parent\n`1.0.0`\n", "#### Parent\n`1.0.0`\n#### Depende de\n`1.1.2`\n", 1
        )
        self.assertIn(
            "1.1.0 declara Depende de, permitido só em item de folha",
            MODULE.validate_backlog(text),
        )

    def test_rejects_empty_dependency_section(self):
        text = _com_depende_de(VALID, "")
        self.assertIn(
            "1.1.1 possui a seção Depende de presente e vazia", MODULE.validate_backlog(text)
        )

    def test_rejects_dependency_cycle(self):
        text = _com_depende_de(VALID_WITH_BUG, "`1.1.2`")
        text = text.replace(
            "#### 1.1.2 [Bug] Reabertura falha sem mensagem de erro\n##### Parent\n`1.1.0`\n",
            "#### 1.1.2 [Bug] Reabertura falha sem mensagem de erro\n##### Parent\n`1.1.0`\n"
            "##### Depende de\n`1.1.1`\n",
        )
        self.assertTrue(
            any(
                error.startswith("ciclo de dependência entre")
                for error in MODULE.validate_backlog(text)
            )
        )

    def test_accepts_existing_azure_boards_id_on_epic_and_feature(self):
        text = _com_id_no_epic(_com_id_na_feature(VALID))
        self.assertEqual([], MODULE.validate_backlog(text))

    def test_rejects_azure_boards_id_on_leaf_item(self):
        text = VALID.replace(
            "##### Parent\n`1.1.0`\n", "##### Parent\n`1.1.0`\n##### Azure Boards ID\n`4723`\n", 1
        )
        self.assertIn(
            "1.1.1 declara Azure Boards ID, permitido só em Epic e Feature",
            MODULE.validate_backlog(text),
        )

    def test_rejects_feature_with_id_under_epic_without_id(self):
        text = _com_id_na_feature(VALID)
        self.assertIn(
            "1.1.0 declara Azure Boards ID, mas seu pai 1.0.0 não declara",
            MODULE.validate_backlog(text),
        )

    def test_rejects_azure_boards_id_that_is_not_a_positive_integer(self):
        text = _com_id_no_epic(VALID, "`0`")
        self.assertIn(
            "1.0.0: '0' não é um ID de work item inteiro e positivo",
            MODULE.validate_backlog(text),
        )

    def test_rejects_empty_azure_boards_id_section(self):
        text = _com_id_no_epic(VALID, "")
        self.assertIn(
            "1.0.0 possui a seção Azure Boards ID presente e vazia",
            MODULE.validate_backlog(text),
        )


if __name__ == "__main__":
    unittest.main()

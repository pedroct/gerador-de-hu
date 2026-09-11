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
        # refining-user-stories-with-3w has no references/ directory; the other three do.
        cls.existing_skill_references = [
            (
                ROOT / "refining-user-stories-with-3c" / "references" / "azure-boards-fields.md"
            ).read_text(),
            (
                ROOT
                / "refining-user-stories-with-gherkin"
                / "references"
                / "gherkin-practices.md"
            ).read_text(),
            (
                ROOT
                / "generating-azure-boards-backlog-from-spec"
                / "references"
                / "backlog-markdown-contract.md"
            ).read_text(),
            (
                ROOT
                / "generating-azure-boards-backlog-from-spec"
                / "references"
                / "brownfield-validation.md"
            ).read_text(),
        ]

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
        other_skill_names = (
            "refining-user-stories-with-3w",
            "refining-user-stories-with-3c",
            "refining-user-stories-with-gherkin",
            "generating-azure-boards-backlog-from-spec",
        )
        self.assert_has_no_named_skill_invocation(self.drafting, other_skill_names)
        self.assert_has_no_named_skill_invocation(self.investigation, other_skill_names)

    def test_existing_skills_do_not_reference_drafting_skill(self):
        for text in (self.three_w, self.three_c, self.gherkin, self.backlog):
            self.assertNotIn("drafting-a-spec-from-business-request", text)
        for text in self.existing_skill_references:
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

    def test_investigation_reference_prefixes_evidence_with_repo_name_when_multiple_repos(self):
        self.assertIn(
            "Quando mais de um repositório estiver em escopo, prefixe o caminho com o nome do "
            "repositório",
            self.investigation,
        )

    def test_skill_classifies_request_as_defect_improvement_or_other(self):
        self.assertIn("## Classificação", self.drafting)
        self.assertIn("Defeito | Melhoria | Outro", self.drafting)
        self.assertIn("**Defeito**", self.drafting)
        self.assertIn("**Melhoria**", self.drafting)
        self.assertIn("**Outro**", self.drafting)

    def test_skill_does_not_select_a_work_item_type(self):
        self.assertIn(
            "esta skill não cria, seleciona nem sugere tipo de work item específico",
            self.drafting,
        )


if __name__ == "__main__":
    unittest.main()

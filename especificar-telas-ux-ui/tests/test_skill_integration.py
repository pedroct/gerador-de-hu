import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class SkillIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        skill_dir = ROOT / "especificar-telas-ux-ui"
        cls.skill = (skill_dir / "SKILL.md").read_text()
        cls.reference = (
            skill_dir / "references" / "ui-brownfield-validation.md"
        ).read_text()
        cls.agent = (skill_dir / "agents" / "openai.yaml").read_text()

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
                        msg=f"leaf skill calls {skill_name!r}: {line}",
                    )

    def test_skill_has_discoverable_contract(self):
        self.assertIn("name: especificar-telas-ux-ui", self.skill)
        self.assertIn("Use quando", self.skill)
        self.assertIn("tela nova ou fluxo de tela alterado", self.skill)

    def test_skill_is_leaf_and_never_invokes_other_skills(self):
        self.assertNotIn("REQUIRED SUB-SKILL", self.skill)
        other_skill_names = (
            "redigir-spec-pedido-negocio",
            "entrevistar-lacunas-requisito",
            "gerar-backlog-azure-boards",
            "refinar-historias-3c",
            "refinar-historias-3w",
            "refinar-historias-gherkin",
            "especificar-debitos-tecnicos",
            "revisar-textos-requisitos",
            "publicar-backlog-azure-boards",
        )
        self.assert_has_no_named_skill_invocation(self.skill, other_skill_names)

    def test_skill_declares_mode_per_platform(self):
        self.assertIn("Modo Web", self.skill)
        self.assertIn("Modo Mobile", self.skill)
        self.assertIn("Greenfield-UI", self.skill)
        self.assertIn("Brownfield-UI", self.skill)
        self.assertIn("Não aplicável", self.skill)

    def test_skill_delegates_copy_to_revisar_textos_requisitos(self):
        self.assertIn("revisar-textos-requisitos", self.skill)
        self.assertIn("não defina o texto final", self.skill)

    def test_skill_never_creates_task_or_bug_for_screen_need(self):
        self.assertIn(
            "Não crie item do tipo Task nem Bug para necessidade de tela",
            self.skill,
        )
        self.assertIn("sempre uma User Story de design nova", self.skill)

    def test_skill_groups_one_design_item_per_platform(self):
        self.assertIn("Sempre um item por plataforma necessária", self.skill)
        self.assertIn(
            "nunca agrupe web e mobile no mesmo item de design", self.skill
        )

    def test_screen_script_avoids_gherkin_syntax(self):
        self.assertIn("sem sintaxe Gherkin", self.skill)
        self.assertIn("sem `Dado/Quando/Então`", self.skill)

    def test_reference_defines_matrix_and_exact_statuses(self):
        self.assertIn(
            "| Requisito | Plataforma | Evidência `caminho:linha` | Status | Confiança |",
            self.reference,
        )
        expected_statuses = (
            "`Implementado`",
            "`Parcialmente implementado`",
            "`Não encontrado`",
            "`Impossível validar`",
            "`Não aplicável`",
        )
        for status in expected_statuses:
            self.assertIn(status, self.reference)
        self.assertIn(
            "Ausência de evidência não significa `Implementado`", self.reference
        )

    def test_reference_inspection_is_read_only_without_authorization(self):
        for command in ("`rg`", "`find`", "`git status`"):
            self.assertIn(command, self.reference)
        self.assertIn("sem autorização explícita", self.reference)

    def test_reference_never_creates_requirement_from_incidental_code(self):
        self.assertIn(
            "Compare o código somente com a necessidade de tela do requisito da spec",
            self.reference,
        )

    def test_skill_has_openai_metadata_in_portuguese(self):
        self.assertIn('display_name: "Especificar telas UX-UI"', self.agent)
        self.assertIn("$especificar-telas-ux-ui", self.agent)


if __name__ == "__main__":
    unittest.main()

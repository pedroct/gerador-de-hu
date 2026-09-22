import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class SkillIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        skill_dir = ROOT / "especificar-debitos-tecnicos"
        cls.skill = (skill_dir / "SKILL.md").read_text()
        cls.agent = (skill_dir / "agents" / "openai.yaml").read_text()

    def test_skill_has_discoverable_contract(self):
        self.assertIn("name: especificar-debitos-tecnicos", self.skill)
        self.assertIn("Use when", self.skill)
        self.assertIn("débitos técnicos", self.skill)

    def test_skill_preserves_reference_prioritization(self):
        self.assertIn("Código", self.skill)
        self.assertIn("Arquitetura", self.skill)
        self.assertIn("Testes", self.skill)
        self.assertIn("Dependências", self.skill)
        self.assertIn("Documentação", self.skill)
        self.assertIn("Infraestrutura", self.skill)
        self.assertIn("(Impacto + Risco) × (6 − Esforço)", self.skill)

    def test_skill_generates_azure_ready_spec_without_mutating_azure(self):
        for field in (
            "Tipo sugerido",
            "Título",
            "Descrição",
            "Critérios de aceite",
            "Evidência",
            "Origem",
            "Lacunas",
        ):
            self.assertIn(field, self.skill)
        self.assertIn("não cria nem altera work items", self.skill)
        self.assertIn("não invente", self.skill.lower())

    def test_skill_distinguishes_bug_from_user_story(self):
        self.assertIn("Bug", self.skill)
        self.assertIn("User Story", self.skill)
        self.assertIn("comportamento atual incorreto", self.skill)
        self.assertIn("melhoria de manutenibilidade", self.skill)

    def test_skill_has_openai_metadata_in_portuguese(self):
        self.assertIn('display_name: "Especificar débitos técnicos"', self.agent)
        self.assertIn("$especificar-debitos-tecnicos", self.agent)


if __name__ == "__main__":
    unittest.main()

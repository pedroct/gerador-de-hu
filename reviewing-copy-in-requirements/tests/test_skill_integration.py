import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ReviewingCopySkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "reviewing-copy-in-requirements" / "SKILL.md").read_text()
        cls.reference = (
            ROOT
            / "reviewing-copy-in-requirements"
            / "references"
            / "copy-review-framework.md"
        ).read_text()
        cls.metadata = (
            ROOT / "reviewing-copy-in-requirements" / "agents" / "openai.yaml"
        ).read_text()

    def test_skill_is_in_portuguese_and_has_discriminating_scope(self):
        self.assertIn("name: reviewing-copy-in-requirements", self.skill)
        self.assertIn("requisitos", self.skill.lower())
        self.assertIn("Não use para escrever campanhas", self.skill)

    def test_skill_requires_context_before_definitive_copy(self):
        self.assertIn("faça perguntas objetivas", self.skill)
        self.assertIn("Não invente público", self.skill)
        self.assertIn("Dúvida/decisão pendente", self.skill)

    def test_skill_defines_review_output_and_severity(self):
        for term in ("Trecho:", "Diagnóstico:", "Impacto:", "Recomendação:", "Sugestão de copy:"):
            self.assertIn(term, self.skill)
        for severity in ("Crítico", "Importante", "Aperfeiçoamento"):
            self.assertIn(severity, self.skill)

    def test_reference_is_linked_and_contains_product_copy_heuristics(self):
        self.assertIn("references/copy-review-framework.md", self.skill)
        for term in ("Clareza", "Valor", "Ação e estado", "Consistência"):
            self.assertIn(term, self.reference)

    def test_openai_metadata_mentions_skill_explicitly(self):
        self.assertIn("$reviewing-copy-in-requirements", self.metadata)


if __name__ == "__main__":
    unittest.main()

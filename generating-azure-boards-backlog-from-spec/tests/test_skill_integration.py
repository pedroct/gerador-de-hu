from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SkillIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.three_w = (ROOT / "refining-user-stories-with-3w" / "SKILL.md").read_text()
        cls.gherkin = (ROOT / "refining-user-stories-with-gherkin" / "SKILL.md").read_text()
        cls.three_c = (ROOT / "refining-user-stories-with-3c" / "SKILL.md").read_text()
        cls.backlog = (ROOT / "generating-azure-boards-backlog-from-spec" / "SKILL.md").read_text()

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

    def test_leaf_skills_do_not_call_other_skills(self):
        self.assertNotIn("REQUIRED SUB-SKILL", self.three_w)
        self.assertNotIn("REQUIRED SUB-SKILL", self.gherkin)
        self.assert_has_no_named_skill_invocation(
            self.three_w,
            ("refining-user-stories-with-3c", "refining-user-stories-with-gherkin"),
        )
        self.assert_has_no_named_skill_invocation(
            self.gherkin,
            ("refining-user-stories-with-3w", "refining-user-stories-with-3c"),
        )

    def test_leaf_skills_do_not_emit_general_readiness(self):
        self.assertIn(
            "Não produza Conversation, Gherkin ou prontidão geral.", self.three_w
        )
        self.assertIn("Não emita prontidão geral.", self.gherkin)

    def test_three_w_returns_only_its_leaf_outputs(self):
        self.assertNotIn("**Possíveis divisões**", self.three_w)
        self.assertIn(
            "Entregue somente mapa 3W, história ou rascunho, perguntas e estado 3W.",
            self.three_w,
        )
        self.assertIn(
            "Quando for invocada por outra skill, devolva esses artefatos ao chamador.",
            self.three_w,
        )
        example = self.three_w.split("## Exemplo", maxsplit=1)[1]
        self.assertNotIn("Gherkin", example)

    def test_gherkin_declares_local_confirmation_states(self):
        self.assertIn(
            "estado da Confirmation (`Ausente`, `Parcial` ou `Completa`)",
            self.gherkin,
        )

    def test_three_c_passes_complete_payload_to_gherkin(self):
        self.assertIn(
            "Encaminhe à Gherkin a história ou Card, os fatos e as decisões "
            "registradas na Conversation, incluindo as regras decididas.",
            self.three_c,
        )

    def test_gherkin_consumes_payload_without_calling_another_skill(self):
        self.assertIn(
            "Consuma a história ou Card, os fatos e as decisões registradas na "
            "Conversation, incluindo as regras decididas.",
            self.gherkin,
        )
        self.assertIn("Aponte lacunas sem chamar outra skill.", self.gherkin)

    def test_three_c_is_the_refinement_orchestrator(self):
        self.assertIn("REQUIRED SUB-SKILL:** use refining-user-stories-with-3w", self.three_c)
        self.assertIn("REQUIRED SUB-SKILL:** refining-user-stories-with-gherkin", self.three_c)
        self.assertIn("única prontidão geral", self.three_c)

    def test_backlog_calls_only_three_c(self):
        self.assertIn("REQUIRED SUB-SKILL:** use refining-user-stories-with-3c", self.backlog)
        self.assertNotIn("REQUIRED SUB-SKILL:** use refining-user-stories-with-3w", self.backlog)
        self.assertNotIn("REQUIRED SUB-SKILL:** use refining-user-stories-with-gherkin", self.backlog)
        self.assert_has_no_named_skill_invocation(
            self.backlog,
            ("refining-user-stories-with-3w", "refining-user-stories-with-gherkin"),
        )


if __name__ == "__main__":
    unittest.main()

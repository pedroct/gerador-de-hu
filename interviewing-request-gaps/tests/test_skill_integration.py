import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class InterviewingSkillIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interviewing = (ROOT / "interviewing-request-gaps" / "SKILL.md").read_text()
        cls.notice = (ROOT / "interviewing-request-gaps" / "NOTICE.md").read_text()
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
                        msg=f"interviewing skill calls {skill_name!r}: {line}",
                    )

    def test_interviewing_skill_does_not_call_other_skills(self):
        self.assertNotIn("REQUIRED SUB-SKILL", self.interviewing)
        other_skill_names = (
            "refining-user-stories-with-3w",
            "refining-user-stories-with-3c",
            "refining-user-stories-with-gherkin",
            "generating-azure-boards-backlog-from-spec",
            "drafting-a-spec-from-business-request",
        )
        self.assert_has_no_named_skill_invocation(self.interviewing, other_skill_names)

    def test_other_skills_do_not_reference_interviewing_skill(self):
        for text in (self.three_w, self.three_c, self.gherkin):
            self.assertNotIn("interviewing-request-gaps", text)
        for text in self.existing_skill_references:
            self.assertNotIn("interviewing-request-gaps", text)

    def test_backlog_skill_only_suggests_interviewing_skill_conditionally(self):
        # generating-azure-boards-backlog-from-spec referencia interviewing-request-gaps
        # por nome (README.md documenta essa exceção), mas só como sugestão condicional
        # ao usuário — nunca como REQUIRED SUB-SKILL nem como invocação direta.
        self.assertNotIn("REQUIRED SUB-SKILL:** use interviewing-request-gaps", self.backlog)
        self.assert_has_no_named_skill_invocation(self.backlog, ("interviewing-request-gaps",))
        self.assertIn(
            "indicação ao usuário, nunca uma chamada direta a essa skill", self.backlog
        )

    def test_interviewing_skill_computes_frontier_each_round(self):
        self.assertIn("Pergunte a fronteira inteira em uma única rodada", self.interviewing)
        self.assertIn("Recalcule a fronteira", self.interviewing)

    def test_interviewing_skill_asks_frontier_with_recommended_answer_format(self):
        self.assertIn("❓ **P1**", self.interviewing)
        self.assertIn("➡️", self.interviewing)
        self.assertIn("resposta recomendada", self.interviewing.lower())

    def test_interviewing_skill_treats_explicit_deferral_as_valid_decision(self):
        self.assertIn(
            "Adiamento explícito do usuário é uma decisão válida",
            self.interviewing,
        )

    def test_interviewing_skill_never_fills_gaps_by_plausibility(self):
        self.assertIn(
            "Nunca preencha uma lacuna por plausibilidade",
            self.interviewing,
        )

    def test_interviewing_skill_does_not_investigate_source_code(self):
        self.assertIn("Não investigue código-fonte", self.interviewing)

    def test_notice_file_has_mit_attribution_to_grilling_origin(self):
        self.assertIn("MIT License", self.notice)
        self.assertIn("Copyright (c) 2026 Matt Pocock", self.notice)
        self.assertIn(
            "https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling",
            self.notice,
        )


if __name__ == "__main__":
    unittest.main()

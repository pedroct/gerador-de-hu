import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sem_quebras(texto: str) -> str:
    """Normaliza o reflow do Markdown para a asserção não quebrar ao reformatar o parágrafo."""
    return " ".join(texto.split())


class InterviewingSkillIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interviewing = (ROOT / "entrevistar-lacunas-requisito" / "SKILL.md").read_text()
        cls.notice = (ROOT / "entrevistar-lacunas-requisito" / "NOTICE.md").read_text()
        cls.three_w = (ROOT / "refinar-historias-3w" / "SKILL.md").read_text()
        cls.three_c = (ROOT / "refinar-historias-3c" / "SKILL.md").read_text()
        cls.gherkin = (ROOT / "refinar-historias-gherkin" / "SKILL.md").read_text()
        cls.backlog = (ROOT / "gerar-backlog-azure-boards" / "SKILL.md").read_text()
        # refinar-historias-3w has no references/ directory; the other three do.
        cls.existing_skill_references = [
            (ROOT / "refinar-historias-3c" / "references" / "azure-boards-fields.md").read_text(),
            (
                ROOT / "refinar-historias-gherkin" / "references" / "gherkin-practices.md"
            ).read_text(),
            (
                ROOT / "gerar-backlog-azure-boards" / "references" / "backlog-markdown-contract.md"
            ).read_text(),
            (
                ROOT / "gerar-backlog-azure-boards" / "references" / "brownfield-validation.md"
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
            "refinar-historias-3w",
            "refinar-historias-3c",
            "refinar-historias-gherkin",
            "gerar-backlog-azure-boards",
            "redigir-spec-pedido-negocio",
        )
        self.assert_has_no_named_skill_invocation(self.interviewing, other_skill_names)

    def test_other_skills_do_not_reference_interviewing_skill(self):
        for text in (self.three_w, self.three_c, self.gherkin):
            self.assertNotIn("entrevistar-lacunas-requisito", text)
        for text in self.existing_skill_references:
            self.assertNotIn("entrevistar-lacunas-requisito", text)

    def test_backlog_skill_only_suggests_interviewing_skill_conditionally(self):
        # gerar-backlog-azure-boards referencia entrevistar-lacunas-requisito
        # por nome (README.md documenta essa exceção), mas só como sugestão condicional
        # ao usuário — nunca como REQUIRED SUB-SKILL nem como invocação direta.
        self.assertNotIn("REQUIRED SUB-SKILL:** use entrevistar-lacunas-requisito", self.backlog)
        self.assert_has_no_named_skill_invocation(self.backlog, ("entrevistar-lacunas-requisito",))
        self.assertIn("indicação ao usuário, nunca uma chamada direta a essa skill", self.backlog)

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

    def test_escopo_filtra_por_audiencia(self):
        self.assertIn("escopo", self.interviewing)
        self.assertIn("Negócio", self.interviewing)
        self.assertIn("Técnico", self.interviewing)

    def test_escopo_compoe_com_a_fronteira_em_vez_de_substitui_la(self):
        """Sem isso, a rodada técnica perguntaria algo que depende de decisão de negócio aberta."""
        texto = sem_quebras(self.interviewing)
        self.assertIn("compõe com a fronteira", texto)
        self.assertIn("fica fora da fronteira", texto)

    def test_spec_sem_rotulos_pergunta_tudo(self):
        """Toda spec já escrita não tem rótulos; o escopo é filtro opcional, não requisito de
        formato."""
        texto = sem_quebras(self.interviewing)
        self.assertIn("Spec sem rótulos de audiência", texto)
        self.assertIn("pergunte todas as lacunas", texto)

    def test_resposta_pode_criar_lacuna_nova(self):
        """Decisão de negócio que gera trabalho técnico não pode virar descoberta na
        implementação."""
        texto = sem_quebras(self.interviewing)
        self.assertIn("registrar uma lacuna nova", texto)

    def test_description_nao_fixa_uma_unica_skill_de_origem(self):
        frontmatter = self.interviewing[: self.interviewing.index("---", 4)]
        self.assertTrue(
            "redigir-spec-demanda-azure-boards" in frontmatter
            or ("tipicamente produzida por `redigir-spec-pedido-negocio`" not in self.interviewing)
        )


if __name__ == "__main__":
    unittest.main()

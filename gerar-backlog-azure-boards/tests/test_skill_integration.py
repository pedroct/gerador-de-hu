import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class SkillIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.three_w = (ROOT / "refinar-historias-3w" / "SKILL.md").read_text()
        cls.gherkin = (ROOT / "refinar-historias-gherkin" / "SKILL.md").read_text()
        cls.gherkin_practices = (
            ROOT / "refinar-historias-gherkin" / "references" / "gherkin-practices.md"
        ).read_text()
        cls.three_c = (ROOT / "refinar-historias-3c" / "SKILL.md").read_text()
        cls.backlog = (ROOT / "gerar-backlog-azure-boards" / "SKILL.md").read_text()
        cls.backlog_contract = (
            ROOT
            / "gerar-backlog-azure-boards"
            / "references"
            / "backlog-markdown-contract.md"
        ).read_text()
        brownfield_path = (
            ROOT
            / "gerar-backlog-azure-boards"
            / "references"
            / "brownfield-validation.md"
        )
        cls.brownfield = brownfield_path.read_text() if brownfield_path.exists() else ""
        cls.readme = (ROOT / "README.md").read_text()

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
            ("refinar-historias-3c", "refinar-historias-gherkin"),
        )
        self.assert_has_no_named_skill_invocation(
            self.gherkin,
            ("refinar-historias-3w", "refinar-historias-3c"),
        )

    def test_leaf_skills_do_not_emit_general_readiness(self):
        self.assertIn("Não produza Conversation, Gherkin ou prontidão geral.", self.three_w)
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
        self.assertIn(
            "estado local da Confirmation (`Ausente`, `Parcial` ou `Completa`)",
            self.gherkin_practices,
        )
        self.assertNotIn("veredito de prontidão", self.gherkin_practices)

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
        self.assertIn("REQUIRED SUB-SKILL:** use refinar-historias-3w", self.three_c)
        self.assertIn("REQUIRED SUB-SKILL:** refinar-historias-gherkin", self.three_c)
        self.assertIn(
            "REQUIRED OPTIONAL SUB-SKILL:** use\n   `especificar-debitos-tecnicos`",
            self.three_c,
        )
        self.assertIn("única prontidão geral", self.three_c)

    def test_backlog_calls_only_three_c(self):
        self.assertIn("REQUIRED SUB-SKILL:** use refinar-historias-3c", self.backlog)
        self.assertNotIn("REQUIRED SUB-SKILL:** use refinar-historias-3w", self.backlog)
        self.assertNotIn(
            "REQUIRED SUB-SKILL:** use refinar-historias-gherkin", self.backlog
        )
        self.assert_has_no_named_skill_invocation(
            self.backlog,
            ("refinar-historias-3w", "refinar-historias-gherkin"),
        )

    def test_backlog_detects_greenfield_brownfield_and_ambiguous_mode(self):
        self.assertIn("**Greenfield:**", self.backlog)
        self.assertIn("**Brownfield:**", self.backlog)
        self.assertIn("escolha Brownfield conservadoramente", self.backlog)
        self.assertIn("registre a incerteza", self.backlog)
        self.assertIn("não exija uma inspeção inexistente", self.backlog)
        self.assertIn("antes de decompor ou refinar", self.backlog)

    def test_brownfield_reference_defines_matrix_and_exact_statuses(self):
        self.assertTrue(self.brownfield, "brownfield-validation.md must exist")
        self.assertIn(
            "| Requisito | Evidência `caminho:linha` | Status | Impacto | Confiança |",
            self.brownfield,
        )
        expected_statuses = (
            "`Implementado`",
            "`Parcialmente implementado`",
            "`Divergente`",
            "`Não encontrado`",
            "`Impossível validar`",
        )
        for status in expected_statuses:
            self.assertIn(status, self.brownfield)
        self.assertIn("Ausência de evidência não significa `Implementado`", self.brownfield)

    def test_brownfield_inspection_is_read_only_without_authorization(self):
        for command in ("`rg`", "`find`", "`git status`"):
            self.assertIn(command, self.brownfield)
        self.assertIn("leitura de arquivos de configuração", self.brownfield)
        self.assertIn(
            "Não execute scripts, testes, builds, servidores, migrações ou a aplicação",
            self.brownfield,
        )
        self.assertIn("sem autorização explícita", self.brownfield)

    def test_brownfield_implementation_policy_does_not_create_requirements(self):
        self.assertIn("Compare o código somente com requisitos da spec", self.brownfield)
        self.assertIn(
            "Código existente não confirma valor nem decisão de negócio e não cria regra",
            self.brownfield,
        )
        self.assertIn("não geram itens duplicados por padrão", self.brownfield)
        self.assertIn("documentar comportamento existente", self.brownfield)

    def test_implementation_evidence_stays_out_of_acceptance_criteria(self):
        self.assertIn("##### Implementation Evidence", self.backlog_contract)
        self.assertNotIn("## Validation Summary", self.backlog_contract)
        self.assertNotIn("##### Refinement Status", self.backlog_contract)
        self.assertIn(
            "Evidência de implementação nunca pertence a `Acceptance Criteria`",
            self.backlog_contract,
        )
        self.assertIn("não infira Who, What, Why ou valor", self.three_w)
        self.assertIn("não transforma código em confirmação", self.gherkin)
        self.assertIn("Implementation Evidence", self.three_c)

    def test_contract_and_readme_document_both_modes(self):
        self.assertIn("- Modo: Greenfield | Brownfield", self.backlog_contract)
        self.assertIn("- Raiz analisada:", self.backlog_contract)
        self.assertIn("- Código-fonte relevante:", self.backlog_contract)
        self.assertIn("### Fluxo Greenfield", self.readme)
        self.assertIn("### Fluxo Brownfield", self.readme)
        self.assertIn("Parcialmente implementado", self.readme)
        self.assertIn("Impossível validar", self.readme)


if __name__ == "__main__":
    unittest.main()

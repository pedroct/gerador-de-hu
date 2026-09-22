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

    def test_greenfield_ui_has_explicit_status_mapping(self):
        self.assertIn(
            "Em Greenfield-UI, classifique todo par como `Não encontrado`", self.skill
        )
        self.assertIn(
            "Em Greenfield-UI (nenhum código de front-end acessível para a plataforma), "
            "classifique sempre como",
            self.reference,
        )


    def test_skill_declares_ux_audience_and_bans_process_jargon(self):
        self.assertIn("## Para quem a saída é escrita", self.skill)
        self.assertIn("Sem vocabulário de processo no briefing", self.skill)
        self.assertIn("Sem `caminho:linha` no briefing", self.skill)
        self.assertIn(
            "Economia de texto é requisito da saída, não estilo", self.skill
        )

    def test_traceability_is_a_separate_section_from_the_briefing(self):
        self.assertIn(
            "## Rastreabilidade — não é para a equipe de UX-UI", self.skill
        )

    def test_item_template_has_design_sections(self):
        for secao in (
            "### Por que esta tela existe",
            "### Quem usa",
            "### Onde fica",
            "### O que a pessoa precisa fazer",
            "### Regras que a tela precisa honrar",
            "### Campos",
            "### Estados da tela",
            "### Volume e escala",
            "### Referência de padrão no produto",
            "### Textos a definir",
            "### Perguntas abertas",
            "### Fora do escopo desta tela, mas afetado pelo mesmo requisito",
            "### O que se espera desta especificação",
        ):
            self.assertIn(secao, self.skill, msg=f"template sem {secao!r}")

    def test_screen_script_covers_first_use_entry_point_and_implied_actions(self):
        self.assertIn("o **primeiro uso**, com a base vazia", self.skill)
        self.assertIn("o **ponto de entrada**", self.skill)
        self.assertIn("toda ação pressuposta por alguma regra", self.skill)
        self.assertIn("Regra sem ação correspondente é lacuna", self.skill)

    def test_screen_script_is_written_in_user_voice(self):
        self.assertIn("na voz de quem usa, nunca na voz do sistema", self.skill)
        self.assertIn("Não escreva o briefing na voz do sistema", self.skill)

    def test_changed_content_of_existing_screen_is_a_ui_facet(self):
        self.assertIn("o que uma tela existente passa a mostrar", self.skill)
        self.assertIn("silêncio não é cobertura", self.skill)
        self.assertIn("Nunca conclua cobertura por omissão", self.skill)

    def test_unconfirmed_platform_becomes_open_question_instead_of_item(self):
        self.assertIn("a necessidade **não está confirmada**", self.skill)
        self.assertIn("não gere um item vazio para a outra", self.skill)
        self.assertIn(
            "Necessidade de plataforma não confirmada", self.reference
        )

    def test_reference_separates_available_component_from_adopted_pattern(self):
        self.assertIn("## Evidência de padrão visual", self.reference)
        self.assertIn(
            "componente disponível de padrão adotado", self.reference
        )
        self.assertIn("não é** referência de padrão", self.reference)

    def test_open_questions_declare_what_they_block(self):
        self.assertIn("| # | Pergunta | O que trava no desenho |", self.skill)
        self.assertIn(
            "Pergunta aberta sem consequência declarada é ruído", self.skill
        )


    def test_flow_diagram_is_required_in_mermaid(self):
        self.assertIn("### Fluxo da tela", self.skill)
        self.assertIn("Desenhe o fluxo em diagrama Mermaid", self.skill)
        self.assertIn("`flowchart TD`", self.skill)
        self.assertIn("`stateDiagram-v2`", self.skill)
        self.assertIn("tela de caminho único não precisa de diagrama", self.skill)

    def test_flow_diagram_exposes_undecided_paths(self):
        self.assertIn("caminho ainda pendente de decisão em linha tracejada", self.skill)
        self.assertIn(
            "Caminho sem origem, sem volta ou sem interação definida é lacuna",
            self.skill,
        )
        self.assertIn(
            "Não feche um caminho no diagrama para ele parecer completo", self.skill
        )


if __name__ == "__main__":
    unittest.main()

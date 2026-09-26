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
            ROOT / "gerar-backlog-azure-boards" / "references" / "backlog-markdown-contract.md"
        ).read_text()
        brownfield_path = (
            ROOT / "gerar-backlog-azure-boards" / "references" / "brownfield-validation.md"
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
        self.assertNotIn("REQUIRED SUB-SKILL:** use refinar-historias-gherkin", self.backlog)
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

    def test_backlog_carrega_a_demanda_de_origem_nos_metadados(self):
        """O ID da Demanda existia na spec e no manifesto, mas nao no backlog.

        Sem ele, quem revisa nao consegue escolher entre as duas publicadoras sem
        voltar a spec: uma cria Epicos filhos da Demanda, a outra os cria soltos.
        """
        self.assertIn("Demanda de Negócio de origem", self.backlog_contract)
        self.assertIn("Fonte da Demanda", self.backlog_contract)
        self.assertIn("Não se aplica — a spec não nasceu de uma Demanda", self.backlog_contract)
        self.assertIn("Demanda de Negócio de origem", self.backlog)

    def test_a_demanda_de_origem_nunca_e_inferida_fora_da_spec(self):
        self.assertIn("Nunca infira o ID de outra fonte que não a spec", self.backlog_contract)

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

    def test_backlog_consumes_telas_output_as_file_not_invocation(self):
        self.assertIn(
            "como input opcional por arquivo — nunca como invocação de `especificar-telas-ux-ui`",
            self.backlog,
        )
        self.assert_has_no_named_skill_invocation(
            self.backlog,
            ("especificar-telas-ux-ui",),
        )

    def test_backlog_contract_has_no_named_skill_invocation_for_telas(self):
        self.assert_has_no_named_skill_invocation(
            self.backlog_contract,
            ("especificar-telas-ux-ui",),
        )

    def test_contract_template_has_a_slot_for_depende_de_and_bloqueia(self):
        self.assertIn("##### Depende de", self.backlog_contract)
        self.assertIn(
            "uma ou mais chaves `E.F.S` de item de folha já existente no backlog",
            self.backlog_contract,
        )
        self.assertIn("Bloqueia: 1.1.1", self.backlog_contract)

    def test_backlog_pairs_design_item_and_fills_dependency_fields(self):
        self.assertIn(
            "crie a User Story de design correspondente como item-irmão do item funcional "
            "que ela bloqueia, sob a mesma Feature",
            self.backlog,
        )
        self.assertIn("Um item de design nascido do passo 2 é sempre `User Story`", self.backlog)
        self.assertIn(
            "preencha `Depende de` no item funcional com a chave `E.F.S` do item de "
            "design, e `Bloqueia` no item de design com a chave `E.F.S` do item funcional",
            self.backlog,
        )

    def test_backlog_boundaries_distinguish_dependency_link_from_informative_bloqueia(self):
        """A Tarefa 9 tornou `Depende de` gerador de link real (System.LinkTypes.Dependency-
        Reverse); a asserção anterior, que descrevia os dois campos como só 'informativo',
        descrevia o contrato pré-Tarefa 9 e ficou incorreta com a reescrita do contrato."""
        self.assertIn(
            "gera, na publicação, a relação real `System.LinkTypes.Dependency-Reverse`",
            self.backlog,
        )
        self.assertIn(
            "`Bloqueia`, ao contrário, permanece texto informativo em prosa",
            self.backlog,
        )

    def test_contract_documents_bloqueia_as_informative_and_linkless(self):
        self.assertIn("## Depende de e Bloqueia", self.backlog_contract)
        self.assertIn("Não altera a prontidão calculada pela 3C", self.backlog_contract)
        self.assertIn(
            "`Bloqueia` permanece **texto informativo**, sem seção própria nem chave estruturada",
            self.backlog_contract,
        )
        self.assertIn("Não gera link algum; é só rastro documental.", self.backlog_contract)
        self.assertIn(
            "Só `Depende de` gera relação real no Azure Boards",
            self.backlog_contract,
        )

    def test_readme_documents_screen_spec_skill(self):
        self.assertIn(
            "| [`especificar-telas-ux-ui`](especificar-telas-ux-ui/SKILL.md) "
            "| Um requisito da spec pode exigir tela nova ou fluxo de tela alterado "
            "em web e/ou mobile |",
            self.readme,
        )
        self.assertIn("- **Telas UX-UI:** identifica, por inspeção somente leitura", self.readme)

    def test_atalho_por_pasta_nao_substitui_a_busca_por_titulo(self) -> None:
        """A busca por título é fallback permanente: sem ela, toda spec antiga para de funcionar."""
        self.assertIn("DN-<id>-<slug>", self.backlog)
        self.assertIn("telas-ux-ui.md", self.backlog)
        self.assertIn("Spec: Telas UX-UI", self.backlog)
        self.assertIn("fallback permanente", self.backlog)

    def test_companheiros_da_pasta_nao_viram_item_de_backlog(self) -> None:
        """Mandar abrir `debitos-tecnicos.md` sem dizer o limite convida a virá-lo backlog."""
        texto = " ".join(self.backlog.split())
        self.assertIn(
            "`debitos-tecnicos.md` e `revisao-textos.md`, que são contexto rotulado, "
            "nunca origem de item de backlog",
            texto,
        )

    def test_spec_de_origem_registra_o_caminho_completo_ate_spec_md(self) -> None:
        """É esse caminho que liga o backlog publicado de volta à pasta da Demanda."""
        texto = " ".join(self.backlog_contract.split())
        self.assertIn(
            "- Spec de origem: [caminho completo até `spec.md`, "
            "ou documento, versão ou localização]",
            texto,
        )
        self.assertIn("docs/specs/DN-14125-emissao-de-convites/spec.md", texto)
        self.assertIn("nunca fonte do ID da Demanda", texto)

    def test_contrato_proibe_o_nome_da_pasta_como_fonte_do_id(self) -> None:
        """Depois da convenção há um `DN-14125` a um basename de distância,

        e ele parece uma resposta.
        """
        self.assertIn("nome da pasta", self.backlog_contract)
        self.assertIn("DN-", self.backlog_contract)

    def test_sugestao_de_entrevista_nomeia_o_escopo(self) -> None:
        self.assertIn("escopo `negócio`", self.backlog)
        self.assertIn("escopo `técnico`", self.backlog)

    def test_readme_descreve_as_duas_rodadas(self) -> None:
        self.assertIn("duas rodadas", self.readme)
        self.assertIn("negocio.md", self.readme)

    def test_reconhece_spec_de_debitos_tecnicos_como_entrada_valida(self) -> None:
        """Companheiro é contexto; spec de entrada é origem — os dois papéis convivem."""
        self.assertIn("## Specs de entrada reconhecidas", self.backlog)
        self.assertIn("Spec: Débitos técnicos", self.backlog)
        self.assertIn(
            "não localizado como companheiro dentro da pasta de outra Demanda",
            self.backlog,
        )
        self.assertIn(
            "`debitos-tecnicos.md` e `revisao-textos.md`, que são contexto rotulado, "
            "nunca origem de item de backlog",
            self.backlog,
        )

    def test_emite_vocabulario_de_tags_por_origem_do_item(self) -> None:
        self.assertIn("## Tags emitidas", self.backlog)
        self.assertIn("**Epic e Feature nunca recebem tags**", self.backlog)
        self.assertIn("`debito-tecnico`", self.backlog)
        self.assertIn("`dt-restricao`, `dt-candidato` ou `dt-a-confirmar`", self.backlog)
        self.assertIn("`design-ux-ui`", self.backlog)
        self.assertIn("`plataforma-web`", self.backlog)
        self.assertIn("`plataforma-mobile`", self.backlog)
        self.assertIn("`dn-<id>`", self.backlog)

    def test_epico_e_feature_de_debito_nomeiam_capacidade_nao_o_debito(self) -> None:
        """Decisão de 2026-09-12: hierarquia é por capacidade, não por problema."""
        self.assertIn(
            "Epic e Feature nomeiam a **capacidade de produto afetada** pelo débito",
            self.backlog,
        )
        self.assertIn(
            'um Epic "Débito técnico" com Features por categoria seria contêiner do problema',
            self.backlog,
        )

    def test_criterios_do_dt_viram_contexto_da_conversation_nao_acceptance_criteria(self) -> None:
        self.assertIn(
            "forneça os bullets de `### Critérios de aceite` do DT como contexto rotulado "
            "de entrada para a Conversation da 3C",
            self.backlog,
        )
        self.assertIn("não os copie diretamente para `Acceptance Criteria`", self.backlog)

    def test_backlog_de_debito_indica_publicadora_solta_mesmo_com_demanda(self) -> None:
        self.assertIn(
            "indique ainda assim `publicar-backlog-azure-boards` (a publicadora solta)",
            self.backlog,
        )
        self.assertIn("nunca `publicar-backlog-demanda-azure-boards`", self.backlog)


if __name__ == "__main__":
    unittest.main()

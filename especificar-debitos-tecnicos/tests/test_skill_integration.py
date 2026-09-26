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

    def test_skill_aceita_diretorio_de_destino_opcional(self):
        """Com diretório, grava com nome fixo; sem diretório, segue como antes."""
        self.assertIn("debitos-tecnicos.md", self.skill)
        self.assertIn("diretório de destino", self.skill)
        self.assertIn("Sem diretório de destino", self.skill)

    def test_resumo_priorizado_declara_a_coluna_faixa(self):
        """A coluna `Faixa` é contrato estrutural, não prosa: `gerar-backlog-azure-boards`
        a lê para emitir a tag `dt-<faixa>`. Se alguém a remover daqui, a tag morre em
        silêncio e ninguém percebe até a query do board voltar vazia."""
        self.assertIn("| Prioridade | Faixa |", self.skill)

    def test_declara_a_secao_fonte_da_demanda(self):
        """É de `## Fonte da Demanda` que sai a tag `dn-<id>`; sem a seção no template, o
        backlog perde a rastreabilidade da Demanda."""
        self.assertIn("## Fonte da Demanda", self.skill)

    def test_registra_que_a_faixa_e_fotografia_da_geracao(self):
        """A tag `dt-<faixa>` envelhece: uma reavaliação posterior não atualiza o work item
        já criado. A ressalva tem de estar escrita onde a Faixa é preenchida."""
        self.assertIn("fotografia da geração, não obrigação recalculável", self.skill)

    def test_indica_a_publicadora_solta_para_o_backlog_de_debitos(self):
        """A publicadora de Demanda herdaria dela o Iteration Path, e o débito nasceria na
        sprint da Demanda — exatamente a sprint em que ele não será pago."""
        self.assertIn("(a publicadora solta) como próxima etapa manual", self.skill)


if __name__ == "__main__":
    unittest.main()

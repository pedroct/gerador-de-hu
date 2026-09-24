"""Testes da política de roteamento, sem rede.

O que se testa aqui é a tabela determinística: dadas respostas do Jev, qual skill
sai. A qualidade do julgamento do modelo é medida à parte, por
`scripts/avaliar_roteador.py`, que faz chamadas reais.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "roteamento.py"
SPEC = importlib.util.spec_from_file_location("roteamento", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

NOULS = (
    "tem_lacunas_abertas",
    "ja_existe_demanda_no_board",
    "descreve_interacao_de_tela",
    "tem_copy_de_interface",
    "menciona_debito_tecnico",
)


def respostas(
    tipo: str,
    *,
    confianca: float = 0.99,
    refinamento: str = "nao_aplicavel",
    **noul: float,
) -> dict[str, Any]:
    """Monta uma resposta do Jev; tudo que não for informado fica em 0.0."""
    saida: dict[str, Any] = {
        "tipo_de_entrada": {
            "type": "choice",
            "choice": tipo,
            "confidence": confianca,
            "probabilities": {tipo: confianca},
        },
        "lacuna_de_refinamento": {
            "type": "choice",
            "choice": refinamento,
            "confidence": 0.9,
            "probabilities": {refinamento: 0.9},
        },
    }
    for chave in NOULS:
        saida[chave] = {"type": "noul", "noul": noul.get(chave, 0.0)}
    return saida


class TestRotaPrincipal(unittest.TestCase):
    def test_id_de_demanda_vai_para_a_skill_de_demanda(self) -> None:
        r = MODULE.rotear(respostas("id_demanda_azure_boards"))
        self.assertEqual(r["skill"], "redigir-spec-demanda-azure-boards")

    def test_pedido_informal_vai_para_drafting_de_pedido(self) -> None:
        r = MODULE.rotear(respostas("pedido_informal_negocio"))
        self.assertEqual(r["skill"], "redigir-spec-pedido-negocio")

    def test_spec_com_lacunas_vai_para_entrevista(self) -> None:
        r = MODULE.rotear(respostas("spec_escrita", tem_lacunas_abertas=0.9))
        self.assertEqual(r["skill"], "entrevistar-lacunas-requisito")

    def test_spec_sem_lacunas_vai_para_geracao_de_backlog(self) -> None:
        r = MODULE.rotear(respostas("spec_escrita", tem_lacunas_abertas=0.1))
        self.assertEqual(r["skill"], "gerar-backlog-azure-boards")

    def test_backlog_com_demanda_usa_a_publicadora_vinculada(self) -> None:
        r = MODULE.rotear(respostas("backlog_markdown", ja_existe_demanda_no_board=0.9))
        self.assertEqual(r["skill"], "publicar-backlog-demanda-azure-boards")

    def test_backlog_sem_demanda_usa_a_publicadora_solta(self) -> None:
        r = MODULE.rotear(respostas("backlog_markdown", ja_existe_demanda_no_board=0.1))
        self.assertEqual(r["skill"], "publicar-backlog-azure-boards")

    def test_debito_tecnico_vai_para_spec_de_debitos(self) -> None:
        r = MODULE.rotear(respostas("debito_tecnico"))
        self.assertEqual(r["skill"], "especificar-debitos-tecnicos")

    def test_regras_confirmadas_vao_para_gherkin(self) -> None:
        r = MODULE.rotear(respostas("regras_de_negocio_confirmadas"))
        self.assertEqual(r["skill"], "refinar-historias-gherkin")

    def test_material_nao_reconhecido_nao_roteia(self) -> None:
        r = MODULE.rotear(respostas("outro"))
        self.assertIsNone(r["skill"])


class TestRefinamento(unittest.TestCase):
    def test_cada_lacuna_leva_a_sua_rubrica(self) -> None:
        esperado = {
            "ator_objetivo_ou_valor_vagos": "refinar-historias-3w",
            "falta_conversa_e_confirmacao": "refinar-historias-3c",
            "regras_confirmadas_sem_exemplos": "refinar-historias-gherkin",
        }
        for lacuna, skill in esperado.items():
            with self.subTest(lacuna=lacuna):
                r = MODULE.rotear(respostas("historia_individual", refinamento=lacuna))
                self.assertEqual(r["skill"], skill)

    def test_historia_sem_lacuna_identificavel_nao_roteia(self) -> None:
        r = MODULE.rotear(respostas("historia_individual", refinamento="nao_aplicavel"))
        self.assertIsNone(r["skill"])


class TestCompanheiras(unittest.TestCase):
    def test_sugere_ux_copy_e_debito_quando_os_sinais_passam_do_limiar(self) -> None:
        r = MODULE.rotear(
            respostas(
                "pedido_informal_negocio",
                descreve_interacao_de_tela=0.9,
                tem_copy_de_interface=0.9,
                menciona_debito_tecnico=0.9,
            )
        )
        self.assertEqual(
            sorted(s["skill"] for s in r["tambem_considerar"]),
            [
                "especificar-debitos-tecnicos",
                "especificar-telas-ux-ui",
                "revisar-textos-requisitos",
            ],
        )

    def test_sinal_acima_do_limiar_de_rota_mas_abaixo_do_de_companheira_nao_sugere(self) -> None:
        meio = (MODULE.LIMIAR_NOUL + MODULE.LIMIAR_COMPANHEIRA) / 2
        r = MODULE.rotear(respostas("pedido_informal_negocio", descreve_interacao_de_tela=meio))
        self.assertEqual(r["tambem_considerar"], [])

    def test_id_de_demanda_admite_companheiras(self) -> None:
        """A rota da Demanda está em TIPOS_COM_ANALISES: com conteúdo colado junto
        ao ID, as análises são sugeridas normalmente."""
        self.assertIn("id_demanda_azure_boards", MODULE.TIPOS_COM_ANALISES)
        r = MODULE.rotear(respostas("id_demanda_azure_boards", tem_copy_de_interface=0.9))
        self.assertEqual(
            [s["skill"] for s in r["tambem_considerar"]], ["revisar-textos-requisitos"]
        )

    def test_nao_sugere_debito_quando_o_material_ja_e_um_debito(self) -> None:
        r = MODULE.rotear(respostas("debito_tecnico", menciona_debito_tecnico=0.99))
        self.assertEqual(r["tambem_considerar"], [])

    def test_backlog_nao_recebe_sugestao_de_analise(self) -> None:
        r = MODULE.rotear(
            respostas(
                "backlog_markdown", descreve_interacao_de_tela=0.99, tem_copy_de_interface=0.99
            )
        )
        self.assertEqual(r["tambem_considerar"], [])


class TestConfianca(unittest.TestCase):
    def test_confianca_baixa_devolve_a_decisao_para_a_pessoa(self) -> None:
        r = MODULE.rotear(respostas("spec_escrita", confianca=MODULE.LIMIAR_CONFIANCA - 0.01))
        self.assertTrue(r["decidir_com_a_pessoa"])
        self.assertTrue(r["alternativas"])

    def test_confianca_alta_decide_sozinha(self) -> None:
        r = MODULE.rotear(respostas("spec_escrita", confianca=MODULE.LIMIAR_CONFIANCA + 0.01))
        self.assertFalse(r["decidir_com_a_pessoa"])
        self.assertEqual(r["alternativas"], [])

    def test_confianca_baixa_ainda_assim_indica_a_rota_mais_provavel(self) -> None:
        """Confiança baixa muda quem decide, não invalida o julgamento."""
        r = MODULE.rotear(respostas("debito_tecnico", confianca=0.3))
        self.assertEqual(r["skill"], "especificar-debitos-tecnicos")


if __name__ == "__main__":
    unittest.main()

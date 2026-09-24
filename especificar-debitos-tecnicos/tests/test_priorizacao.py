"""Testes da priorização de débitos, sem rede.

Cobrem a tradução das respostas do Jev nas notas da skill, a fórmula de prioridade
e a detecção de inversões. A qualidade do julgamento é medida à parte, por
`scripts/avaliar_priorizacao.py`, que chama a API real.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "priorizacao.py"
SPEC = importlib.util.spec_from_file_location("priorizacao", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def respostas(
    impacto: float,
    risco: float,
    esforco: float,
    *,
    categoria: str = "codigo",
    defeito: float = 0.0,
    confianca: float = 0.8,
) -> dict[str, Any]:
    """Monta respostas do Jev. Os scores são 0-indexados, como a API devolve.

    `risco` é informado como a nota combinada desejada (0..4); a probabilidade e a
    severidade são derivadas dela pela raiz, já que a matriz é o produto normalizado.
    """
    lado_p = (risco / 4) ** 0.5 * (len(MODULE.PROBABILIDADE) - 1)
    lado_s = (risco / 4) ** 0.5 * (len(MODULE.SEVERIDADE) - 1)
    saida: dict[str, Any] = {
        d: {"type": "score", "score": v, "confidence": confianca, "probabilities": {}}
        for d, v in (
            ("impacto", impacto),
            ("probabilidade", lado_p),
            ("severidade", lado_s),
            ("esforco", esforco),
        )
    }
    saida["categoria"] = {"type": "choice", "choice": categoria, "confidence": 0.9}
    saida["ha_defeito_observavel"] = {"type": "noul", "noul": defeito}
    return saida


class TestConversaoDeNota(unittest.TestCase):
    def test_score_zero_vira_nota_um(self) -> None:
        r = MODULE.priorizar(respostas(0.0, 0.0, 0.0))
        self.assertEqual((r["impacto"], r["risco"], r["esforco"]), (1, 1, 1))

    def test_score_maximo_vira_nota_cinco(self) -> None:
        r = MODULE.priorizar(respostas(4.0, 4.0, 4.0))
        self.assertEqual((r["impacto"], r["risco"], r["esforco"]), (5, 5, 5))

    def test_score_fracionario_arredonda_para_o_nivel_mais_proximo(self) -> None:
        self.assertEqual(MODULE.priorizar(respostas(2.4, 0, 0))["impacto"], 3)
        self.assertEqual(MODULE.priorizar(respostas(2.6, 0, 0))["impacto"], 4)

    def test_nota_fica_sempre_no_intervalo_da_skill(self) -> None:
        for valor in (0.0, 1.3, 2.5, 3.9, 4.0):
            with self.subTest(valor=valor):
                nota = MODULE.priorizar(respostas(valor, valor, valor))["impacto"]
                self.assertGreaterEqual(nota, 1)
                self.assertLessEqual(nota, 5)


class TestFormulaDePrioridade(unittest.TestCase):
    def test_usa_a_formula_da_skill(self) -> None:
        # I=4, R=3, E=2  ->  (4 + 3) * (6 - 2) = 28
        r = MODULE.priorizar(respostas(3.0, 2.0, 1.0))
        self.assertEqual(r["prioridade"], 28)

    def test_menor_esforco_produz_maior_prioridade(self) -> None:
        barato = MODULE.priorizar(respostas(2.0, 2.0, 0.0))
        caro = MODULE.priorizar(respostas(2.0, 2.0, 4.0))
        self.assertGreater(barato["prioridade"], caro["prioridade"])

    def test_extremos_da_escala(self) -> None:
        self.assertEqual(MODULE.priorizar(respostas(0.0, 0.0, 4.0))["prioridade"], 2)
        self.assertEqual(MODULE.priorizar(respostas(4.0, 4.0, 0.0))["prioridade"], 50)


class TestTipoECategoria(unittest.TestCase):
    def test_defeito_observavel_sugere_bug(self) -> None:
        self.assertEqual(MODULE.priorizar(respostas(2, 2, 2, defeito=0.9))["tipo_sugerido"], "Bug")

    def test_ausencia_de_defeito_sugere_user_story(self) -> None:
        r = MODULE.priorizar(respostas(2, 2, 2, defeito=0.1))
        self.assertEqual(r["tipo_sugerido"], "User Story")

    def test_categoria_sai_com_o_rotulo_da_skill(self) -> None:
        for chave, rotulo in MODULE.ROTULO_DA_CATEGORIA.items():
            with self.subTest(categoria=chave):
                r = MODULE.priorizar(respostas(2, 2, 2, categoria=chave))
                self.assertEqual(r["categoria"], rotulo)

    def test_as_categorias_cobrem_exatamente_as_seis_da_skill(self) -> None:
        self.assertEqual(set(MODULE.CATEGORIAS), set(MODULE.ROTULO_DA_CATEGORIA))
        self.assertEqual(len(MODULE.CATEGORIAS), 6)


class TestMatrizDeRisco(unittest.TestCase):
    """Risco é probabilidade × severidade, normalizado — não uma escala única.

    A escala única puxava para cima na ponta baixa, com confiança de 0,38 a 0,60,
    que é o sintoma de pergunta multidimensional.
    """

    def _resp(self, prob: float, sev: float) -> dict[str, Any]:
        """prob e sev em fração de 0 a 1 da própria escala."""
        r = respostas(2.0, 2.0, 2.0)
        prob *= len(MODULE.PROBABILIDADE) - 1
        sev *= len(MODULE.SEVERIDADE) - 1
        r["probabilidade"]["score"] = prob
        r["severidade"]["score"] = sev
        return r

    def test_probabilidade_e_severidade_maximas_dao_risco_maximo(self) -> None:
        self.assertEqual(MODULE.priorizar(self._resp(1.0, 1.0))["risco"], 5)

    def test_probabilidade_nula_zera_o_risco_por_mais_grave_que_seja(self) -> None:
        self.assertEqual(MODULE.priorizar(self._resp(0.0, 1.0))["risco"], 1)

    def test_frequente_e_cosmetico_permanece_baixo(self) -> None:
        self.assertEqual(MODULE.priorizar(self._resp(1.0, 0.0))["risco"], 1)

    def test_raro_e_catastrofico_supera_frequente_e_leve(self) -> None:
        raro_grave = MODULE.priorizar(self._resp(0.25, 1.0))["risco"]
        frequente_leve = MODULE.priorizar(self._resp(1.0, 0.125))["risco"]
        self.assertGreater(raro_grave, frequente_leve)

    def test_risco_fica_sempre_no_intervalo_da_skill(self) -> None:
        for prob in (0.0, 0.4, 0.6, 1.0):
            for sev in (0.0, 0.4, 0.6, 1.0):
                with self.subTest(prob=prob, sev=sev):
                    nota = MODULE.priorizar(self._resp(prob, sev))["risco"]
                    self.assertGreaterEqual(nota, 1)
                    self.assertLessEqual(nota, 5)


class TestNiveis(unittest.TestCase):
    def test_cada_dimensao_tem_o_numero_de_niveis_que_consegue_descrever(self) -> None:
        """O número de níveis de cada dimensão é interno; a nota de Risco que a skill
        pede continua de 1 a 5. Reduzir probabilidade a quatro foi testado e não
        melhorou a retranslação, então a escala permaneceu em cinco."""
        for nome, niveis, esperado in (
            ("impacto", MODULE.IMPACTO, 5),
            ("probabilidade", MODULE.PROBABILIDADE, 5),
            ("severidade", MODULE.SEVERIDADE, 5),
            ("esforco", MODULE.ESFORCO, 5),
        ):
            with self.subTest(dimensao=nome):
                self.assertEqual(len(niveis), esperado)
                self.assertGreaterEqual(len(niveis), 2)
                self.assertLessEqual(len(niveis), 10)

    def test_escalas_de_comprimento_diferente_nao_enviesam_o_risco(self) -> None:
        """Cada escala normaliza pelo próprio máximo, valha ou não o mesmo comprimento.

        Hoje as duas têm cinco níveis, então o erro ficaria dormente: dividir ambas pelo
        mesmo número só enviesa quando os comprimentos divergem. O teste fixa a
        propriedade para que uma mudança futura de comprimento não passe em silêncio.
        """
        r = respostas(2.0, 2.0, 2.0)
        r["probabilidade"]["score"] = float(len(MODULE.PROBABILIDADE) - 1)
        r["severidade"]["score"] = float(len(MODULE.SEVERIDADE) - 1)
        self.assertEqual(MODULE.priorizar(r)["risco"], MODULE.NOTAS_DA_SKILL)

        r["severidade"]["score"] = 0.0
        self.assertEqual(MODULE.priorizar(r)["risco"], 1)

    def test_niveis_descrevem_situacoes_e_nao_graus(self) -> None:
        """A doc do primitivo score é explícita: nível descrito como grau ou número
        degrada o julgamento.

        A busca usa fronteira de palavra: `nível` como substring casaria dentro de
        `indisponível`, que é situação concreta e legítima.
        """
        proibidos = ("baixo", "médio", "alto", "moderado", "grave", "nível", "severo")
        for niveis in (
            MODULE.IMPACTO,
            MODULE.PROBABILIDADE,
            MODULE.SEVERIDADE,
            MODULE.ESFORCO,
        ):
            for nivel in niveis:
                with self.subTest(nivel=nivel[:40]):
                    self.assertFalse(nivel.strip()[0].isdigit())
                    for termo in proibidos:
                        self.assertIsNone(
                            re.search(rf"\b{termo}\b", nivel.lower()),
                            f"{termo!r} usado como grau em {nivel!r}",
                        )


class TestOrdenacaoEInversoes(unittest.TestCase):
    def test_ordena_por_prioridade_decrescente(self) -> None:
        itens = [
            MODULE.priorizar(respostas(0.0, 0.0, 4.0)),  # prioridade 2
            MODULE.priorizar(respostas(4.0, 4.0, 0.0)),  # prioridade 50
        ]
        self.assertEqual([i["prioridade"] for i in MODULE.ordenar(itens)], [50, 2])

    def test_desempata_pelo_score_cru_quando_a_prioridade_empata(self) -> None:
        a = MODULE.priorizar(respostas(2.0, 2.0, 2.0))
        b = MODULE.priorizar(respostas(2.4, 2.4, 2.0))
        self.assertEqual(a["prioridade"], b["prioridade"])
        self.assertEqual(MODULE.ordenar([a, b])[0]["desempate"], b["desempate"])

    def test_sinaliza_quando_o_esforco_inverte_a_ordem_de_impacto(self) -> None:
        trivial_e_barato = MODULE.priorizar(respostas(1.0, 1.0, 0.0))  # I2 R2 E1 -> 20
        grave_e_caro = MODULE.priorizar(respostas(4.0, 4.0, 4.0))  # I5 R5 E5 -> 10
        inversoes = MODULE.sinalizar_inversoes([trivial_e_barato, grave_e_caro])
        self.assertEqual(len(inversoes), 1)
        self.assertEqual(inversoes[0]["acima"]["impacto"], 2)
        self.assertEqual(inversoes[0]["abaixo"]["impacto"], 5)

    def test_nao_sinaliza_quando_a_ordem_respeita_o_impacto(self) -> None:
        alto = MODULE.priorizar(respostas(4.0, 4.0, 0.0))
        baixo = MODULE.priorizar(respostas(0.0, 0.0, 4.0))
        self.assertEqual(MODULE.sinalizar_inversoes([alto, baixo]), [])


if __name__ == "__main__":
    unittest.main()


class TestFaixas(unittest.TestCase):
    """O portão de severidade: itens intoleráveis saem da fila de eficiência.

    A fórmula da skill é uma métrica de eficiência, e favorecer ganho barato é o que ela
    serve para fazer — por isso um item grave e caro afunda nela. Trocá-la por WSJF não
    resolve, porque o WSJF também é métrica de eficiência. A correção é classificar antes
    de ordenar.
    """

    def _item(self, prob: int, sev: int, *, conf: float = 0.9, esforco: int = 1) -> dict[str, Any]:
        r = respostas(2.0, 2.0, float(esforco - 1), confianca=conf)
        r["probabilidade"]["score"] = float(prob - 1)
        r["severidade"]["score"] = float(sev - 1)
        return MODULE.priorizar(r)

    def test_severidade_alta_com_probabilidade_real_vira_restricao(self) -> None:
        self.assertEqual(MODULE.faixa(self._item(prob=3, sev=5)), "restricao")

    def test_esforco_maximo_nao_tira_um_item_da_faixa_de_restricao(self) -> None:
        """É o defeito que o portão existe para corrigir."""
        self.assertTrue(MODULE.e_restricao(self._item(prob=3, sev=5, esforco=5)))

    def test_severidade_alta_com_probabilidade_no_piso_nao_e_restricao(self) -> None:
        """É faixa, não linha: sem caminho conhecido para ocorrer, não é obrigatório."""
        self.assertEqual(MODULE.faixa(self._item(prob=1, sev=5)), "candidato")

    def test_severidade_baixa_nunca_e_restricao(self) -> None:
        self.assertEqual(MODULE.faixa(self._item(prob=5, sev=2)), "candidato")

    def test_confianca_insuficiente_na_severidade_adia_a_classificacao(self) -> None:
        conf = MODULE.CONFIANCA_MINIMA_PARA_FAIXA - 0.01
        self.assertEqual(MODULE.faixa(self._item(prob=3, sev=5, conf=conf)), "a_confirmar")

    def test_confianca_insuficiente_adia_mesmo_quando_a_severidade_e_baixa(self) -> None:
        """A pendência é sobre não saber, não sobre ser grave."""
        conf = MODULE.CONFIANCA_MINIMA_PARA_FAIXA - 0.01
        self.assertEqual(MODULE.faixa(self._item(prob=1, sev=1, conf=conf)), "a_confirmar")

    def test_separar_em_faixas_distribui_e_nao_perde_item(self) -> None:
        itens = [
            self._item(prob=3, sev=5),
            self._item(prob=5, sev=2),
            self._item(prob=3, sev=5, conf=0.2),
        ]
        faixas = MODULE.separar_em_faixas(itens)
        self.assertEqual(len(faixas["restricoes"]), 1)
        self.assertEqual(len(faixas["candidatos"]), 1)
        self.assertEqual(len(faixas["a_confirmar"]), 1)
        self.assertEqual(sum(len(v) for v in faixas.values()), len(itens))

    def test_restricoes_saem_por_gravidade_e_nao_por_eficiencia(self) -> None:
        barato = self._item(prob=3, sev=4, esforco=1)
        caro_e_pior = self._item(prob=5, sev=5, esforco=5)
        ordem = MODULE.separar_em_faixas([barato, caro_e_pior])["restricoes"]
        self.assertGreater(ordem[0]["risco"], ordem[1]["risco"])
        self.assertLess(ordem[0]["prioridade"], ordem[1]["prioridade"])

    def test_candidatos_seguem_a_formula_da_skill(self) -> None:
        a = self._item(prob=5, sev=2, esforco=1)
        b = self._item(prob=5, sev=2, esforco=5)
        candidatos = MODULE.separar_em_faixas([b, a])["candidatos"]
        self.assertEqual(candidatos[0]["prioridade"], max(a["prioridade"], b["prioridade"]))

"""Testes do gate 3W, sem rede.

Testa a tradução das respostas do Jev no contrato de entrega do 3W. A qualidade do
julgamento é medida à parte por `scripts/avaliar_gate_3w.py`, que chama a API real.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "gate_3w.py"
SPEC = importlib.util.spec_from_file_location("gate_3w", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def respostas(who: str, what: str, why: str, confianca: float = 0.9) -> dict[str, Any]:
    return {
        w: {
            "type": "choice",
            "choice": estado,
            "confidence": confianca,
            "probabilities": {estado: confianca},
        }
        for w, estado in (("who", who), ("what", what), ("why", why))
    }


class TestAplicarGate(unittest.TestCase):
    def test_tres_ws_confirmados_resultam_em_completo(self) -> None:
        r = MODULE.aplicar_gate(respostas("confirmado", "confirmado", "confirmado"))
        self.assertEqual(r["estado_3w"], "Completo")

    def test_um_w_fraco_ja_torna_o_estado_incompleto(self) -> None:
        for posicao in range(3):
            estados = ["confirmado"] * 3
            estados[posicao] = "fraco"
            with self.subTest(posicao=posicao):
                r = MODULE.aplicar_gate(respostas(*estados))
                self.assertEqual(r["estado_3w"], "Incompleto")

    def test_um_w_pendente_ja_torna_o_estado_incompleto(self) -> None:
        r = MODULE.aplicar_gate(respostas("confirmado", "confirmado", "pendente"))
        self.assertEqual(r["estado_3w"], "Incompleto")

    def test_preserva_estado_confianca_e_distribuicao_por_w(self) -> None:
        r = MODULE.aplicar_gate(respostas("confirmado", "fraco", "pendente", confianca=0.42))
        self.assertEqual(r["ws"]["who"]["estado"], "confirmado")
        self.assertEqual(r["ws"]["what"]["estado"], "fraco")
        self.assertEqual(r["ws"]["why"]["estado"], "pendente")
        self.assertEqual(r["ws"]["who"]["confianca"], 0.42)
        self.assertIn("pendente", r["ws"]["why"]["probabilidades"])

    def test_menor_confianca_e_a_do_w_mais_incerto(self) -> None:
        entrada = respostas("confirmado", "confirmado", "confirmado")
        entrada["what"]["confidence"] = 0.31
        r = MODULE.aplicar_gate(entrada)
        self.assertAlmostEqual(r["menor_confianca"], 0.31)

    def test_confianca_baixa_nao_altera_o_estado_do_gate(self) -> None:
        """O gate é determinístico: confiança informa a pessoa, não muda a regra."""
        entrada = respostas("confirmado", "confirmado", "confirmado", confianca=0.05)
        self.assertEqual(MODULE.aplicar_gate(entrada)["estado_3w"], "Completo")


class TestMontarState(unittest.TestCase):
    def test_sem_contexto_envia_apenas_a_historia(self) -> None:
        self.assertEqual(MODULE.montar_state("Como X, quero Y."), {"historia": "Como X, quero Y."})

    def test_com_contexto_envia_campo_separado(self) -> None:
        state = MODULE.montar_state("Como X, quero Y.", "A área confirmou o prazo.")
        self.assertEqual(state["contexto_confirmado"], "A área confirmou o prazo.")


class TestPerguntas(unittest.TestCase):
    def test_ha_uma_pergunta_choice_por_w(self) -> None:
        self.assertEqual(set(MODULE.PERGUNTAS), {"who", "what", "why"})
        for pergunta in MODULE.PERGUNTAS.values():
            self.assertEqual(pergunta["type"], "choice")

    def test_cada_pergunta_oferece_os_tres_estados_do_gate(self) -> None:
        for w, pergunta in MODULE.PERGUNTAS.items():
            with self.subTest(w=w):
                self.assertEqual(set(pergunta["criteria"]), {"confirmado", "fraco", "pendente"})


if __name__ == "__main__":
    unittest.main()

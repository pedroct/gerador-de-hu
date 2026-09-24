"""Testes do cliente da Decisions API, sem rede.

O abridor da requisição é injetável, então dá para verificar o que sai no corpo e nos
cabeçalhos sem chamar o OpenRouter.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cliente_jev.py"
SPEC = importlib.util.spec_from_file_location("cliente_jev", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RespostaFalsa:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._corpo = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._corpo

    def __enter__(self) -> RespostaFalsa:
        return self

    def __exit__(self, *_: object) -> None:
        return None


class AbridorFalso:
    """Captura a requisição e devolve uma resposta pronta."""

    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self.payload = payload if payload is not None else {"answers": {}}
        self.requisicao: Any = None
        self.timeout: float | None = None

    def __call__(self, requisicao: Any, timeout: float | None = None) -> RespostaFalsa:
        self.requisicao = requisicao
        self.timeout = timeout
        return RespostaFalsa(self.payload)


class TestDecidir(unittest.TestCase):
    def _chamar(self, abridor: AbridorFalso) -> dict[str, Any]:
        resultado: dict[str, Any] = MODULE.decidir(
            {"material": "texto"},
            {"p": {"type": "noul", "instructions": "?"}},
            "sk-or-v1-fake",
            abrir=abridor,
        )
        return resultado

    def test_envia_modelo_state_e_questions_no_corpo(self) -> None:
        abridor = AbridorFalso()
        self._chamar(abridor)
        corpo = json.loads(abridor.requisicao.data.decode("utf-8"))
        self.assertEqual(corpo["model"], MODULE.MODELO)
        self.assertEqual(corpo["state"], {"material": "texto"})
        self.assertIn("p", corpo["questions"])

    def test_envia_a_chave_como_bearer(self) -> None:
        abridor = AbridorFalso()
        self._chamar(abridor)
        cabecalhos = {k.lower(): v for k, v in abridor.requisicao.header_items()}
        self.assertEqual(cabecalhos["authorization"], "Bearer sk-or-v1-fake")
        self.assertEqual(cabecalhos["content-type"], "application/json")

    def test_usa_post_no_endpoint_da_decisions_api(self) -> None:
        abridor = AbridorFalso()
        self._chamar(abridor)
        self.assertEqual(abridor.requisicao.get_method(), "POST")
        self.assertEqual(abridor.requisicao.full_url, MODULE.ENDPOINT)

    def test_nao_escapa_acentos_no_corpo(self) -> None:
        """As perguntas e o material são em português; escapar inflaria o payload."""
        abridor = AbridorFalso()
        MODULE.decidir({"material": "ação"}, {}, "k", abrir=abridor)
        self.assertIn("ação".encode(), abridor.requisicao.data)

    def test_devolve_a_resposta_desserializada(self) -> None:
        abridor = AbridorFalso({"answers": {"p": {"type": "noul", "noul": 0.9}}})
        self.assertEqual(self._chamar(abridor)["answers"]["p"]["noul"], 0.9)

    def test_aplica_timeout(self) -> None:
        abridor = AbridorFalso()
        self._chamar(abridor)
        self.assertEqual(abridor.timeout, MODULE.TIMEOUT_SEGUNDOS)

    def test_erro_http_vira_mensagem_com_codigo_e_corpo(self) -> None:
        def abridor_com_erro(*_: object, **__: object) -> None:
            raise urllib.error.HTTPError(
                MODULE.ENDPOINT,
                402,
                "Payment Required",
                {},
                None,  # type: ignore[arg-type]
            )

        with self.assertRaises(RuntimeError) as ctx:
            MODULE.decidir({}, {}, "k", abrir=abridor_com_erro)
        self.assertIn("402", str(ctx.exception))


class TestCarregarChave(unittest.TestCase):
    def test_prefere_a_variavel_de_ambiente(self) -> None:
        import os

        anterior = os.environ.get("JEV_OPENROUTER_API")
        os.environ["JEV_OPENROUTER_API"] = "sk-or-v1-do-ambiente"
        try:
            self.assertEqual(MODULE.carregar_chave(), "sk-or-v1-do-ambiente")
        finally:
            if anterior is None:
                del os.environ["JEV_OPENROUTER_API"]
            else:
                os.environ["JEV_OPENROUTER_API"] = anterior


if __name__ == "__main__":
    unittest.main()

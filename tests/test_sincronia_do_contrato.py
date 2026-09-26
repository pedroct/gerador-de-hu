"""Impede que a cópia canônica do contrato divirja da lógica das publicadoras.

As regras do contrato Markdown existem em três cópias: `validate_backlog.py`, que é o gate
que o passo 10 de `gerar-backlog-azure-boards/SKILL.md` manda rodar, e os
`contrato_backlog.py` das duas publicadoras gêmeas. A sincronia entre as duas publicadoras
já é medida dentro da skill de Demanda (`test_sincronia_com_origem.py`); o que faltava era
medir a terceira, e foi exatamente ela que ficou atrás quando `Tags`, `Depende de` e
`Azure Boards ID` entraram no contrato — o mesmo `SKILL.md` mandava emitir os campos e, dez
linhas abaixo, rodar o gate que os recusava.

A comparação é de texto, não de comportamento, porque é a única que não pode passar por
acaso: o trecho espelhado tem de ser byte a byte o corpo de `contrato_backlog.py`.
"""

from __future__ import annotations

import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
VALIDADOR = RAIZ / "gerar-backlog-azure-boards" / "scripts" / "validate_backlog.py"
CONTRATO = (
    RAIZ
    / "publicar-backlog-azure-boards"
    / "src"
    / "publicar_backlog_azure_boards"
    / "contrato_backlog.py"
)
INICIO = "# --- início do trecho espelhado de contrato_backlog.py ---"
FIM = "# --- fim do trecho espelhado de contrato_backlog.py ---"
# O corpo compartilhado começa no primeiro símbolo depois dos imports de `contrato_backlog`.
PRIMEIRO_SIMBOLO = "ITEM_RE = re.compile("


class SincroniaDoContratoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validador = VALIDADOR.read_text(encoding="utf-8")
        self.contrato = CONTRATO.read_text(encoding="utf-8")

    def test_validador_canonico_delimita_o_trecho_espelhado(self) -> None:
        self.assertIn(INICIO, self.validador)
        self.assertIn(FIM, self.validador)

    def test_trecho_espelhado_e_identico_ao_contrato_da_publicadora(self) -> None:
        espelhado = self.validador.split(INICIO, 1)[1].split(FIM, 1)[0].strip("\n")
        esperado = self.contrato[self.contrato.index(PRIMEIRO_SIMBOLO) :].strip("\n")
        self.assertEqual(
            esperado,
            espelhado,
            "O gate canônico divergiu de contrato_backlog.py. Reespelhe o trecho por "
            "substituição mecânica em vez de editá-lo à mão.",
        )


if __name__ == "__main__":
    unittest.main()

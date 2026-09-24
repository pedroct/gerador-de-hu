"""Impede que o README aponte para caminhos que nao existem.

O repositorio ja testa a contagem de capacidades contra a propria lista, pelo mesmo
motivo: documentacao diverge em silencio, e aqui ela e a interface de quem instala as
skills em outro projeto.
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def scripts_invocados() -> set[str]:
    """Scripts citados no README, resolvidos no `cd` vigente do bloco de codigo.

    Varios blocos comecam com `cd <skill>` e invocam `scripts/...` relativo a ela, entao
    procurar o caminho sempre a partir da raiz daria falso negativo.
    """
    achados: set[str] = set()
    dentro_do_bloco = False
    cwd = Path(".")
    for linha in README.splitlines():
        if linha.startswith("```"):
            dentro_do_bloco = not dentro_do_bloco
            if dentro_do_bloco:
                cwd = Path(".")
            continue
        if not dentro_do_bloco:
            continue
        mudou = re.match(r"\s*cd\s+(\S+)", linha)
        if mudou:
            cwd = Path(os.path.normpath(cwd / mudou.group(1)))
            continue
        invocado = re.search(r"uv run python (\S+\.py)", linha)
        if invocado:
            caminho = invocado.group(1)
            if caminho.startswith("/"):
                continue  # ferramenta externa, fora do repositorio
            achados.add(os.path.normpath(cwd / caminho))
    return achados


class TestCaminhosCitados(unittest.TestCase):
    def test_todo_script_invocado_existe(self) -> None:
        invocados = scripts_invocados()
        self.assertTrue(invocados, "o README deve citar ao menos um script")
        for relativo in sorted(invocados):
            with self.subTest(script=relativo):
                self.assertTrue((ROOT / relativo).is_file(), f"{relativo} nao existe")

    def test_todo_link_relativo_existe(self) -> None:
        links = set(re.findall(r"\]\((?!https?://|#)([^)#]+)\)", README))
        self.assertTrue(links, "o README deve ter links relativos")
        for relativo in sorted(links):
            with self.subTest(link=relativo):
                self.assertTrue((ROOT / relativo).exists(), f"{relativo} nao existe")

    def test_toda_skill_da_tabela_tem_diretorio(self) -> None:
        nomes = set(re.findall(r"\| \[`([a-z0-9-]+)`\]\(", README))
        self.assertGreaterEqual(len(nomes), 12)
        for nome in sorted(nomes):
            with self.subTest(skill=nome):
                self.assertTrue((ROOT / nome / "SKILL.md").is_file())


class TestCoerenciaComOContrato(unittest.TestCase):
    def test_exemplo_minimo_traz_a_demanda_de_origem(self) -> None:
        """O exemplo do README e o contrato do backlog precisam concordar."""
        contrato = (
            ROOT / "gerar-backlog-azure-boards" / "references" / "backlog-markdown-contract.md"
        ).read_text(encoding="utf-8")
        campo = "Demanda de Negócio de origem"
        self.assertIn(campo, contrato)
        self.assertIn(campo, README)

    def test_documenta_que_update_nao_traz_skills_novas(self) -> None:
        self.assertIn("update` não traz skills novas", README)
        self.assertIn("--skill '*' -a '*'", README)

    def test_nao_recomenda_update_como_sincronizacao(self) -> None:
        """`update` so ressincroniza o que ja esta no lock."""
        self.assertIn("Use-o como sincronização periódica, não o `update`", README)

    def test_lista_de_testes_nao_repete_pacote(self) -> None:
        comandos = re.findall(r"uv run pytest (\S+) -v", README)
        self.assertEqual(sorted(comandos), sorted(set(comandos)), "pacote repetido")


if __name__ == "__main__":
    unittest.main()

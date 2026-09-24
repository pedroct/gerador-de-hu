"""Testes do verificador de skills instaladas, sem rede.

O script existe por causa de duas armadilhas do `npx skills`: `update` nao traz skills
novas, e `add -a claude-code` instala como copia em vez de symlink. Os testes abaixo
montam projetos de mentira com cada uma dessas situacoes.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verificar_skills_instaladas.py"
SPEC = importlib.util.spec_from_file_location("verificar_skills_instaladas", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def montar_projeto(
    base: Path,
    canonicas: list[str],
    *,
    no_lock: list[str] | None = None,
    copias: dict[str, str] | None = None,
) -> Path:
    """Monta um projeto com o layout canonico: .agents/skills + symlinks por agente."""
    agents = base / ".agents" / "skills"
    agents.mkdir(parents=True)
    claude = base / ".claude" / "skills"
    claude.mkdir(parents=True)

    for nome in canonicas:
        (agents / nome).mkdir()
        (agents / nome / "SKILL.md").write_text("x", encoding="utf-8")
        (claude / nome).symlink_to(Path("../..") / ".agents" / "skills" / nome)

    for nome, agente in (copias or {}).items():
        destino = base / agente / nome
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "SKILL.md").write_text("x", encoding="utf-8")

    listadas = canonicas if no_lock is None else no_lock
    (base / "skills-lock.json").write_text(
        json.dumps({"version": 1, "skills": {n: {} for n in listadas}}), encoding="utf-8"
    )
    return base


class TestDeteccao(unittest.TestCase):
    def test_skills_do_repositorio_sao_os_diretorios_com_skill_md(self) -> None:
        skills = MODULE.skills_do_repositorio()
        self.assertIn("orquestrar-skills-de-requisito", skills)
        self.assertIn("gerar-backlog-azure-boards", skills)
        self.assertNotIn("scripts", skills)
        self.assertNotIn("tests", skills)

    def test_detecta_skill_nova_que_o_update_nao_traria(self) -> None:
        with TemporaryDirectory() as tmp:
            projeto = montar_projeto(Path(tmp), ["refinar-historias-3w"])
            instaladas = MODULE.instaladas_no_canonico(projeto)
            faltando = MODULE.skills_do_repositorio() - instaladas
            self.assertIn("orquestrar-skills-de-requisito", faltando)

    def test_le_o_lock_quando_existe(self) -> None:
        with TemporaryDirectory() as tmp:
            projeto = montar_projeto(Path(tmp), ["refinar-historias-3w"])
            self.assertEqual(MODULE.skills_no_lock(projeto), {"refinar-historias-3w"})

    def test_projeto_sem_lock_nao_quebra(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(MODULE.skills_no_lock(Path(tmp)), set())

    def test_projeto_sem_agents_nao_quebra(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(MODULE.instaladas_no_canonico(Path(tmp)), set())


class TestCopias(unittest.TestCase):
    def test_symlink_no_layout_canonico_nao_e_apontado(self) -> None:
        with TemporaryDirectory() as tmp:
            projeto = montar_projeto(Path(tmp), ["refinar-historias-3w"])
            nossas = MODULE.skills_do_repositorio()
            self.assertEqual(MODULE.copias_fora_do_canonico(projeto, nossas), [])

    def test_copia_de_skill_nossa_e_apontada(self) -> None:
        """Foi o que aconteceu ao instalar com `-a claude-code`."""
        with TemporaryDirectory() as tmp:
            projeto = montar_projeto(
                Path(tmp),
                ["refinar-historias-3w"],
                copias={"orquestrar-skills-de-requisito": ".claude/skills"},
            )
            nossas = MODULE.skills_do_repositorio()
            achados = MODULE.copias_fora_do_canonico(projeto, nossas)
            self.assertEqual(achados, [".claude/skills/orquestrar-skills-de-requisito"])

    def test_copia_de_skill_de_outra_origem_e_ignorada(self) -> None:
        """O projeto pode instalar skills de outros repositorios; nao e assunto daqui."""
        with TemporaryDirectory() as tmp:
            projeto = montar_projeto(
                Path(tmp), ["refinar-historias-3w"], copias={"graphify": ".codex/skills"}
            )
            nossas = MODULE.skills_do_repositorio()
            self.assertEqual(MODULE.copias_fora_do_canonico(projeto, nossas), [])


class TestComandoDeSincronizacao(unittest.TestCase):
    def test_usa_add_com_curinga_e_nunca_update(self) -> None:
        """`update` so ressincroniza o que ja esta no lock; nao traz skill nova."""
        self.assertIn("add", MODULE.COMANDO_SYNC)
        self.assertNotIn("update", MODULE.COMANDO_SYNC)

    def test_instala_para_todos_os_agentes(self) -> None:
        """Sem `-a '*'` a skill vira copia so no agente escolhido."""
        self.assertEqual(MODULE.COMANDO_SYNC[-3:], ["-a", "*", "-y"])

    def test_usa_curinga_de_skill_porque_nomes_separados_por_virgula_nao_instalam(
        self,
    ) -> None:
        self.assertIn("--skill", MODULE.COMANDO_SYNC)
        indice = MODULE.COMANDO_SYNC.index("--skill")
        self.assertEqual(MODULE.COMANDO_SYNC[indice + 1], "*")


if __name__ == "__main__":
    unittest.main()

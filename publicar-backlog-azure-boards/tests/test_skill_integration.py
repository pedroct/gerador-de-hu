from __future__ import annotations

import importlib
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
for caminho in (RAIZ / "src", RAIZ / "scripts"):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

_modelos = importlib.import_module("publicar_backlog_azure_boards.modelos")
_publicar_backlog = importlib.import_module("publicar_backlog")
ConfiguracaoPublicacao = _modelos.ConfiguracaoPublicacao
OperacaoCriacao = _modelos.OperacaoCriacao
RegistroManifesto = _modelos.RegistroManifesto
principal = _publicar_backlog.principal


ROOT = RAIZ
BACKLOG = ROOT / "tests" / "fixtures" / "valid-backlog.md"
CONFIGURACAO = ConfiguracaoPublicacao("organizacao", "projeto", "Projeto", r"Projeto\Sprint 18")


class ClienteFalso:
    def __init__(self) -> None:
        self.configuracao = CONFIGURACAO
        self.chaves_criadas: list[str] = []

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> None:
        assert configuracao == CONFIGURACAO

    def validar_operacao(self, operacao: OperacaoCriacao) -> None:
        del operacao

    def criar_item(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> RegistroManifesto:
        del id_pai
        chave = operacao.chave
        self.chaves_criadas.append(chave)
        return RegistroManifesto(len(self.chaves_criadas), operacao.tipo, chave)


def test_simulacao_nao_chama_criacao(capsys) -> None:
    cliente = ClienteFalso()

    codigo = principal(["publicar", str(BACKLOG), "--simulacao"], cliente=cliente)

    assert codigo == 0
    assert cliente.chaves_criadas == []
    assert "Simulação" in capsys.readouterr().out


def test_skill_declara_confirmacao_antes_de_escrita() -> None:
    texto = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "zero chamadas de criação" in texto
    assert "AUTORIZAR PUBLICAÇÃO" in texto


def test_skill_nao_chama_mcp_obrigatoriamente() -> None:
    texto = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "MCP" in texto
    assert "opcional" in texto

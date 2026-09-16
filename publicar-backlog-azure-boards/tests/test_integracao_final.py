from __future__ import annotations

from pathlib import Path

import pytest

from publicar_backlog_azure_boards.autorizacao import (
    criar_autorizacao,
    criar_frase_confirmacao,
)
from publicar_backlog_azure_boards.cli import principal
from publicar_backlog_azure_boards.executar_publicacao import executar_plano
from publicar_backlog_azure_boards.interpretar_markdown import interpretar_backlog
from publicar_backlog_azure_boards.manifesto import ler_manifesto
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    RegistroManifesto,
)
from publicar_backlog_azure_boards.planejar_publicacao import criar_plano


CONFIGURACAO = ConfiguracaoPublicacao(
    "organizacao", "Projeto", "Projeto", r"Projeto\Sprint 18"
)


@pytest.fixture
def backlog() -> Path:
    return Path(__file__).parent / "fixtures" / "valid-backlog.md"


@pytest.fixture
def cliente() -> ClienteSimulado:
    return ClienteSimulado()


class ClienteSimulado:
    def __init__(self) -> None:
        self.configuracao = CONFIGURACAO
        self.chaves_criadas: list[str] = []

    def criar_item(
        self, operacao: OperacaoCriacao, id_pai: int | None = None
    ) -> RegistroManifesto:
        if operacao.chave_pai is not None:
            assert id_pai is not None
        self.chaves_criadas.append(operacao.chave)
        return RegistroManifesto(
            id=len(self.chaves_criadas),
            tipo=operacao.tipo,
            url=f"https://exemplo/{operacao.chave}",
        )


def test_fluxo_completo_exige_confirmacao_e_grava_manifesto(
    tmp_path: Path, backlog: Path, cliente: ClienteSimulado
) -> None:
    assert principal(["publicar", str(backlog), "--simulacao"], cliente=cliente) == 0
    assert cliente.chaves_criadas == []

    plano = criar_plano(
        interpretar_backlog(backlog),
        cliente.configuracao,
    )
    autorizacao = criar_autorizacao(
        plano,
        criar_frase_confirmacao(plano, frozenset(op.chave for op in plano.operacoes)),
        frozenset(op.chave for op in plano.operacoes),
    )
    executar_plano(plano, autorizacao, cliente, tmp_path / "manifesto.json")

    assert set(ler_manifesto(tmp_path / "manifesto.json").itens) == {
        "1.0.0",
        "1.1.0",
        "1.1.1",
    }

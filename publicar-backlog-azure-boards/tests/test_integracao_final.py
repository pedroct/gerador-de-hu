from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest

from publicar_backlog_azure_boards.autorizacao import criar_frase_confirmacao
from publicar_backlog_azure_boards.cli import principal
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


    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> None:
        assert configuracao == self.configuracao

    def validar_operacao(self, operacao: OperacaoCriacao) -> None:
        del operacao


def test_publicacao_pela_cli_rejeita_confirmacao_invalida_sem_criacoes(
    tmp_path: Path, backlog: Path, cliente: ClienteSimulado
) -> None:
    manifesto = tmp_path / "manifesto-invalido.json"

    codigo = principal(
        ["publicar", str(backlog), "--manifesto", str(manifesto)],
        cliente=cliente,
        entrada=StringIO("1\nCONFIRMAÇÃO INCORRETA\n"),
        saida=StringIO(),
    )

    assert codigo == 2
    assert cliente.chaves_criadas == []


def test_publicacao_pela_cli_cria_itens_em_ordem_e_grava_manifesto_no_caminho_informado(
    tmp_path: Path, backlog: Path, cliente: ClienteSimulado
) -> None:
    plano = criar_plano(
        interpretar_backlog(backlog),
        cliente.configuracao,
    )
    caminho_manifesto = tmp_path / "subdiretorio" / "manifesto.json"
    confirmacao = criar_frase_confirmacao(
        plano, frozenset(op.chave for op in plano.operacoes)
    )

    codigo = principal(
        ["publicar", str(backlog), "--manifesto", str(caminho_manifesto)],
        cliente=cliente,
        entrada=StringIO(f"1\n{confirmacao}\n"),
        saida=StringIO(),
    )

    assert codigo == 0
    assert cliente.chaves_criadas == ["1.0.0", "1.1.0", "1.1.1"]
    assert list(ler_manifesto(caminho_manifesto).itens) == cliente.chaves_criadas

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest

from publicar_backlog_demanda_azure_boards.autorizacao import criar_frase_confirmacao
from publicar_backlog_demanda_azure_boards.cli import principal
from publicar_backlog_demanda_azure_boards.interpretar_markdown import (
    extrair_data_geracao,
    interpretar_backlog,
)
from publicar_backlog_demanda_azure_boards.manifesto import ler_manifesto
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    RegistroManifesto,
)
from publicar_backlog_demanda_azure_boards.planejar_publicacao import criar_plano

CONFIGURACAO = ConfiguracaoPublicacao(
    "organizacao", "Projeto", "Projeto", r"Projeto\Sprint 18", 13959
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
        self.validadas: list[tuple[str, int | None]] = []
        self.pais_usados: list[tuple[str, int | None]] = []

    def criar_item(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> RegistroManifesto:
        if operacao.chave_pai is not None:
            assert id_pai is not None
        self.pais_usados.append((operacao.chave, id_pai))
        self.chaves_criadas.append(operacao.chave)
        return RegistroManifesto(
            id=len(self.chaves_criadas),
            tipo=operacao.tipo,
            url=f"https://exemplo/{operacao.chave}",
        )

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> None:
        assert configuracao == self.configuracao

    def validar_operacao(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> None:
        self.validadas.append((operacao.chave, id_pai))

    def tipos_sem_criterios_aceitacao(self) -> frozenset[str]:
        return frozenset()


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


def test_publicacao_pela_cli_cancela_apos_esgotar_tentativas_de_confirmacao(
    tmp_path: Path, backlog: Path, cliente: ClienteSimulado
) -> None:
    manifesto = tmp_path / "manifesto-esgotado.json"
    entradas = "1\n" + "CONFIRMAÇÃO INCORRETA\n" * 3

    codigo = principal(
        ["publicar", str(backlog), "--manifesto", str(manifesto)],
        cliente=cliente,
        entrada=StringIO(entradas),
        saida=StringIO(),
    )

    assert codigo == 2
    assert cliente.chaves_criadas == []


def test_publicacao_pela_cli_aceita_confirmacao_apos_nova_tentativa(
    tmp_path: Path, backlog: Path, cliente: ClienteSimulado
) -> None:
    plano = criar_plano(
        interpretar_backlog(backlog), cliente.configuracao, extrair_data_geracao(backlog)
    )
    caminho_manifesto = tmp_path / "manifesto-retentativa.json"
    confirmacao = criar_frase_confirmacao(plano, frozenset(op.chave for op in plano.operacoes))
    saida = StringIO()

    codigo = principal(
        ["publicar", str(backlog), "--manifesto", str(caminho_manifesto)],
        cliente=cliente,
        entrada=StringIO(f"1\n{confirmacao.lower()}\n{confirmacao}\n"),
        saida=saida,
    )

    assert codigo == 0
    assert cliente.chaves_criadas == ["1.0.0", "1.1.0", "1.1.1"]
    assert "maiúsculas" in saida.getvalue()


def test_publicacao_pela_cli_cria_itens_em_ordem_e_grava_manifesto_no_caminho_informado(
    tmp_path: Path, backlog: Path, cliente: ClienteSimulado
) -> None:
    plano = criar_plano(
        interpretar_backlog(backlog),
        cliente.configuracao,
        extrair_data_geracao(backlog),
    )
    caminho_manifesto = tmp_path / "subdiretorio" / "manifesto.json"
    confirmacao = criar_frase_confirmacao(plano, frozenset(op.chave for op in plano.operacoes))

    codigo = principal(
        ["publicar", str(backlog), "--manifesto", str(caminho_manifesto)],
        cliente=cliente,
        entrada=StringIO(f"1\n{confirmacao}\n"),
        saida=StringIO(),
    )

    assert codigo == 0
    assert cliente.chaves_criadas == ["1.0.0", "1.1.0", "1.1.1"]
    assert list(ler_manifesto(caminho_manifesto).itens) == cliente.chaves_criadas


@pytest.fixture
def backlog_com_dois_epicos(tmp_path: Path, backlog: Path) -> Path:
    """Backlog com dois Épicos, para provar que todos sobem sob a mesma Demanda."""
    caminho = tmp_path / "backlog-dois-epicos.md"
    caminho.write_text(
        backlog.read_text(encoding="utf-8")
        + """
## 2.0.0 [Epic] Padronizar stacks

### Description
Objetivo, valor e escopo do segundo épico.

Origem na spec: seção 3.
""",
        encoding="utf-8",
    )
    return caminho


def test_publicacao_completa_vincula_tudo_a_demanda(
    tmp_path: Path, backlog_com_dois_epicos: Path, cliente: ClienteSimulado
) -> None:
    """Ponta a ponta: plano, frase, criação e manifesto, todos presos à Demanda."""
    plano = criar_plano(
        interpretar_backlog(backlog_com_dois_epicos),
        cliente.configuracao,
        extrair_data_geracao(backlog_com_dois_epicos),
    )
    caminho_manifesto = tmp_path / "manifesto.json"
    confirmacao = criar_frase_confirmacao(plano, frozenset(op.chave for op in plano.operacoes))
    saida = StringIO()

    codigo = principal(
        [
            "publicar",
            str(backlog_com_dois_epicos),
            "--manifesto",
            str(caminho_manifesto),
        ],
        cliente=cliente,
        entrada=StringIO(f"1\n{confirmacao}\n"),
        saida=saida,
    )

    assert codigo == 0
    assert "DEMANDA 13959" in saida.getvalue()
    assert "Épicos filhos da Demanda #13959: 1.0.0, 2.0.0" in saida.getvalue()

    pais = dict(cliente.pais_usados)
    assert pais["1.0.0"] == 13959
    assert pais["2.0.0"] == 13959
    assert all(id_pai is not None for _, id_pai in cliente.pais_usados)

    manifesto = ler_manifesto(caminho_manifesto)
    assert manifesto.configuracao is not None
    assert manifesto.configuracao.demanda_id == 13959
    assert sorted(manifesto.itens) == ["1.0.0", "1.1.0", "1.1.1", "2.0.0"]

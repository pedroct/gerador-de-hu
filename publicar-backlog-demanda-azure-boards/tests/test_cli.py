"""Testes da orquestração interna da CLI que não passam pelo parser de argumentos."""

from __future__ import annotations

from publicar_backlog_demanda_azure_boards.cli import _verificar_preliminar
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemPreexistente,
    MapeamentoTipos,
    TipoItem,
)

CONFIGURACAO = ConfiguracaoPublicacao("organizacao", "projeto", "projeto", "projeto\\Sprint", 13959)


class ClienteEspiao:
    def __init__(self) -> None:
        self.itens_verificados: list[tuple[int, str]] = []

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> None:
        del configuracao

    def verificar_item_existente(self, id_item: int, tipo_esperado: str) -> None:
        self.itens_verificados.append((id_item, tipo_esperado))

    def validar_operacao(self, operacao: object, id_pai: int | None = None) -> None:
        del operacao, id_pai


def test_verificacao_preliminar_confere_cada_item_preexistente() -> None:
    cliente = ClienteEspiao()

    _verificar_preliminar(
        cliente,
        CONFIGURACAO,
        (),
        (
            ItemPreexistente("1.0.0", TipoItem.EPIC, 4721),
            ItemPreexistente("2.0.0", TipoItem.EPIC, 4722),
        ),
    )

    assert cliente.itens_verificados == [(4721, "Epic"), (4722, "Epic")]


def test_verificacao_preliminar_usa_o_tipo_remoto_mapeado() -> None:
    configuracao_customizada = ConfiguracaoPublicacao(
        "organizacao",
        "projeto",
        "projeto",
        "projeto\\Sprint",
        13959,
        mapeamento_tipos=MapeamentoTipos(epic="Epico Customizado"),
    )
    cliente = ClienteEspiao()

    _verificar_preliminar(
        cliente,
        configuracao_customizada,
        (),
        (ItemPreexistente("1.0.0", TipoItem.EPIC, 4721),),
    )

    assert cliente.itens_verificados == [(4721, "Epico Customizado")]


def test_verificacao_preliminar_sem_preexistentes_nao_verifica_nada() -> None:
    cliente = ClienteEspiao()

    _verificar_preliminar(cliente, CONFIGURACAO, ())

    assert cliente.itens_verificados == []

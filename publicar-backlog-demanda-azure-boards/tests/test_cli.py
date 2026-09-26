"""Testes da orquestração interna da CLI que não passam pelo parser de argumentos."""

from __future__ import annotations

import io

from publicar_backlog_demanda_azure_boards.cli import (
    _apresentar_plano,
    _verificar_preliminar,
)
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemPreexistente,
    MapeamentoTipos,
    OperacaoCriacao,
    PlanoPublicacao,
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


def _plano(preexistentes: tuple[ItemPreexistente, ...]) -> PlanoPublicacao:
    return PlanoPublicacao(
        operacoes=(
            OperacaoCriacao(
                "1.1.1", TipoItem.HISTORIA_USUARIO, "História", "", "", "1.1.0", "User Story"
            ),
        ),
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        preexistentes=preexistentes,
    )


def test_plano_apresenta_os_itens_reaproveitados_com_o_id_declarado() -> None:
    saida = io.StringIO()
    plano = _plano(
        (
            ItemPreexistente("1.0.0", TipoItem.EPIC, 4721),
            ItemPreexistente("1.1.0", TipoItem.FEATURE, 4722),
        )
    )

    _apresentar_plano(plano, plano.operacoes, 3, 2, None, saida)

    assert "Itens já publicados reaproveitados: 1.0.0 (#4721), 1.1.0 (#4722)\n" in saida.getvalue()


def test_plano_sem_reaproveitados_diz_nenhum() -> None:
    saida = io.StringIO()
    plano = _plano(())

    _apresentar_plano(plano, plano.operacoes, 1, 0, None, saida)

    assert "Itens já publicados reaproveitados: nenhum\n" in saida.getvalue()


def test_reaproveitados_aparecem_antes_das_relacoes_que_os_citam() -> None:
    """O ID reaproveitado precede a linha que cita a chave dele.

    A linha de relações pai-filho nomeia uma chave que não está na ordem de
    criação; sem a linha acima, quem lê a tela não tem como saber de onde ela veio.
    """
    saida = io.StringIO()
    plano = _plano((ItemPreexistente("1.1.0", TipoItem.FEATURE, 4722),))

    _apresentar_plano(plano, plano.operacoes, 2, 1, None, saida)

    texto = saida.getvalue()
    assert texto.index("Itens já publicados reaproveitados:") < texto.index("Relações pai-filho:")

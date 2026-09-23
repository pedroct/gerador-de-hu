"""Numeração de título no formato praticado no board de destino."""

import pytest

from publicar_backlog_demanda_azure_boards.modelos import ItemBacklog, TipoItem
from publicar_backlog_demanda_azure_boards.titulo_hierarquico import montar_titulo, numerar


@pytest.mark.parametrize(
    ("chave", "esperado"),
    [
        ("1.0.0", "01"),
        ("1.1.0", "01.01"),
        ("1.1.1", "01.01.01"),
        ("2.3.4", "02.03.04"),
        ("10.0.0", "10"),
        ("10.11.12", "10.11.12"),
        ("100.0.0", "100"),
        ("1.1.112", "01.01.112"),
    ],
)
def test_numerar_converte_a_chave_documental(chave: str, esperado: str) -> None:
    assert numerar(chave) == esperado


@pytest.mark.parametrize("chave", ["", "1", "1.1", "1.1.1.1", "a.b.c", "1.-1.0"])
def test_numerar_rejeita_chave_fora_do_contrato(chave: str) -> None:
    with pytest.raises(ValueError):
        numerar(chave)


def test_montar_titulo_usa_o_titulo_curto_quando_existe() -> None:
    item = ItemBacklog(
        chave="1.1.1",
        tipo=TipoItem.HISTORIA_USUARIO,
        titulo="Análise de padrões de stacks em todos os repositórios",
        pai="1.1.0",
        descricao="",
        criterios_aceitacao="",
        titulo_curto="Análise de padrões de stacks",
    )
    assert montar_titulo(item) == "01.01.01 Análise de padrões de stacks"


def test_montar_titulo_cai_no_titulo_longo_sem_titulo_curto() -> None:
    item = ItemBacklog(
        chave="1.0.0",
        tipo=TipoItem.EPIC,
        titulo="Gestão do projeto",
        pai=None,
        descricao="",
        criterios_aceitacao="",
    )
    assert montar_titulo(item) == "01 Gestão do projeto"


def test_montar_titulo_nao_inclui_data() -> None:
    item = ItemBacklog(
        chave="1.1.0",
        tipo=TipoItem.FEATURE,
        titulo="Gestão do projeto",
        pai="1.0.0",
        descricao="",
        criterios_aceitacao="",
    )
    titulo = montar_titulo(item)
    assert titulo == "01.01 Gestão do projeto"
    assert "2026" not in titulo

import json

from publicar_backlog_azure_boards.manifesto import (
    Manifesto,
    gravar_manifesto,
    ler_manifesto,
)
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    RegistroManifesto,
    TipoItem,
)

CONFIGURACAO = ConfiguracaoPublicacao("organizacao", "projeto", "Projeto", "Projeto\\Sprint")


def test_manifesto_inexistente_comeca_vazio(tmp_path) -> None:
    manifesto = ler_manifesto(tmp_path / "mapa.json")

    assert manifesto.itens == {}


def test_manifesto_vazio_tem_round_trip(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"

    gravar_manifesto(caminho, Manifesto())

    assert ler_manifesto(caminho) == Manifesto()


def test_manifesto_e_gravado_e_lido_com_seus_metadados(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    manifesto = Manifesto(
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        itens={"1.0.0": RegistroManifesto(123, TipoItem.EPIC, "https://exemplo/123")},
        titulos={"1.0.0": "Épico"},
    )

    gravar_manifesto(caminho, manifesto)

    assert ler_manifesto(caminho) == manifesto
    assert json.loads(caminho.read_text(encoding="utf-8"))["versao"] == 1


def test_gravacao_substitui_atomicamente_sem_deixar_temporario(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    manifesto = Manifesto(hash_plano="hash", configuracao=CONFIGURACAO)

    gravar_manifesto(caminho, manifesto)

    assert list(tmp_path.glob("mapa.json.*")) == []

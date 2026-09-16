import json

import pytest

from publicar_backlog_azure_boards.manifesto import (
    ErroReconciliacaoPendente,
    Manifesto,
    ReconciliacaoPendente,
    gravar_manifesto,
    ler_manifesto,
)
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    RegistroManifesto,
    TipoItem,
)

CONFIGURACAO = ConfiguracaoPublicacao("organizacao", "projeto", "projeto", "projeto\\Sprint")


def destino_json() -> dict[str, object]:
    return {
        "organizacao": "organizacao",
        "projeto": "projeto",
        "area_path": "projeto",
        "iteration_path": "projeto\\Sprint",
        "mapeamento_tipos": {
            "Epic": "Epic",
            "Feature": "Feature",
            "User Story": "User Story",
            "Bug": "Bug",
        },
    }


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


def test_manifesto_preserva_estado_de_reconciliacao_manual(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    manifesto = Manifesto(
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        reconciliacao_pendente=ReconciliacaoPendente(
            chave="1.0.0",
            tipo_remoto="Epic",
            titulo="Épico",
        ),
    )

    gravar_manifesto(caminho, manifesto)

    assert ler_manifesto(caminho) == manifesto
    assert (
        json.loads(caminho.read_text(encoding="utf-8"))["reconciliacao_pendente"]["chave"]
        == "1.0.0"
    )


def test_manifesto_preserva_reconciliacao_com_contexto_completo(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    reconciliacao = ReconciliacaoPendente(
        chave="1.0.0",
        tipo_remoto="Epic",
        titulo="Épico",
        tipo=TipoItem.EPIC,
        destino=CONFIGURACAO,
        hash_plano="hash",
        timestamp="2026-09-16T15:00:00+00:00",
        motivo="URL de resposta malformada",
    )
    manifesto = Manifesto(
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        reconciliacoes={"1.0.0": reconciliacao},
    )

    gravar_manifesto(caminho, manifesto)
    dados = json.loads(caminho.read_text(encoding="utf-8"))

    assert ler_manifesto(caminho).reconciliacoes == {"1.0.0": reconciliacao}
    assert dados["reconciliacoes"]["1.0.0"]["resolucao"] == "pendente"
    assert dados["reconciliacoes"]["1.0.0"]["destino"] == {
        "organizacao": "organizacao",
        "projeto": "projeto",
        "area_path": "projeto",
        "iteration_path": "projeto\\Sprint",
        "mapeamento_tipos": {
            "Epic": "Epic",
            "Feature": "Feature",
            "User Story": "User Story",
            "Bug": "Bug",
        },
    }
    assert "token" not in json.dumps(dados).lower()


def test_manifesto_legado_singular_expoe_mapa_de_reconciliacoes() -> None:
    reconciliacao = ReconciliacaoPendente("1.0.0", "Epic", "Épico")

    manifesto = Manifesto(reconciliacao_pendente=reconciliacao)

    assert manifesto.reconciliacoes == {"1.0.0": reconciliacao}
    assert manifesto.reconciliacao_pendente == reconciliacao


def test_erro_de_reconciliacao_pendente_e_especializacao_compatível() -> None:
    assert issubclass(ErroReconciliacaoPendente, RuntimeError)


def test_estado_de_reconciliacao_desconhecido_e_rejeitado() -> None:
    with pytest.raises(ValueError, match="resolução"):
        ReconciliacaoPendente(
            chave="1.0.0",
            tipo_remoto="Epic",
            titulo="Épico",
            resolucao="resolvidaa",
        )


@pytest.mark.parametrize("destino_reconciliacao", [None, pytest.param("ausente")])
def test_reconciliacao_nova_exige_destino_completo(tmp_path, destino_reconciliacao) -> None:
    dados_reconciliacao: dict[str, object] = {
        "chave": "1.0.0",
        "tipo_remoto": "Epic",
        "tipo": "Epic",
        "titulo": "Épico",
        "hash_plano": "hash",
        "timestamp": "2026-09-16T15:00:00+00:00",
        "motivo": "timeout após envio",
        "resolucao": "pendente",
        "destino": destino_json(),
    }
    if destino_reconciliacao is None:
        dados_reconciliacao["destino"] = None
    else:
        dados_reconciliacao.pop("destino")
    caminho = tmp_path / "mapa.json"
    caminho.write_text(
        json.dumps(
            {
                "versao": 1,
                "origem": "backlog.md",
                "hash_plano": "hash",
                "destino": destino_json(),
                "reconciliacoes": {"1.0.0": dados_reconciliacao},
                "itens": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="é inválido"):
        ler_manifesto(caminho)


def test_manifesto_legado_preserva_reconciliacao_sem_destino(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    caminho.write_text(
        json.dumps(
            {
                "versao": 1,
                "origem": "backlog.md",
                "hash_plano": "hash",
                "destino": destino_json(),
                "reconciliacao_pendente": {
                    "chave": "1.0.0",
                    "tipo_remoto": "Epic",
                    "titulo": "Épico",
                },
                "itens": {},
            }
        ),
        encoding="utf-8",
    )

    manifesto = ler_manifesto(caminho)

    assert manifesto.reconciliacao_pendente is not None
    assert manifesto.reconciliacao_pendente.destino is None


def test_gravacao_substitui_atomicamente_sem_deixar_temporario(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    manifesto = Manifesto(hash_plano="hash", configuracao=CONFIGURACAO)

    gravar_manifesto(caminho, manifesto)

    assert list(tmp_path.glob("mapa.json.*")) == []

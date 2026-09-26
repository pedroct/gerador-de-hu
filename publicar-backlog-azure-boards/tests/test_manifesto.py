import json

import pytest

from publicar_backlog_azure_boards.manifesto import (
    ErroReconciliacaoPendente,
    Manifesto,
    ReconciliacaoPendente,
    gravar_manifesto,
    ler_manifesto,
    validar_manifesto,
)
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemPreexistente,
    OperacaoCriacao,
    PlanoPublicacao,
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


def test_reconciliacao_nova_sem_destino_e_rejeitada_mesmo_com_registro_legado() -> None:
    legado = ReconciliacaoPendente("1.0.0", "Epic", "Épico")
    nova = ReconciliacaoPendente("2.0.0", "Feature", "Funcionalidade")

    with pytest.raises(ValueError, match="exigem contexto de destino completo"):
        Manifesto(
            reconciliacao_pendente=legado,
            reconciliacoes={"2.0.0": nova},
        )


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


def test_manifesto_legado_resolvido_sem_destino_preserva_estado_no_round_trip(tmp_path) -> None:
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
                    "resolucao": "resolvida_nao_criada",
                },
                "itens": {},
            }
        ),
        encoding="utf-8",
    )

    manifesto = ler_manifesto(caminho)
    gravar_manifesto(caminho, manifesto)
    dados = json.loads(caminho.read_text(encoding="utf-8"))

    assert manifesto.reconciliacao_pendente is not None
    assert manifesto.reconciliacao_pendente.resolucao == "resolvida_nao_criada"
    assert dados["reconciliacao_pendente"]["resolucao"] == "resolvida_nao_criada"
    assert ler_manifesto(caminho).reconciliacoes["1.0.0"].resolucao == "resolvida_nao_criada"


def test_validar_manifesto_rejeita_resolvida_criada_sem_o_item_em_itens() -> None:
    plano = PlanoPublicacao(
        operacoes=(OperacaoCriacao("1.0.0", TipoItem.EPIC, "Épico", "", "", None, "Epic"),),
        hash_plano="hash",
        configuracao=CONFIGURACAO,
    )
    reconciliacao = ReconciliacaoPendente(
        chave="1.0.0",
        tipo_remoto="Epic",
        titulo="Épico",
        tipo=TipoItem.EPIC,
        destino=CONFIGURACAO,
        hash_plano="hash",
        resolucao="resolvida_criada",
    )
    manifesto = Manifesto(
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        reconciliacoes={"1.0.0": reconciliacao},
    )

    with pytest.raises(ValueError, match="resolvida_criada"):
        validar_manifesto(manifesto, plano, CONFIGURACAO)


def test_validar_manifesto_rejeita_resolvida_nao_criada_com_o_item_em_itens() -> None:
    plano = PlanoPublicacao(
        operacoes=(OperacaoCriacao("1.0.0", TipoItem.EPIC, "Épico", "", "", None, "Epic"),),
        hash_plano="hash",
        configuracao=CONFIGURACAO,
    )
    reconciliacao = ReconciliacaoPendente(
        chave="1.0.0",
        tipo_remoto="Epic",
        titulo="Épico",
        tipo=TipoItem.EPIC,
        destino=CONFIGURACAO,
        hash_plano="hash",
        resolucao="resolvida_nao_criada",
    )
    manifesto = Manifesto(
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        itens={"1.0.0": RegistroManifesto(1, TipoItem.EPIC, "https://exemplo/1")},
        titulos={"1.0.0": "Épico"},
        reconciliacoes={"1.0.0": reconciliacao},
    )

    with pytest.raises(ValueError, match="resolvida_nao_criada"):
        validar_manifesto(manifesto, plano, CONFIGURACAO)


def test_gravacao_substitui_atomicamente_sem_deixar_temporario(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    manifesto = Manifesto(hash_plano="hash", configuracao=CONFIGURACAO)

    gravar_manifesto(caminho, manifesto)

    assert list(tmp_path.glob("mapa.json.*")) == []


def test_preserva_a_marca_de_preexistente_ao_gravar_e_ler(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    original = Manifesto(
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        itens={"1.0.0": RegistroManifesto(4721, TipoItem.EPIC, "https://exemplo/4721", True)},
        titulos={"1.0.0": "2026-09-25 1.0.0 Épico"},
    )

    gravar_manifesto(caminho, original)

    assert ler_manifesto(caminho).itens["1.0.0"].preexistente is True


def test_manifesto_antigo_sem_a_marca_continua_valido(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    original = Manifesto(
        hash_plano="hash",
        configuracao=CONFIGURACAO,
        itens={"1.0.0": RegistroManifesto(9, TipoItem.EPIC, "https://exemplo/9")},
        titulos={"1.0.0": "2026-09-25 1.0.0 Épico"},
    )
    gravar_manifesto(caminho, original)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    del dados["itens"]["1.0.0"]["preexistente"]
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    assert ler_manifesto(caminho).itens["1.0.0"].preexistente is False


def _plano_com_preexistente() -> PlanoPublicacao:
    return PlanoPublicacao(
        operacoes=(
            OperacaoCriacao("1.1.0", TipoItem.FEATURE, "Feature", "", "", "1.0.0", "Feature"),
        ),
        hash_plano="hash-preexistente",
        configuracao=CONFIGURACAO,
        preexistentes=(ItemPreexistente("1.0.0", TipoItem.EPIC, 4721),),
    )


def test_validar_manifesto_aceita_segunda_rodada_com_item_preexistente_ja_registrado() -> None:
    """A segunda rodada sobre o mesmo backlog encontra o Epic já publicado e continua.

    Antes desta correção, `validar_manifesto` exigia que toda chave em `manifesto.itens`
    estivesse em `plano.operacoes` — e um preexistente nunca está lá (a Tarefa 7a o remove
    de propósito). Isso derrubava com ValueError qualquer segunda chamada sobre um
    manifesto que já tivesse persistido o preexistente.
    """
    plano = _plano_com_preexistente()
    manifesto = Manifesto(
        hash_plano="hash-preexistente",
        configuracao=CONFIGURACAO,
        itens={
            "1.0.0": RegistroManifesto(4721, TipoItem.EPIC, "https://exemplo/4721", True),
            "1.1.0": RegistroManifesto(1, TipoItem.FEATURE, "https://exemplo/1.1.0"),
        },
        titulos={
            "1.0.0": "(item pré-existente, Azure Boards #4721)",
            "1.1.0": "Feature",
        },
    )

    pendentes = validar_manifesto(manifesto, plano, CONFIGURACAO)

    assert pendentes == ()


def test_validar_manifesto_recusa_id_preexistente_alterado_entre_rodadas() -> None:
    """Um `Azure Boards ID` editado no Markdown entre duas rodadas precisa ser detectado."""
    plano = _plano_com_preexistente()
    manifesto = Manifesto(
        hash_plano="hash-preexistente",
        configuracao=CONFIGURACAO,
        itens={"1.0.0": RegistroManifesto(9999, TipoItem.EPIC, "https://exemplo/9999", True)},
        titulos={"1.0.0": "(item pré-existente, Azure Boards #9999)"},
    )

    with pytest.raises(ValueError, match="1.0.0 do manifesto diverge do item pré-existente"):
        validar_manifesto(manifesto, plano, CONFIGURACAO)


def test_validar_manifesto_recusa_registro_nao_marcado_como_preexistente() -> None:
    """Um manifesto adulterado à mão não pode se passar por uma criação legítima."""
    plano = _plano_com_preexistente()
    manifesto = Manifesto(
        hash_plano="hash-preexistente",
        configuracao=CONFIGURACAO,
        itens={"1.0.0": RegistroManifesto(4721, TipoItem.EPIC, "https://exemplo/4721")},
        titulos={"1.0.0": "(item pré-existente, Azure Boards #4721)"},
    )

    with pytest.raises(ValueError, match="1.0.0 do manifesto não está marcado como pré-existente"):
        validar_manifesto(manifesto, plano, CONFIGURACAO)


def test_validar_manifesto_continua_recusando_item_fora_do_backlog_completo() -> None:
    """Não-regressão: uma chave que não é operação nem preexistente continua rejeitada."""
    plano = _plano_com_preexistente()
    manifesto = Manifesto(
        hash_plano="hash-preexistente",
        configuracao=CONFIGURACAO,
        itens={"9.9.9": RegistroManifesto(1, TipoItem.EPIC, "https://exemplo/9")},
        titulos={"9.9.9": "Item desconhecido"},
    )

    with pytest.raises(ValueError, match="9.9.9"):
        validar_manifesto(manifesto, plano, CONFIGURACAO)

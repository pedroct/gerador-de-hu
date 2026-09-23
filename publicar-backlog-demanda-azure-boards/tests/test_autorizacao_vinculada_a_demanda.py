"""A autorização e o manifesto ficam presos à Demanda para a qual foram emitidos."""

from dataclasses import replace

import pytest

from publicar_backlog_demanda_azure_boards.autorizacao import (
    ModalidadeAutorizacao,
    criar_autorizacao,
    criar_frase_confirmacao,
)
from publicar_backlog_demanda_azure_boards.manifesto import Manifesto, validar_manifesto
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    MapeamentoTipos,
    RegistroManifesto,
    TipoItem,
)
from publicar_backlog_demanda_azure_boards.planejar_publicacao import criar_plano

_ITENS = [
    ItemBacklog(
        chave="1.0.0",
        tipo=TipoItem.EPIC,
        titulo="Gestão do projeto",
        pai=None,
        descricao="Contexto.",
        criterios_aceitacao="",
    )
]


def _destino(demanda_id: int) -> ConfiguracaoPublicacao:
    return ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=demanda_id,
        mapeamento_tipos=MapeamentoTipos(),
    )


def _plano(demanda_id: int):
    return criar_plano(_ITENS, _destino(demanda_id), "2026-09-22")


def test_trocar_a_demanda_muda_o_hash_do_plano() -> None:
    assert _plano(13959).hash_plano != _plano(13970).hash_plano


def test_a_frase_nomeia_a_demanda() -> None:
    frase = criar_frase_confirmacao(_plano(13959), ("1.0.0",))
    assert "DEMANDA 13959" in frase


def test_frase_de_uma_demanda_nao_autoriza_outra() -> None:
    frase_original = criar_frase_confirmacao(_plano(13959), ("1.0.0",))
    with pytest.raises(PermissionError):
        criar_autorizacao(
            _plano(13970),
            frase_original,
            frozenset({"1.0.0"}),
            modalidade=ModalidadeAutorizacao.INTEIRA,
        )


def test_autorizacao_valida_nao_vale_para_outro_destino() -> None:
    plano = _plano(13959)
    autorizacao = criar_autorizacao(
        plano,
        criar_frase_confirmacao(plano, ("1.0.0",)),
        frozenset({"1.0.0"}),
        modalidade=ModalidadeAutorizacao.INTEIRA,
    )
    assert autorizacao.valida_para(plano, _destino(13959))
    assert not autorizacao.valida_para(plano, _destino(13970))


def test_manifesto_de_uma_demanda_nao_retoma_sob_outra() -> None:
    plano_original = _plano(13959)
    manifesto = Manifesto(
        hash_plano=plano_original.hash_plano,
        configuracao=_destino(13959),
        itens={"1.0.0": RegistroManifesto(id=13969, tipo=TipoItem.EPIC, url="https://exemplo")},
        titulos={"1.0.0": plano_original.operacoes[0].titulo},
    )
    with pytest.raises(ValueError):
        validar_manifesto(manifesto, _plano(13970), _destino(13970))


def test_validacao_de_manifesto_rejeita_divergencia_de_demanda_mesmo_com_hash_igual() -> None:
    """Prova que a validação de destino do manifesto rejeita demanda_id divergente, isolada do hash.

    Sem este teste, um manifesto com configuracao de demanda diferente poderia passar se o
    hash por acaso batesse com o novo plano.
    """
    plano_novo = _plano(13970)
    manifesto = replace(
        Manifesto(
            hash_plano=plano_novo.hash_plano,  # Hash do novo plano (passa na linha 166)
            configuracao=_destino(13959),  # Mas configuracao da demanda antiga
            itens={"1.0.0": RegistroManifesto(id=13969, tipo=TipoItem.EPIC, url="https://exemplo")},
            titulos={"1.0.0": plano_novo.operacoes[0].titulo},
        ),
        hash_plano=plano_novo.hash_plano,
    )
    with pytest.raises(ValueError):
        validar_manifesto(manifesto, plano_novo, _destino(13970))

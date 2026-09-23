"""O ID da Demanda faz parte da identidade do destino publicado."""

import pytest

from publicar_backlog_demanda_azure_boards.autorizacao import imprimir_destino
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    Demanda,
    MapeamentoTipos,
)


def _destino(demanda_id: int) -> ConfiguracaoPublicacao:
    return ConfiguracaoPublicacao(
        organizacao="contoso",
        projeto="CESOP-DILIGENCIA",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        demanda_id=demanda_id,
        mapeamento_tipos=MapeamentoTipos(),
    )


def test_demanda_id_e_obrigatorio_no_destino() -> None:
    with pytest.raises(TypeError):
        ConfiguracaoPublicacao(  # type: ignore[call-arg]
            organizacao="contoso",
            projeto="CESOP-DILIGENCIA",
            area_path="CESOP-DILIGENCIA\\Sustentacao",
            iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        )


def test_destinos_com_demandas_diferentes_tem_impressoes_diferentes() -> None:
    assert imprimir_destino(_destino(13959)) != imprimir_destino(_destino(13970))


def test_demanda_carrega_titulo_e_caminhos_para_derivar_o_destino() -> None:
    demanda = Demanda(
        id=13959,
        titulo="PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        url="https://dev.azure.com/contoso/_apis/wit/workItems/13959",
    )
    assert demanda.id == 13959
    assert demanda.area_path.endswith("Sustentacao")

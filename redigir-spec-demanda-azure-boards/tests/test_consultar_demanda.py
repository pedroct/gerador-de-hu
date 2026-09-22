import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "consultar_demanda.py"
SPEC = importlib.util.spec_from_file_location("consultar_demanda", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
modulo = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = modulo
SPEC.loader.exec_module(modulo)


CONFIGURACAO = modulo.ConfiguracaoAzureBoards("org", "projeto", "segredo")
CAMPOS = {
    "System.Title",
    "Custom.DemandaAreaSolicitante",
    "Custom.DemandaPublicoAlvo",
    "Custom.DemandaValorEsperado",
    "Custom.DemandaDoraResolver",
    "Custom.DemandaRegraseRestricoes",
}


def resposta_demanda(**campos: object) -> dict[str, object]:
    valores = {
        "System.WorkItemType": "Demanda de Negócio",
        "System.Title": "Consultar débitos do contribuinte",
        "Custom.DemandaAreaSolicitante": "Célula de Arrecadação",
        "Custom.DemandaPublicoAlvo": "Auditor Fiscal",
        "Custom.DemandaValorEsperado": "Reduzir retrabalho",
        "Custom.DemandaDoraResolver": "Consulta é dispersa",
        "Custom.DemandaRegraseRestricoes": "Restringir por perfil",
    }
    valores.update(campos)
    return {
        "id": 42,
        "url": "https://dev.azure.com/org/projeto/_apis/wit/workItems/42",
        "fields": valores,
    }


def requisitar_resposta_padrao(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
    if "/workitems/42?" in url:
        return resposta_demanda()
    return {"value": [{"referenceName": campo} for campo in CAMPOS]}


def test_consultar_demanda_mapeia_campos_e_usa_apenas_urls_get() -> None:
    chamadas: list[str] = []

    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        chamadas.append(url)
        return requisitar_resposta_padrao(url, cabecalhos)

    demanda = modulo.consultar_demanda(42, CONFIGURACAO, requisitar)

    assert demanda.id == 42
    assert demanda.titulo == "Consultar débitos do contribuinte"
    assert demanda.valores["Custom.DemandaDoraResolver"] == "Consulta é dispersa"
    assert len(chamadas) == 2
    assert chamadas[0] == (
        "https://dev.azure.com/org/projeto/_apis/wit/workitems/42?"
        "$expand=Fields&api-version=7.1"
    )
    assert chamadas[1] == (
        "https://dev.azure.com/org/projeto/_apis/wit/workitemtypes/"
        "Demanda%20de%20Neg%C3%B3cio/fields?api-version=7.1"
    )
    assert all("api-version=" in url for url in chamadas)
    assert all(
        not any(verbo in url for verbo in ("POST", "PATCH", "PUT", "DELETE"))
        for url in chamadas
    )


@pytest.mark.parametrize("id_item", [0, -1])
def test_consultar_demanda_rejeita_id_nao_positivo(id_item: int) -> None:
    def nao_deve_ser_chamado(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        raise AssertionError("a requisição não deveria ocorrer")

    with pytest.raises(modulo.ErroConsultaDemanda, match="ID"):
        modulo.consultar_demanda(id_item, CONFIGURACAO, nao_deve_ser_chamado)


@pytest.mark.parametrize(
    ("nome", "resposta"),
    [
        ("work item sem fields", {"id": 42, "url": "https://dev.azure.com/item"}),
        ("ID remoto diferente", {**resposta_demanda(), "id": 99}),
        ("URL não HTTPS", {**resposta_demanda(), "url": "http://dev.azure.com/item"}),
        ("tipo incorreto", resposta_demanda(**{"System.WorkItemType": "User Story"})),
        ("título vazio", resposta_demanda(**{"System.Title": "  "})),
    ],
)
def test_consultar_demanda_rejeita_payload_principal_invalido(
    nome: str, resposta: dict[str, object]
) -> None:
    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        if "/workitems/42?" in url:
            return resposta
        return {"value": [{"referenceName": campo} for campo in CAMPOS]}

    with pytest.raises(modulo.ErroConsultaDemanda, match="ID|URL|tipo|título|fields"):
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)


def test_consultar_demanda_preserva_campo_vazio_como_lacuna() -> None:
    demanda = modulo.consultar_demanda(
        42,
        CONFIGURACAO,
        lambda url, cabecalhos: (
            resposta_demanda(**{"Custom.DemandaAreaSolicitante": "  "})
            if "/workitems/42?" in url
            else {"value": [{"referenceName": campo} for campo in CAMPOS]}
        ),
    )

    assert demanda.valores["Custom.DemandaAreaSolicitante"] is None


def test_consultar_demanda_rejeita_campo_ausente_no_tipo() -> None:
    campos = CAMPOS - {"Custom.DemandaValorEsperado"}

    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        if "/workitems/42?" in url:
            return resposta_demanda()
        return {"value": [{"referenceName": campo} for campo in campos]}

    with pytest.raises(modulo.ErroConsultaDemanda, match="Custom.DemandaValorEsperado"):
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)


def test_consultar_demanda_rejeita_campo_customizado_nao_textual() -> None:
    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        if "/workitems/42?" in url:
            return resposta_demanda(**{"Custom.DemandaValorEsperado": 123})
        return {"value": [{"referenceName": campo} for campo in CAMPOS]}

    with pytest.raises(modulo.ErroConsultaDemanda, match="Custom.DemandaValorEsperado"):
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)


@pytest.mark.parametrize(
    "resposta",
    [
        {"value": []},
        {"value": [{"referenceName": 42}]},
        {"value": ["não é objeto"]},
    ],
)
def test_consultar_demanda_rejeita_definicao_de_campos_invalida(
    resposta: dict[str, object],
) -> None:
    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        return resposta_demanda() if "/workitems/42?" in url else resposta

    with pytest.raises(modulo.ErroConsultaDemanda, match="campos"):
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)


def test_consultar_demanda_converte_erro_http_e_json_sem_expor_token() -> None:
    class RespostaHttp:
        status = 401

    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        raise modulo.HTTPError(url, 401, "não autorizado", {}, None)

    with pytest.raises(modulo.ErroConsultaDemanda, match="401") as erro:
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)

    assert "segredo" not in str(erro.value)


def test_consultar_demanda_nao_expoe_detalhes_do_erro_de_transporte() -> None:
    valor_proibido = "token-super-secreto-do-proxy"

    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        raise modulo.URLError(f"proxy recusou a credencial {valor_proibido}")

    with pytest.raises(modulo.ErroConsultaDemanda) as erro:
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)

    assert valor_proibido not in str(erro.value)


def test_requisitar_json_envia_get_e_token_no_cabecalho() -> None:
    chamadas: list[tuple[str, dict[str, str]]] = []

    class Resposta:
        def read(self) -> bytes:
            return json.dumps({"ok": True}).encode()

        def __enter__(self) -> "Resposta":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    def abrir(request: object) -> Resposta:
        chamadas.append((request.full_url, dict(request.header_items())))
        return Resposta()

    resultado = modulo.requisitar_json(
        "https://dev.azure.com/x", {"Authorization": "Bearer segredo"}, abrir=abrir
    )

    assert resultado == {"ok": True}
    assert chamadas == [("https://dev.azure.com/x", {"Authorization": "Bearer segredo"})]

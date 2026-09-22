import importlib.util
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "consultar_demanda.py"
SPEC = importlib.util.spec_from_file_location("consultar_demanda", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
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


def modulo_fonte() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def requisitar_resposta_padrao(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
    if "/workitems/42?" in url:
        return resposta_demanda()
    return {"value": [{"referenceName": campo} for campo in CAMPOS]}


class RespostaFalsa:
    """Dublê de resposta HTTP usado no lugar do objeto devolvido por urlopen."""

    def __init__(self, corpo: bytes) -> None:
        self._corpo = corpo

    def read(self) -> bytes:
        return self._corpo

    def __enter__(self) -> "RespostaFalsa":
        return self

    def __exit__(self, *args: object) -> None:
        return None


@pytest.fixture(autouse=True)
def _sem_espera_real(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Registra as esperas de retry em vez de dormir, mantendo a suíte rápida."""
    esperas: list[float] = []
    monkeypatch.setattr(modulo.time, "sleep", esperas.append)
    return esperas


def test_consultar_demanda_mapeia_campos_e_url_por_consulta() -> None:
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


def test_caminho_de_producao_emite_somente_requests_get(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercita `requisitar=None`, o único caminho que a CLI usa de verdade."""
    requisicoes: list[object] = []

    def abrir(requisicao: object, timeout: float | None = None) -> RespostaFalsa:
        requisicoes.append(requisicao)
        corpo = (
            resposta_demanda()
            if "/workitems/42?" in requisicao.full_url
            else {"value": [{"referenceName": campo} for campo in CAMPOS]}
        )
        assert timeout == modulo.TIMEOUT_SEGUNDOS
        return RespostaFalsa(json.dumps(corpo).encode("utf-8"))

    monkeypatch.setattr(modulo, "urlopen", abrir)

    demanda = modulo.consultar_demanda(42, CONFIGURACAO)

    assert demanda.titulo == "Consultar débitos do contribuinte"
    assert len(requisicoes) == 2
    # A proibição de escrita é verificada nos objetos Request reais, não na string da URL.
    assert [requisicao.get_method() for requisicao in requisicoes] == ["GET", "GET"]
    assert all(requisicao.data is None for requisicao in requisicoes)
    assert [requisicao.full_url for requisicao in requisicoes] == [
        "https://dev.azure.com/org/projeto/_apis/wit/workitems/42?$expand=Fields&api-version=7.1",
        "https://dev.azure.com/org/projeto/_apis/wit/workitemtypes/"
        "Demanda%20de%20Neg%C3%B3cio/fields?api-version=7.1",
    ]
    esperado = "Basic " + modulo.base64.b64encode(b":segredo").decode()
    assert all(
        requisicao.get_header("Authorization") == esperado for requisicao in requisicoes
    )


def test_fonte_do_leitor_nao_declara_metodo_diferente_de_get() -> None:
    """Trava a regressão que uma asserção sobre URLs jamais pegaria."""
    fonte = modulo_fonte()
    assert fonte.count("method=") == 1
    assert 'method="GET"' in fonte
    for verbo in ("POST", "PATCH", "PUT", "DELETE"):
        assert f'"{verbo}"' not in fonte


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


def test_consultar_demanda_mapeia_lista_vazia_como_lacuna() -> None:
    demanda = modulo.consultar_demanda(
        42,
        CONFIGURACAO,
        lambda url, cabecalhos: (
            resposta_demanda(**{"Custom.DemandaPublicoAlvo": []})
            if "/workitems/42?" in url
            else {"value": [{"referenceName": campo} for campo in CAMPOS]}
        ),
    )

    assert demanda.valores["Custom.DemandaPublicoAlvo"] is None


def test_consultar_demanda_rejeita_campo_ausente_no_tipo() -> None:
    campos = CAMPOS - {"Custom.DemandaValorEsperado"}

    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        if "/workitems/42?" in url:
            return resposta_demanda()
        return {"value": [{"referenceName": campo} for campo in campos]}

    with pytest.raises(modulo.ErroConsultaDemanda, match="Custom.DemandaValorEsperado") as erro:
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)

    assert erro.value.categoria == "contrato"
    assert erro.value.detalhe_publico == (
        "campo remoto obrigatório ausente: Custom.DemandaValorEsperado"
    )


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


@pytest.mark.parametrize(
    ("codigo", "trecho_publico"),
    [
        (401, "credencial inválida"),
        (403, "sem permissão"),
        (404, "não encontrada"),
    ],
)
def test_consultar_demanda_converte_erro_http_sem_expor_token(
    codigo: int, trecho_publico: str
) -> None:
    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        raise modulo.HTTPError(url, codigo, "recusado", {}, None)

    with pytest.raises(modulo.ErroConsultaDemanda, match=str(codigo)) as erro:
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)

    assert "segredo" not in str(erro.value)
    # O código HTTP não é segredo e é o que distingue ID errado de acesso negado.
    assert erro.value.codigo_http == codigo
    assert trecho_publico in erro.value.detalhe_publico


def test_erro_http_sem_diagnostico_publico_nao_inventa_detalhe() -> None:
    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        raise modulo.HTTPError(url, 418, "bule de chá", {}, None)

    with pytest.raises(modulo.ErroConsultaDemanda) as erro:
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)

    assert erro.value.codigo_http is None
    assert erro.value.detalhe_publico is None


def test_consultar_demanda_nao_expoe_detalhes_do_erro_de_transporte() -> None:
    valor_proibido = "token-super-secreto-do-proxy"

    def requisitar(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
        raise modulo.URLError(f"proxy recusou a credencial {valor_proibido}")

    with pytest.raises(modulo.ErroConsultaDemanda) as erro:
        modulo.consultar_demanda(42, CONFIGURACAO, requisitar)

    assert valor_proibido not in str(erro.value)


def test_requisitar_json_repassa_cabecalhos_e_usa_get_com_timeout() -> None:
    chamadas: list[tuple[str, dict[str, str], str, float | None]] = []

    def abrir(request: object, timeout: float | None = None) -> RespostaFalsa:
        chamadas.append(
            (
                request.full_url,
                dict(request.header_items()),
                request.get_method(),
                timeout,
            )
        )
        return RespostaFalsa(json.dumps({"ok": True}).encode())

    resultado = modulo.requisitar_json(
        "https://dev.azure.com/x", {"Authorization": "Bearer segredo"}, abrir=abrir
    )

    assert resultado == {"ok": True}
    assert chamadas == [
        (
            "https://dev.azure.com/x",
            {"Authorization": "Bearer segredo"},
            "GET",
            modulo.TIMEOUT_SEGUNDOS,
        )
    ]


def test_requisitar_json_honra_retry_after_dentro_do_limite(
    _sem_espera_real: list[float],
) -> None:
    chamadas = 0

    def abrir(request: object, timeout: float | None = None) -> RespostaFalsa:
        nonlocal chamadas
        chamadas += 1
        if chamadas == 1:
            raise HTTPError(request.full_url, 429, "throttle", {"Retry-After": "2"}, None)
        return RespostaFalsa(b'{"ok": true}')

    assert modulo.requisitar_json("https://dev.azure.com/x", {}, abrir=abrir) == {"ok": True}
    assert _sem_espera_real == [2.0]


@pytest.mark.parametrize(
    ("cabecalhos", "esperado"),
    [
        ({}, 0.5),
        ({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}, 0.5),
        ({"Retry-After": "-3"}, 0.5),
        ({"Retry-After": "900"}, modulo._ESPERA_RETRY_AFTER_MAXIMA),
    ],
)
def test_requisitar_json_ignora_retry_after_invalido_ou_abusivo(
    cabecalhos: dict[str, str], esperado: float, _sem_espera_real: list[float]
) -> None:
    chamadas = 0

    def abrir(request: object, timeout: float | None = None) -> RespostaFalsa:
        nonlocal chamadas
        chamadas += 1
        if chamadas == 1:
            raise HTTPError(request.full_url, 503, "indisponível", cabecalhos, None)
        return RespostaFalsa(b'{"ok": true}')

    assert modulo.requisitar_json("https://dev.azure.com/x", {}, abrir=abrir) == {"ok": True}
    assert _sem_espera_real == [esperado]


@pytest.mark.parametrize("erro", [TimeoutError("estourou"), ConnectionResetError("caiu")])
def test_requisitar_json_repete_timeout_cru_fora_de_urlerror(erro: OSError) -> None:
    """Com timeout no socket, a falha chega crua — e é tão transitória quanto via URLError."""
    chamadas = 0

    def abrir(request: object, timeout: float | None = None) -> RespostaFalsa:
        nonlocal chamadas
        chamadas += 1
        if chamadas < 3:
            raise erro
        return RespostaFalsa(b'{"ok": true}')

    assert modulo.requisitar_json("https://dev.azure.com/x", {}, abrir=abrir) == {"ok": True}
    assert chamadas == 3


def test_configuracao_prefere_argumento_a_arquivo_e_ambiente(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "AZURE_DEVOPS_ORGANIZACAO=env-org\nAZURE_DEVOPS_PROJETO=env-projeto\n"
        "AZURE_DEVOPS_TOKEN=token-env\n"
    )
    argumentos = modulo.construir_parser().parse_args(
        [
            "42",
            "--organizacao",
            "arg-org",
            "--projeto",
            "Projeto",
            "--env-file",
            str(env),
        ]
    )

    configuracao = modulo.carregar_configuracao(
        argumentos,
        ambiente={
            "AZURE_DEVOPS_ORGANIZACAO": "ambiente-org",
            "AZURE_DEVOPS_PROJETO": "ambiente-projeto",
            "AZURE_DEVOPS_TOKEN": "token-ambiente",
        },
    )

    assert configuracao.organizacao == "arg-org"
    assert configuracao.projeto == "Projeto"
    assert configuracao.token == "token-" + "env"


def test_configuracao_usa_raiz_do_toml_e_ambiente(tmp_path: Path) -> None:
    configuracao_toml = tmp_path / "config.toml"
    configuracao_toml.write_text(
        'AZURE_DEVOPS_ORGANIZACAO = "toml-org"\nAZURE_DEVOPS_PROJETO = "toml-projeto"\n'
        'AZURE_DEVOPS_TOKEN = "token-toml"\n'
    )
    argumentos = modulo.construir_parser().parse_args(
        ["42", "--config", str(configuracao_toml), "--env-file", str(tmp_path / "inexistente")]
    )

    configuracao = modulo.carregar_configuracao(
        argumentos,
        ambiente={"AZURE_DEVOPS_TOKEN": "token-ambiente"},
    )

    assert configuracao == modulo.ConfiguracaoAzureBoards("toml-org", "toml-projeto", "token-toml")


def test_configuracao_aplica_precedencia_completa_com_tabela_azure_devops(
    tmp_path: Path,
) -> None:
    configuracao_toml = tmp_path / "config.toml"
    configuracao_toml.write_text(
        "[azure_devops]\n"
        'organizacao = "toml-org"\n'
        'projeto = "toml-projeto"\n'
        'AZURE_DEVOPS_TOKEN = "token-toml"\n'
    )
    env = tmp_path / ".env"
    env.write_text(
        "AZURE_DEVOPS_ORGANIZACAO=env-org\n"
        "AZURE_DEVOPS_PROJETO=env-projeto\n"
        "AZURE_DEVOPS_TOKEN=token-env\n"
    )
    ambiente = {
        "AZURE_DEVOPS_ORGANIZACAO": "ambiente-org",
        "AZURE_DEVOPS_PROJETO": "ambiente-projeto",
        "AZURE_DEVOPS_TOKEN": "token-ambiente",
    }

    argumentos = modulo.construir_parser().parse_args(
        [
            "42",
            "--organizacao",
            "arg-org",
            "--projeto",
            "arg-projeto",
            "--config",
            str(configuracao_toml),
            "--env-file",
            str(env),
        ]
    )
    assert modulo.carregar_configuracao(argumentos, ambiente=ambiente) == (
        modulo.ConfiguracaoAzureBoards("arg-org", "arg-projeto", "token-toml")
    )

    argumentos = modulo.construir_parser().parse_args(
        ["42", "--config", str(configuracao_toml), "--env-file", str(env)]
    )
    assert modulo.carregar_configuracao(argumentos, ambiente=ambiente) == (
        modulo.ConfiguracaoAzureBoards("toml-org", "toml-projeto", "token-toml")
    )

    configuracao_toml.write_text('[azure_devops]\norganizacao = "toml-org"\n')
    assert modulo.carregar_configuracao(argumentos, ambiente=ambiente) == (
        modulo.ConfiguracaoAzureBoards("toml-org", "env-projeto", "token-env")
    )

    configuracao_toml.write_text("[azure_devops]\n")
    env.write_text("")
    assert modulo.carregar_configuracao(argumentos, ambiente=ambiente) == (
        modulo.ConfiguracaoAzureBoards("ambiente-org", "ambiente-projeto", "token-ambiente")
    )


def test_configuracao_rejeita_entrada_nao_interativa_sem_token(monkeypatch, tmp_path: Path) -> None:
    argumentos = modulo.construir_parser().parse_args(
        [
            "42",
            "--organizacao",
            "org",
            "--projeto",
            "p",
            "--env-file",
            str(tmp_path / "inexistente"),
        ]
    )
    monkeypatch.setattr(modulo.sys.stdin, "isatty", lambda: False)
    getpass_chamado = False

    def nao_deve_pedir(mensagem: str) -> str:
        nonlocal getpass_chamado
        getpass_chamado = True
        raise AssertionError("não deve solicitar senha em entrada não interativa")

    monkeypatch.setattr(modulo.getpass, "getpass", nao_deve_pedir)

    with pytest.raises(modulo.ErroConfiguracao, match="token"):
        modulo.carregar_configuracao(argumentos, ambiente={})
    assert not getpass_chamado


@pytest.mark.parametrize(
    ("argumentos", "trecho_esperado"),
    [
        (["42"], "AZURE_DEVOPS_ORGANIZACAO"),
        (["42", "--organizacao", "org"], "AZURE_DEVOPS_PROJETO"),
        (["42", "--organizacao", "org", "--projeto", "p"], "AZURE_DEVOPS_TOKEN"),
    ],
)
def test_principal_diz_qual_configuracao_faltou(
    argumentos: list[str], trecho_esperado: str, monkeypatch, capsys, tmp_path: Path
) -> None:
    """Destino e nome de variável não são segredo; sem isso o erro é irrecuperável."""
    for chave in ("AZURE_DEVOPS_ORGANIZACAO", "AZURE_DEVOPS_PROJETO", "AZURE_DEVOPS_TOKEN"):
        monkeypatch.delenv(chave, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(modulo.sys.stdin, "isatty", lambda: False)

    assert modulo.principal(argumentos) == 1

    capturado = capsys.readouterr()
    assert "Erro [configuração]" in capturado.err
    assert trecho_esperado in capturado.err
    assert capturado.out == ""


def test_erro_de_configuracao_recusa_detalhe_fora_da_allow_list() -> None:
    erro = modulo.ErroConfiguracao("interno", detalhe_publico="token=abc123")
    assert erro.detalhe_publico is None


def test_principal_nao_expoe_token_em_falha(monkeypatch, capsys) -> None:
    token = "segredo-" + "de-teste"

    def levantar_erro_comunicavel(*args: object, **kwargs: object) -> None:
        raise modulo.ErroConsultaDemanda(f"falha: {token}")

    monkeypatch.setattr(modulo, "consultar_demanda", levantar_erro_comunicavel)
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", token)
    assert modulo.principal(["42", "--organizacao", "org", "--projeto", "p"]) == 1
    capturado = capsys.readouterr()
    assert token not in capturado.err
    assert token not in json.dumps(capturado.err)
    assert capturado.out == ""


def test_principal_diagnostica_campo_ausente_com_sigilo(monkeypatch, capsys) -> None:
    campo_ausente = "Custom.DemandaValorEsperado"
    detalhe_externo = "resposta externa com token-super-secreto"

    def levantar_erro_com_diagnostico(*args: object, **kwargs: object) -> None:
        raise modulo.ErroConsultaDemanda(
            detalhe_externo,
            categoria="contrato",
            campo_ausente=campo_ausente,
        )

    monkeypatch.setattr(modulo, "consultar_demanda", levantar_erro_com_diagnostico)
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", "token-super-secreto")

    assert modulo.principal(["42", "--organizacao", "org", "--projeto", "p"]) == 1

    capturado = capsys.readouterr()
    saida = capturado.err
    assert "Erro [contrato]" in saida
    assert campo_ausente in saida
    assert detalhe_externo not in saida
    assert "token-super-secreto" not in saida
    # stdout continua reservado ao JSON, para não sujar um pipe para jq.
    assert capturado.out == ""


def test_principal_serializa_apenas_campos_publicos(monkeypatch, capsys) -> None:
    demanda = modulo.DemandaNegocio(
        id=42,
        url="https://dev.azure.com/org/p/_apis/wit/workItems/42",
        tipo="Demanda de Negócio",
        titulo="Título",
        valores={campo: f"valor-{campo}" for campo in CAMPOS if campo != "System.Title"},
    )
    monkeypatch.setattr(modulo, "consultar_demanda", lambda *args, **kwargs: demanda)
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", "segredo")

    assert modulo.principal(["42", "--organizacao", "org", "--projeto", "p"]) == 0
    saida = json.loads(capsys.readouterr().out)
    assert set(saida) == {"id", "url", "tipo", "titulo", "campos"}
    assert set(saida["campos"]) == CAMPOS - {"System.Title"}
    assert "System.Title" not in saida["campos"]
    assert "segredo" not in json.dumps(saida)


def test_principal_serializa_lista_vazia_mapeada_como_null(monkeypatch, capsys) -> None:
    valores = {campo: f"valor-{campo}" for campo in CAMPOS if campo != "System.Title"}
    valores["Custom.DemandaPublicoAlvo"] = None
    demanda = modulo.DemandaNegocio(
        id=42,
        url="https://dev.azure.com/org/p/_apis/wit/workItems/42",
        tipo="Demanda de Negócio",
        titulo="Título",
        valores=valores,
    )
    monkeypatch.setattr(modulo, "consultar_demanda", lambda *args, **kwargs: demanda)
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", "segredo")

    assert modulo.principal(["42", "--organizacao", "org", "--projeto", "p"]) == 0

    saida = json.loads(capsys.readouterr().out)
    assert saida["campos"]["Custom.DemandaPublicoAlvo"] is None


def test_requisitar_json_retries_transitorios() -> None:
    chamadas: list[object] = []

    class Resposta:
        def read(self) -> bytes:
            return b'{"ok": true}'

        def __enter__(self) -> "Resposta":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    def abrir(request: object, timeout: float | None = None) -> Resposta:
        chamadas.append(request)
        if len(chamadas) < 3:
            raise HTTPError(request.full_url, 503, "indisponível", {}, None)
        return Resposta()

    assert modulo.requisitar_json(
        "https://dev.azure.com/x",
        {"Accept": "application/json", "X": "y"},
        token="token",  # noqa: S106
        abrir=abrir,
    ) == {"ok": True}
    assert len(chamadas) == 3
    assert chamadas[0].get_method() == "GET"
    assert chamadas[0].get_header("Authorization") == "Basic " + modulo.base64.b64encode(
        b":token"
    ).decode()


def test_requisitar_json_erro_http_permanente_nao_repetido() -> None:
    chamadas = 0

    def abrir(request: object, timeout: float | None = None) -> object:
        nonlocal chamadas
        chamadas += 1
        raise HTTPError(request.full_url, 400, "ruim", {}, None)

    with pytest.raises(modulo.ErroConsultaDemanda, match="HTTP 400"):
        modulo.requisitar_json("https://dev.azure.com/x", {}, token="token", abrir=abrir)  # noqa: S106
    assert chamadas == 1


def test_requisitar_json_encapsula_erro_de_transporte_sem_detalhes() -> None:
    segredo = "token-super-secreto"
    chamadas = 0

    def abrir(request: object, timeout: float | None = None) -> object:
        nonlocal chamadas
        chamadas += 1
        raise URLError(f"falha com {segredo}")

    with pytest.raises(modulo.ErroConsultaDemanda) as erro:
        modulo.requisitar_json("https://dev.azure.com/x", {}, token=segredo, abrir=abrir)
    assert segredo not in str(erro.value)
    assert chamadas == 1


def test_requisitar_json_repete_urlerro_transitorio_ate_sucesso() -> None:
    chamadas = 0

    class Resposta:
        def read(self) -> bytes:
            return b'{"ok": true}'

        def __enter__(self) -> "Resposta":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    def abrir(request: object, timeout: float | None = None) -> Resposta:
        nonlocal chamadas
        chamadas += 1
        if chamadas < 3:
            raise URLError(TimeoutError("tempo esgotado"))
        return Resposta()

    assert modulo.requisitar_json("https://dev.azure.com/x", {}, abrir=abrir) == {"ok": True}
    assert chamadas == 3


def test_requisitar_json_limita_urlerro_transitorio_a_tres_tentativas() -> None:
    chamadas = 0

    def abrir(request: object, timeout: float | None = None) -> object:
        nonlocal chamadas
        chamadas += 1
        raise URLError(TimeoutError("tempo esgotado"))

    with pytest.raises(modulo.ErroConsultaDemanda):
        modulo.requisitar_json("https://dev.azure.com/x", {}, abrir=abrir)
    assert chamadas == 3


def test_requisitar_json_nao_repete_oserror_puro() -> None:
    chamadas = 0

    def abrir(request: object, timeout: float | None = None) -> object:
        nonlocal chamadas
        chamadas += 1
        raise OSError("falha local")

    with pytest.raises(modulo.ErroConsultaDemanda):
        modulo.requisitar_json("https://dev.azure.com/x", {}, abrir=abrir)
    assert chamadas == 1

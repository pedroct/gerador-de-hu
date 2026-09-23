from __future__ import annotations

import importlib
import sys
from io import StringIO
from pathlib import Path

import httpx
import pytest

from publicar_backlog_demanda_azure_boards.cliente_azure_devops import ClienteAzureDevOps

RAIZ = Path(__file__).resolve().parents[1]
for caminho in (RAIZ / "src",):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

_modelos = importlib.import_module("publicar_backlog_demanda_azure_boards.modelos")
_publicar_backlog = importlib.import_module("publicar_backlog_demanda_azure_boards.cli")
ConfiguracaoPublicacao = _modelos.ConfiguracaoPublicacao
OperacaoCriacao = _modelos.OperacaoCriacao
RegistroManifesto = _modelos.RegistroManifesto
principal = _publicar_backlog.principal


ROOT = RAIZ
BACKLOG = ROOT / "tests" / "fixtures" / "valid-backlog.md"
CONFIGURACAO = ConfiguracaoPublicacao(
    "organizacao", "projeto", "Projeto", r"Projeto\Sprint 18", 13959
)


class ClienteFalso:
    def __init__(self) -> None:
        self.configuracao = CONFIGURACAO
        self.chaves_criadas: list[str] = []
        self.chamadas_http: list[str] = []

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> None:
        assert configuracao == CONFIGURACAO
        self.chamadas_http.append("GET")

    def validar_operacao(self, operacao: OperacaoCriacao) -> None:
        del operacao
        self.chamadas_http.append("POST validateOnly")

    def criar_item(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> RegistroManifesto:
        del id_pai
        chave = operacao.chave
        self.chaves_criadas.append(chave)
        return RegistroManifesto(len(self.chaves_criadas), operacao.tipo, chave)


def test_simulacao_nao_chama_criacao(capsys) -> None:
    cliente = ClienteFalso()

    codigo = principal(["publicar", str(BACKLOG), "--simulacao"], cliente=cliente)

    assert codigo == 0
    assert cliente.chaves_criadas == []
    assert not any(
        metodo == "POST" or metodo.startswith("POST ") for metodo in cliente.chamadas_http
    )
    assert "Simulação" in capsys.readouterr().out


def test_simulacao_sem_token_nao_instancia_cliente_http(monkeypatch, tmp_path) -> None:
    env_vazio = tmp_path / ".env"
    env_vazio.write_text("", encoding="utf-8")

    class ClienteProibido:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("simulação não pode instanciar cliente HTTP")

    monkeypatch.setattr(_publicar_backlog, "ClienteAzureDevOps", ClienteProibido)
    monkeypatch.delenv("AZURE_DEVOPS_TOKEN", raising=False)

    codigo = principal(
        [
            "publicar",
            str(BACKLOG),
            "--simulacao",
            "--organizacao",
            "organizacao",
            "--projeto",
            "Projeto",
            "--area-path",
            "Projeto",
            "--iteration-path",
            r"Projeto\Sprint 18",
            "--demanda",
            "13959",
            "--env-file",
            str(env_vazio),
            "--manifesto",
            str(tmp_path / "manifesto.json"),
        ],
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert codigo == 0


def test_validar_apenas_valida_operacoes_remotamente_sem_criar_itens() -> None:
    cliente = ClienteFalso()

    codigo = principal(
        ["publicar", str(BACKLOG), "--validar-apenas"],
        cliente=cliente,
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert codigo == 0
    assert cliente.chamadas_http == [
        "GET",
        "POST validateOnly",
        "POST validateOnly",
        "POST validateOnly",
    ]
    assert cliente.chaves_criadas == []


def test_validar_apenas_valida_remotamente_com_validate_only_true_sem_criacao_persistente(
    monkeypatch, tmp_path
) -> None:
    env_vazio = tmp_path / ".env"
    env_vazio.write_text("", encoding="utf-8")
    chamadas: list[httpx.Request] = []
    prompts: list[str] = []
    saida = StringIO()

    def ler_sem_eco(prompt: str) -> str:
        prompts.append(prompt)
        return "credencial-de-teste"

    def responder(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        if request.method == "POST":
            assert request.url.params.get("validateOnly") == "true"
            return httpx.Response(200, json={}, request=request)
        if request.method != "GET":
            pytest.fail(f"Método inesperado: {request.method}")
        caminho = request.url.path
        if caminho.endswith("/_apis/wit/workitemtypes"):
            corpo: dict[str, object] = {
                "value": [{"name": tipo} for tipo in CONFIGURACAO.mapeamento_tipos.nomes_remotos()]
            }
        elif caminho.endswith("/fields"):
            corpo = {
                "value": [
                    {"referenceName": campo}
                    for campo in (
                        "System.Title",
                        "System.Description",
                        "System.AreaPath",
                        "System.IterationPath",
                    )
                ]
            }
        elif caminho.endswith("/_apis/wit/workitemrelationtypes"):
            corpo = {"value": [{"referenceName": "System.LinkTypes.Hierarchy-Reverse"}]}
        elif caminho.endswith("/classificationnodes/Areas"):
            corpo = {
                "name": "Projeto",
                "path": r"\Projeto\Area",
                "url": "https://dev.azure.com/organizacao/Projeto/_apis/wit/classificationnodes/Areas",
                "structureType": "area",
            }
        elif caminho.endswith("/classificationnodes/Iterations/Sprint 18"):
            corpo = {
                "name": "Sprint 18",
                "path": r"\Projeto\Iteration\Sprint 18",
                "url": "https://dev.azure.com/organizacao/Projeto/_apis/wit/classificationnodes/Iterations/Sprint%2018",
                "structureType": "iteration",
            }
        else:
            pytest.fail(f"GET inesperado: {request.url}")
        return httpx.Response(200, json=corpo, request=request)

    def construir_cliente(configuracao, token):
        assert token == "credencial" + "-de-teste"
        return ClienteAzureDevOps(
            configuracao,
            token,
            transport=httpx.MockTransport(responder),
            espera_inicial=0,
        )

    monkeypatch.setattr("getpass.getpass", ler_sem_eco)
    monkeypatch.setattr(_publicar_backlog, "ClienteAzureDevOps", construir_cliente)

    codigo = principal(
        [
            "publicar",
            str(BACKLOG),
            "--validar-apenas",
            "--organizacao",
            "organizacao",
            "--projeto",
            "Projeto",
            "--area-path",
            "Projeto",
            "--iteration-path",
            r"Projeto\Sprint 18",
            "--demanda",
            "13959",
            "--env-file",
            str(env_vazio),
            "--manifesto",
            str(tmp_path / "manifesto.json"),
        ],
        entrada=StringIO(),
        saida=saida,
    )

    assert codigo == 0
    assert prompts == ["Credencial do Azure DevOps: "]
    assert chamadas
    assert any(request.method == "POST" for request in chamadas)
    assert all(
        request.method == "GET" or request.url.params.get("validateOnly") == "true"
        for request in chamadas
    )
    assert "credencial-de-teste" not in saida.getvalue()


def test_validador_estrutural_existente_bloqueia_antes_do_planejamento(
    monkeypatch, tmp_path
) -> None:
    backlog_invalido = tmp_path / "backlog.md"
    backlog_invalido.write_text(
        BACKLOG.read_text(encoding="utf-8").replace("1.1.1", "1.1.2"),
        encoding="utf-8",
    )
    planejamento_chamado = False

    def criar_plano_proibido(*args, **kwargs):
        nonlocal planejamento_chamado
        planejamento_chamado = True
        raise AssertionError("backlog inválido não pode alcançar o planejamento")

    monkeypatch.setattr(_publicar_backlog, "criar_plano", criar_plano_proibido)

    codigo = principal(
        [
            "planejar",
            str(backlog_invalido),
            "--organizacao",
            "organizacao",
            "--projeto",
            "Projeto",
            "--area-path",
            "Projeto",
            "--iteration-path",
            r"Projeto\Sprint 18",
            "--env-file",
            str(tmp_path / ".env-inexistente"),
        ],
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert codigo == 1
    assert planejamento_chamado is False


def test_skill_declara_confirmacao_antes_de_escrita() -> None:
    texto = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "zero chamadas de criação" in texto
    assert "AUTORIZAR PUBLICAÇÃO" in texto


def test_skill_nao_chama_mcp_obrigatoriamente() -> None:
    texto = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "MCP" in texto
    assert "opcional" in texto

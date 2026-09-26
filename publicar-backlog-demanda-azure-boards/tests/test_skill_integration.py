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


def _demanda_falsa() -> object:
    """Demanda coerente com CONFIGURACAO, para os fluxos que não falam com a rede."""
    return _modelos.Demanda(
        id=13959,
        titulo="PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO",
        area_path="Projeto",
        iteration_path=r"Projeto\Sprint 18",
        url="https://dev.azure.com/organizacao/_apis/wit/workItems/13959",
    )


class ClienteFalso:
    def __init__(self) -> None:
        self.configuracao = CONFIGURACAO
        self.chaves_criadas: list[str] = []
        self.chamadas_http: list[str] = []
        self.validadas: list[tuple[str, int | None]] = []

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> None:
        assert configuracao == CONFIGURACAO
        self.chamadas_http.append("GET")

    def validar_operacao(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> None:
        self.validadas.append((operacao.chave, id_pai))
        self.chamadas_http.append("POST validateOnly")

    def tipos_sem_criterios_aceitacao(self) -> frozenset[str]:
        return frozenset()

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


def test_simulacao_le_a_demanda_uma_vez_e_nao_instancia_cliente_de_escrita(
    monkeypatch, tmp_path
) -> None:
    """Critério 2 da spec: a simulação faz exatamente um GET e nenhuma escrita.

    A simulação deixou de ser offline quando Area Path e Iteration Path passaram a
    vir da Demanda: não há como montar o plano — nem o hash — sem ler o work item.
    O que ela preserva é o resto: nenhuma escrita e nenhuma autorização pedida.
    """
    env_vazio = tmp_path / ".env"
    env_vazio.write_text("", encoding="utf-8")
    metodos: list[str] = []

    def responder(request: httpx.Request) -> httpx.Response:
        metodos.append(request.method)
        return httpx.Response(
            200,
            json={
                "id": 13959,
                "url": "https://dev.azure.com/organizacao/_apis/wit/workItems/13959",
                "fields": {
                    "System.WorkItemType": "Demanda de Negócio",
                    "System.TeamProject": "Projeto",
                    "System.Title": "PADRONIZAÇÃO",
                    "System.AreaPath": "Projeto",
                    "System.IterationPath": r"Projeto\Sprint 18",
                },
            },
            request=request,
        )

    leitor_real = _publicar_backlog.ler_demanda
    monkeypatch.setattr(
        _publicar_backlog,
        "ler_demanda",
        lambda *args: leitor_real(*args, transport=httpx.MockTransport(responder)),
    )

    class ClienteProibido:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("a simulação não pode instanciar o cliente de escrita")

    monkeypatch.setattr(_publicar_backlog, "ClienteAzureDevOps", ClienteProibido)
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", "credencial" + "-de-teste")
    saida = StringIO()

    codigo = principal(
        [
            "publicar",
            str(BACKLOG),
            "--simulacao",
            "--organizacao",
            "organizacao",
            "--projeto",
            "Projeto",
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
    assert metodos == ["GET"]
    assert "nenhuma autorização foi solicitada" in saida.getvalue()
    assert not (tmp_path / "manifesto.json").exists()


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
    # A leitura da Demanda é um GET próprio, fora do cliente de publicação; este teste
    # mede o que acontece depois dela.
    monkeypatch.setattr(_publicar_backlog, "ler_demanda", lambda *args: _demanda_falsa())

    codigo = principal(
        [
            "publicar",
            str(BACKLOG),
            "--validar-apenas",
            "--organizacao",
            "organizacao",
            "--projeto",
            "Projeto",
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


def test_verificacao_preliminar_valida_epicos_contra_a_demanda() -> None:
    """Critério 3 da spec: `--validar-apenas` exercita o vínculo com a Demanda.

    Um item sem ``chave_pai`` é sempre um Épico, e o pai dele — a Demanda — já existe
    no Azure Boards. Features e Histórias seguem validando sem pai, porque os seus
    ainda não foram criados.
    """
    ItemBacklog = _modelos.ItemBacklog
    TipoItem = _modelos.TipoItem
    criar_plano = importlib.import_module(
        "publicar_backlog_demanda_azure_boards.planejar_publicacao"
    ).criar_plano

    plano = criar_plano(
        [
            ItemBacklog("1.0.0", TipoItem.EPIC, "Gestão", None, "d", ""),
            ItemBacklog("1.1.0", TipoItem.FEATURE, "Gestão", "1.0.0", "d", ""),
        ],
        CONFIGURACAO,
        "2026-09-22",
    )
    validadas: list[tuple[str, int | None]] = []

    class ClienteVerificador:
        configuracao = CONFIGURACAO

        def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> None:
            return None

        def validar_operacao(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> None:
            validadas.append((operacao.chave, id_pai))

        def criar_item(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> object:
            raise AssertionError("A verificação preliminar não pode criar itens.")

    _publicar_backlog._verificar_preliminar(ClienteVerificador(), CONFIGURACAO, plano.operacoes)

    assert dict(validadas) == {"1.0.0": 13959, "1.1.0": None}


def test_plano_apresenta_a_demanda_de_origem() -> None:
    """O plano nomeia a Demanda e marca os caminhos como herdados dela."""
    saida = StringIO()

    codigo = principal(
        ["planejar", str(BACKLOG)],
        cliente=ClienteFalso(),
        entrada=StringIO(),
        saida=saida,
    )

    texto = saida.getvalue()
    assert codigo == 0
    assert "Demanda de Negócio: #13959" in texto
    assert texto.count("(herdado da Demanda #13959)") == 2
    assert "Épicos filhos da Demanda #13959: 1.0.0" in texto


def test_plano_nomeia_a_demanda_lida_com_seu_titulo(monkeypatch, tmp_path) -> None:
    """Quando a Demanda é lida de verdade, o plano mostra o título dela."""
    saida = StringIO()
    monkeypatch.setattr(_publicar_backlog, "ler_demanda", lambda *args: _demanda_falsa())
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", "credencial" + "-de-teste")

    codigo = principal(
        [
            "planejar",
            str(BACKLOG),
            "--organizacao",
            "organizacao",
            "--projeto",
            "Projeto",
            "--demanda",
            "13959",
            "--env-file",
            str(tmp_path / ".env-inexistente"),
        ],
        entrada=StringIO(),
        saida=saida,
    )

    assert codigo == 0
    assert (
        "Demanda de Negócio: #13959 — PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO"
        in saida.getvalue()
    )


def test_plano_exibe_a_data_de_geracao_do_backlog() -> None:
    """Sem a data no título, ela é o único sinal na tela de qual geração se autoriza."""
    saida = StringIO()

    codigo = principal(
        ["planejar", str(BACKLOG)],
        cliente=ClienteFalso(),
        entrada=StringIO(),
        saida=saida,
    )

    assert codigo == 0
    assert "Backlog gerado em: 2026-09-10" in saida.getvalue()


def test_ajuda_da_simulacao_nao_promete_execucao_offline() -> None:
    """A simulação lê a Demanda desde que os caminhos passaram a ser herdados."""
    parser = _publicar_backlog.construir_parser()
    acoes = {
        acao.dest: acao
        for subparser in parser._subparsers._group_actions  # type: ignore[union-attr]
        for nome, sub in subparser.choices.items()
        if nome == "publicar"
        for acao in sub._actions
    }
    ajuda_simulacao = acoes["simulacao"].help or ""

    assert "sem token" not in ajuda_simulacao
    assert "sem chamadas remotas" not in ajuda_simulacao
    assert "Demanda" in ajuda_simulacao


class _ClienteComTipoLimitado(ClienteFalso):
    """Processo remoto que não expõe critérios no tipo do item que os carrega.

    Modela o caso real encontrado no CESOP-DILIGENCIA: `Bug` não tem
    `Microsoft.VSTS.Common.AcceptanceCriteria`, e o Gherkin escrito para um Bug
    era descartado sem aviso. A fixture só tem critérios na User Story `1.1.1`,
    então é esse o tipo limitado aqui.
    """

    def tipos_sem_criterios_aceitacao(self) -> frozenset[str]:
        return frozenset({"User Story"})


def _publicar_com(cliente: ClienteFalso, tmp_path) -> str:
    saida = StringIO()
    principal(
        ["publicar", str(BACKLOG), "--validar-apenas", "--manifesto", str(tmp_path / "m.json")],
        cliente=cliente,
        entrada=StringIO(),
        saida=saida,
    )
    return saida.getvalue()


def test_avisa_quando_criterios_nao_serao_publicados(tmp_path) -> None:
    """A autorização vincula o conteúdo executável; o que se perde tem de ser dito antes."""
    texto = _publicar_com(_ClienteComTipoLimitado(), tmp_path)

    assert "NÃO serão publicados" in texto
    assert "1.1.1" in texto


def test_sem_aviso_quando_o_processo_expoe_o_campo(tmp_path) -> None:
    texto = _publicar_com(ClienteFalso(), tmp_path)

    assert "NÃO serão publicados" not in texto

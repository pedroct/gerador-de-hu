from __future__ import annotations

import importlib
import sys
from io import StringIO
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
for caminho in (RAIZ / "src",):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

_modelos = importlib.import_module("publicar_backlog_azure_boards.modelos")
_publicar_backlog = importlib.import_module("publicar_backlog_azure_boards.cli")
ConfiguracaoPublicacao = _modelos.ConfiguracaoPublicacao
OperacaoCriacao = _modelos.OperacaoCriacao
RegistroManifesto = _modelos.RegistroManifesto
principal = _publicar_backlog.principal


ROOT = RAIZ
BACKLOG = ROOT / "tests" / "fixtures" / "valid-backlog.md"
CONFIGURACAO = ConfiguracaoPublicacao("organizacao", "projeto", "Projeto", r"Projeto\Sprint 18")


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
            "--env-file",
            str(env_vazio),
            "--manifesto",
            str(tmp_path / "manifesto.json"),
        ],
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert codigo == 0


def test_validar_apenas_consulta_remotamente_sem_post() -> None:
    cliente = ClienteFalso()

    codigo = principal(
        ["publicar", str(BACKLOG), "--validar-apenas"],
        cliente=cliente,
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert codigo == 0
    assert cliente.chamadas_http == ["GET"]
    assert cliente.chaves_criadas == []


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

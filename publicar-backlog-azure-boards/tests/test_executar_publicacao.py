from dataclasses import replace

import pytest

from publicar_backlog_azure_boards.autorizacao import (
    ErroAutorizacao,
    criar_autorizacao,
    criar_frase_confirmacao,
)
from publicar_backlog_azure_boards.cliente_azure_devops import ErroCriacaoAmbigua
from publicar_backlog_azure_boards.executar_publicacao import FalhaPublicacao, executar_plano
from publicar_backlog_azure_boards.manifesto import (
    Manifesto,
    ReconciliacaoManualNecessaria,
    gravar_manifesto,
    ler_manifesto,
)
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    PlanoPublicacao,
    RegistroManifesto,
    TipoItem,
)

CONFIGURACAO = ConfiguracaoPublicacao("organizacao", "projeto", "projeto", "projeto\\Sprint")


def plano() -> PlanoPublicacao:
    return PlanoPublicacao(
        operacoes=(
            OperacaoCriacao("1.0.0", TipoItem.EPIC, "Épico", "", "", None, "Epic"),
            OperacaoCriacao("1.1.0", TipoItem.FEATURE, "Feature", "", "", "1.0.0", "Feature"),
        ),
        hash_plano="hash",
        configuracao=CONFIGURACAO,
    )


def autorizacao(chaves_pendentes: tuple[str, ...] = ("1.0.0", "1.1.0")):
    plano_atual = plano()
    confirmacao = criar_frase_confirmacao(plano_atual, chaves_pendentes)
    return criar_autorizacao(
        plano_atual,
        confirmacao,
        frozenset(chaves_pendentes),
    )


class ClienteFalso:
    def __init__(
        self,
        falhar_na_chave: str | None = None,
        erro: Exception | None = None,
        configuracao: ConfiguracaoPublicacao = CONFIGURACAO,
    ) -> None:
        self.falhar_na_chave = falhar_na_chave
        self.erro = erro or RuntimeError("falha permanente")
        self.configuracao = configuracao
        self.chaves_criadas: list[str] = []

    def criar_item(self, operacao: OperacaoCriacao, id_pai: int | None = None):
        if operacao.chave == self.falhar_na_chave:
            raise self.erro
        self.chaves_criadas.append(operacao.chave)
        return RegistroManifesto(
            len(self.chaves_criadas), operacao.tipo, f"https://exemplo/{operacao.chave}"
        )


def test_manifesto_e_gravado_depois_de_cada_sucesso(tmp_path) -> None:
    cliente = ClienteFalso()

    executar_plano(plano(), autorizacao(), cliente, tmp_path / "mapa.json")

    assert set(ler_manifesto(tmp_path / "mapa.json").itens) == {"1.0.0", "1.1.0"}
    assert cliente.chaves_criadas == ["1.0.0", "1.1.0"]


def test_retomada_valida_manifesto_no_backlog_completo_antes_de_remover_pendentes(
    tmp_path,
) -> None:
    caminho = tmp_path / "mapa.json"
    cliente_com_falha = ClienteFalso("1.1.0")

    with pytest.raises(FalhaPublicacao):
        executar_plano(plano(), autorizacao(), cliente_com_falha, caminho)

    cliente_sem_falha = ClienteFalso()
    executar_plano(plano(), autorizacao(("1.1.0",)), cliente_sem_falha, caminho)

    assert cliente_sem_falha.chaves_criadas == ["1.1.0"]


def test_manifesto_divergente_bloqueia_antes_de_remover_pendentes(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    gravar_manifesto(
        caminho,
        Manifesto(
            hash_plano="hash",
            configuracao=CONFIGURACAO,
            itens={"1.0.0": RegistroManifesto(1, TipoItem.EPIC, "https://exemplo/1")},
            titulos={"1.0.0": "Título divergente"},
        ),
    )
    cliente = ClienteFalso()

    with pytest.raises(ValueError, match="diverge"):
        executar_plano(plano(), autorizacao(("1.1.0",)), cliente, caminho)

    assert cliente.chaves_criadas == []


def test_executor_bloqueia_conteudo_divergente_mesmo_com_mesmo_hash(tmp_path) -> None:
    plano_alterado = replace(
        plano(),
        operacoes=(replace(plano().operacoes[0], titulo="Alterado"), plano().operacoes[1]),
    )
    cliente = ClienteFalso()

    with pytest.raises(ErroAutorizacao):
        executar_plano(plano_alterado, autorizacao(), cliente, tmp_path / "mapa.json")

    assert cliente.chaves_criadas == []


def test_cliente_de_outro_destino_e_rejeitado_antes_de_criar(tmp_path) -> None:
    cliente_outro_projeto = ClienteFalso(
        configuracao=replace(
            CONFIGURACAO,
            projeto="outro-projeto",
            area_path="outro-projeto",
            iteration_path="outro-projeto\\Sprint",
        )
    )

    with pytest.raises(ErroAutorizacao):
        executar_plano(plano(), autorizacao(), cliente_outro_projeto, tmp_path / "mapa.json")

    assert cliente_outro_projeto.chaves_criadas == []


def test_falha_ambigua_deixa_manifesto_bloqueado_para_reconciliacao(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    cliente_ambiguo = ClienteFalso(
        "1.0.0",
        ErroCriacaoAmbigua("Não é possível confirmar se o item foi criado."),
    )

    with pytest.raises(FalhaPublicacao):
        executar_plano(plano(), autorizacao(), cliente_ambiguo, caminho)

    manifesto = ler_manifesto(caminho)
    assert manifesto.reconciliacao_pendente is not None
    assert manifesto.reconciliacao_pendente.chave == "1.0.0"

    cliente_novo = ClienteFalso()
    with pytest.raises(ReconciliacaoManualNecessaria):
        executar_plano(plano(), autorizacao(), cliente_novo, caminho)
    assert cliente_novo.chaves_criadas == []

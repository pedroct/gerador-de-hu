import pytest

from publicar_backlog_azure_boards.autorizacao import (
    Autorizacao,
    ModalidadeAutorizacao,
    criar_autorizacao,
    criar_frase_confirmacao,
)
from publicar_backlog_azure_boards.executar_publicacao import FalhaPublicacao, executar_plano
from publicar_backlog_azure_boards.manifesto import ler_manifesto
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    PlanoPublicacao,
    RegistroManifesto,
    TipoItem,
)

CONFIGURACAO = ConfiguracaoPublicacao("organizacao", "projeto", "Projeto", "Projeto\\Sprint")


def plano() -> PlanoPublicacao:
    return PlanoPublicacao(
        operacoes=(
            OperacaoCriacao("1.0.0", TipoItem.EPIC, "Épico", "", "", None),
            OperacaoCriacao("1.1.0", TipoItem.FEATURE, "Feature", "", "", "1.0.0"),
        ),
        hash_plano="hash",
    )


def autorizacao() -> Autorizacao:
    autorizacao = Autorizacao("hash", ModalidadeAutorizacao.INTEIRA)
    object.__setattr__(autorizacao, "_confirmada", True)
    return autorizacao


def autorizacao_do_primeiro_lote() -> Autorizacao:
    confirmacao = criar_frase_confirmacao("hash", 1, CONFIGURACAO, numero_lote=1)
    return criar_autorizacao(
        plano_hash="hash",
        modalidade=ModalidadeAutorizacao.LOTES,
        confirmacao=confirmacao,
        quantidade=1,
        configuracao=CONFIGURACAO,
        numero_lote=1,
        chaves_autorizadas={"1.0.0"},
    )


class ClienteFalso:
    configuracao = CONFIGURACAO

    def __init__(self, falhar_na_chave: str | None = None) -> None:
        self.falhar_na_chave = falhar_na_chave
        self.chaves_criadas: list[str] = []

    def criar_item(self, operacao: OperacaoCriacao, id_pai: int | None = None):
        if operacao.chave == self.falhar_na_chave:
            raise RuntimeError("falha permanente")
        self.chaves_criadas.append(operacao.chave)
        return RegistroManifesto(len(self.chaves_criadas), operacao.tipo, f"https://exemplo/{operacao.chave}")


def test_manifesto_e_gravado_depois_de_cada_sucesso(tmp_path) -> None:
    cliente = ClienteFalso()

    executar_plano(plano(), autorizacao(), cliente, tmp_path / "mapa.json")

    assert set(ler_manifesto(tmp_path / "mapa.json").itens) == {"1.0.0", "1.1.0"}
    assert cliente.chaves_criadas == ["1.0.0", "1.1.0"]


def test_falha_para_e_retomada_sem_duplicar_item(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    cliente_com_falha = ClienteFalso("1.1.0")

    with pytest.raises(FalhaPublicacao):
        executar_plano(plano(), autorizacao(), cliente_com_falha, caminho)

    cliente_sem_falha = ClienteFalso()
    executar_plano(plano(), autorizacao(), cliente_sem_falha, caminho)

    assert cliente_sem_falha.chaves_criadas == ["1.1.0"]


def test_autorizacao_invalida_nao_cria_item(tmp_path) -> None:
    cliente = ClienteFalso()

    with pytest.raises(PermissionError):
        executar_plano(
            plano(),
            Autorizacao("outro-hash", ModalidadeAutorizacao.INTEIRA),
            cliente,
            tmp_path / "mapa.json",
        )

    assert cliente.chaves_criadas == []


def test_autorizacao_por_lote_cria_somente_o_conjunto_autorizado(tmp_path) -> None:
    cliente = ClienteFalso()

    resultado = executar_plano(
        plano(), autorizacao_do_primeiro_lote(), cliente, tmp_path / "mapa.json"
    )

    assert resultado.itens == ("1.0.0",)
    assert cliente.chaves_criadas == ["1.0.0"]

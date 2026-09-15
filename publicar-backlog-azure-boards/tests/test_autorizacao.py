from io import StringIO

import pytest

from publicar_backlog_azure_boards.autorizacao import (
    ModalidadeAutorizacao,
    coletar_confirmacao,
    criar_autorizacao,
    criar_frase_confirmacao,
    criar_lotes,
    escolher_modalidade,
    validar_confirmacao,
)
from publicar_backlog_azure_boards.configuracao import carregar_configuracao
from publicar_backlog_azure_boards.modelos import ConfiguracaoPublicacao

CONFIGURACAO = ConfiguracaoPublicacao(
    organizacao="organizacao",
    projeto="Projeto",
    area_path="Projeto",
    iteration_path="Projeto\\Sprint 18",
)


def test_confirmacao_incorreta_e_rejeitada() -> None:
    esperada = criar_frase_confirmacao("7f3a9d", 3, CONFIGURACAO)

    assert validar_confirmacao("AUTORIZAR PUBLICAÇÃO 3 ITENS X 0000", esperada) is False


def test_confirmacao_exata_e_aceita() -> None:
    esperada = criar_frase_confirmacao("7f3a9d", 3, CONFIGURACAO)

    assert validar_confirmacao(esperada, esperada) is True


def test_confirmacao_parcial_e_rejeitada() -> None:
    esperada = criar_frase_confirmacao("7f3a9d", 3, CONFIGURACAO)

    assert validar_confirmacao("AUTORIZAR PUBLICAÇÃO", esperada) is False


def test_frase_de_lote_identifica_numero_e_quantidade() -> None:
    frase = criar_frase_confirmacao("b91c9d", 4, CONFIGURACAO, numero_lote=2)

    assert frase == "AUTORIZAR LOTE 2 4 ITENS Projeto Projeto Projeto\\Sprint 18 B91C"


def test_ausencia_de_confirmacao_nao_cria_autorizacao_operacional() -> None:
    autorizacao = criar_autorizacao(plano_hash="novo")

    assert autorizacao.valida_para("novo") is False


def test_confirmacao_exata_cria_autorizacao_operacional() -> None:
    plano_hash = "novo"
    confirmacao = criar_frase_confirmacao(plano_hash, 3, CONFIGURACAO)

    autorizacao = criar_autorizacao(
        plano_hash=plano_hash,
        confirmacao=confirmacao,
        quantidade=3,
        configuracao=CONFIGURACAO,
    )

    assert autorizacao.valida_para(plano_hash) is True


def test_confirmacao_incorreta_nao_cria_autorizacao_operacional() -> None:
    autorizacao = criar_autorizacao(
        plano_hash="novo",
        confirmacao="AUTORIZAR PUBLICAÇÃO 3 ITENS X 0000",
        quantidade=3,
        configuracao=CONFIGURACAO,
    )

    assert autorizacao.valida_para("novo") is False


def test_plano_alterado_invalida_autorizacao() -> None:
    plano_hash = "novo"
    confirmacao = criar_frase_confirmacao(plano_hash, 3, CONFIGURACAO)
    autorizacao = criar_autorizacao(
        plano_hash=plano_hash,
        confirmacao=confirmacao,
        quantidade=3,
        configuracao=CONFIGURACAO,
    )

    assert autorizacao.valida_para("antigo") is False


def test_coleta_confirmacao_remove_apenas_quebra_de_linha() -> None:
    esperada = criar_frase_confirmacao("novo", 3, CONFIGURACAO)

    confirmacao = coletar_confirmacao(StringIO(f"{esperada}\r\n"), StringIO())

    assert confirmacao == esperada


def test_escolha_de_modalidade_inteira() -> None:
    saida = StringIO()

    modalidade = escolher_modalidade(StringIO("1\n"), saida)

    assert modalidade is ModalidadeAutorizacao.INTEIRA
    assert "[2] Por lotes" in saida.getvalue()


def test_escolha_de_modalidade_permite_cancelamento() -> None:
    modalidade = escolher_modalidade(StringIO("C\n"), StringIO())

    assert modalidade is ModalidadeAutorizacao.CANCELADA


def test_modalidade_por_lotes_exige_tamanho_positivo() -> None:
    with pytest.raises(ValueError, match="positivo"):
        criar_lotes(total=5, tamanho=0)


def test_criar_lotes_divide_o_total_em_sequencia() -> None:
    lotes = criar_lotes(total=5, tamanho=2)

    faixas = [(lote.numero, lote.inicio, lote.fim) for lote in lotes]

    assert faixas == [(1, 0, 2), (2, 2, 4), (3, 4, 5)]


def test_argumento_tem_precedencia_sobre_arquivo_e_ambiente(tmp_path) -> None:
    arquivo = tmp_path / "publicador.toml"
    arquivo.write_text(
        """
[azure_devops]
organizacao = "organizacao-do-arquivo"
projeto = "projeto-do-arquivo"
area_path = "Area do arquivo"
iteration_path = "Iteracao do arquivo"
token = "token-do-arquivo"
""",
        encoding="utf-8",
    )
    ambiente = {
        "AZURE_DEVOPS_ORGANIZACAO": "organizacao-do-ambiente",
        "AZURE_DEVOPS_PROJETO": "projeto-do-ambiente",
        "AZURE_DEVOPS_AREA_PATH": "Area do ambiente",
        "AZURE_DEVOPS_ITERATION_PATH": "Iteracao do ambiente",
        "AZURE_DEVOPS_TOKEN": "token-do-ambiente",
    }

    configuracao = carregar_configuracao(
        argumentos={"projeto": "projeto-do-argumento"},
        caminho_arquivo=arquivo,
        ambiente=ambiente,
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert configuracao.publicacao.organizacao == "organizacao-do-arquivo"
    assert configuracao.publicacao.projeto == "projeto-do-argumento"
    assert configuracao.token.get_secret_value() == "token-do-arquivo"


def test_multiplos_area_paths_exigem_escolha_explicita() -> None:
    ambiente = {
        "AZURE_DEVOPS_ORGANIZACAO": "organizacao",
        "AZURE_DEVOPS_PROJETO": "Projeto",
        "AZURE_DEVOPS_TOKEN": "token",
        "AZURE_DEVOPS_AREA_PATHS": "Sustentacao,Projeto",
        "AZURE_DEVOPS_ITERATION_PATH": "Projeto\\Sprint 18",
    }

    configuracao = carregar_configuracao(
        ambiente=ambiente,
        entrada=StringIO("Projeto\n"),
        saida=StringIO(),
    )

    assert configuracao.publicacao.area_path == "Projeto"


def test_iteration_path_e_exigida_em_cada_execucao() -> None:
    ambiente = {
        "AZURE_DEVOPS_ORGANIZACAO": "organizacao",
        "AZURE_DEVOPS_PROJETO": "Projeto",
        "AZURE_DEVOPS_TOKEN": "token",
        "AZURE_DEVOPS_AREA_PATH": "Projeto",
    }

    configuracao = carregar_configuracao(
        ambiente=ambiente,
        entrada=StringIO("Projeto\\Sprint 18\n"),
        saida=StringIO(),
    )

    assert configuracao.publicacao.iteration_path == "Projeto\\Sprint 18"


def test_repr_da_configuracao_nao_expoe_token() -> None:
    configuracao = carregar_configuracao(
        ambiente={
            "AZURE_DEVOPS_ORGANIZACAO": "organizacao",
            "AZURE_DEVOPS_PROJETO": "Projeto",
            "AZURE_DEVOPS_TOKEN": "token-confidencial",
            "AZURE_DEVOPS_AREA_PATH": "Projeto",
            "AZURE_DEVOPS_ITERATION_PATH": "Projeto\\Sprint 18",
        },
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert "token-confidencial" not in repr(configuracao)

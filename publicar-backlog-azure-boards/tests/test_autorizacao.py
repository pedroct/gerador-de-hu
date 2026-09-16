from dataclasses import replace
from io import StringIO

import pytest

from publicar_backlog_azure_boards.autorizacao import (
    Autorizacao,
    ErroAutorizacao,
    ModalidadeAutorizacao,
    coletar_confirmacao,
    criar_autorizacao,
    criar_frase_confirmacao,
    criar_lotes,
    escolher_modalidade,
    imprimir_destino,
    imprimir_operacoes,
    validar_confirmacao,
)
from publicar_backlog_azure_boards.configuracao import carregar_configuracao
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    MapeamentoTipos,
    OperacaoCriacao,
    PlanoPublicacao,
    TipoItem,
)

CONFIGURACAO = ConfiguracaoPublicacao(
    organizacao="organizacao",
    projeto="Projeto",
    area_path="Projeto",
    iteration_path="Projeto\\Sprint 18",
)
PLANO = PlanoPublicacao(
    operacoes=(
        OperacaoCriacao("1.0.0", TipoItem.EPIC, "Épico", "<p>Descrição</p>", "", None, "Epic"),
        OperacaoCriacao(
            "1.1.0",
            TipoItem.FEATURE,
            "Feature",
            "<p>Descrição</p>",
            "",
            "1.0.0",
            "Feature",
        ),
    ),
    hash_plano="7f3a9d",
    configuracao=CONFIGURACAO,
)
PENDENTES = ("1.0.0", "1.1.0")


def _autorizacao_inteira(plano: PlanoPublicacao = PLANO):
    frase = criar_frase_confirmacao(plano, PENDENTES)
    return criar_autorizacao(
        plano,
        frase,
        frozenset(PENDENTES),
    )


def test_confirmacao_incorreta_e_rejeitada() -> None:
    esperada = criar_frase_confirmacao(PLANO, PENDENTES)

    assert validar_confirmacao("AUTORIZAR PUBLICAÇÃO 2 ITENS X 0000", esperada) is False


def test_confirmacao_exata_e_aceita() -> None:
    esperada = criar_frase_confirmacao(PLANO, PENDENTES)

    assert validar_confirmacao(esperada, esperada) is True


def test_confirmacao_nao_pode_ser_injetada_no_construtor() -> None:
    frase = criar_frase_confirmacao(PLANO, PENDENTES)
    chaves = frozenset(PENDENTES)

    with pytest.raises(ErroAutorizacao):
        Autorizacao(
            hash_plano=PLANO.hash_plano,
            quantidade=len(chaves),
            modalidade=ModalidadeAutorizacao.INTEIRA,
            chaves_autorizadas=chaves,
            impressao_destino=imprimir_destino(PLANO.configuracao),
            impressao_conteudo=imprimir_operacoes(PLANO, chaves),
            confirmacao=frase,
        )


def test_confirmacao_parcial_e_rejeitada() -> None:
    esperada = criar_frase_confirmacao(PLANO, PENDENTES)

    assert validar_confirmacao("AUTORIZAR PUBLICAÇÃO", esperada) is False


def test_frase_de_lote_identifica_numero_quantidade_e_destino() -> None:
    lote = criar_lotes(total=2, tamanho=1)[1]

    frase = criar_frase_confirmacao(PLANO, PENDENTES[lote.inicio : lote.fim], numero_lote=2)

    assert frase == "AUTORIZAR LOTE 2 1 ITENS Projeto Projeto Projeto\\Sprint 18 7F3A"


def test_ausencia_de_confirmacao_nao_cria_autorizacao_operacional() -> None:
    with pytest.raises(ErroAutorizacao):
        criar_autorizacao(PLANO, None, frozenset(PENDENTES))


def test_fabrica_exige_conjunto_imutavel_de_chaves() -> None:
    confirmacao = criar_frase_confirmacao(PLANO, PENDENTES)

    with pytest.raises(ValueError, match="imutável"):
        criar_autorizacao(PLANO, confirmacao, set(PENDENTES))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "plano_divergente",
    [
        replace(
            PLANO,
            operacoes=(replace(PLANO.operacoes[0], titulo="Épico alterado"), PLANO.operacoes[1]),
        ),
        replace(PLANO, operacoes=PLANO.operacoes[:1]),
        replace(PLANO, configuracao=replace(CONFIGURACAO, iteration_path="Projeto\\Sprint 19")),
        replace(
            PLANO,
            configuracao=replace(
                CONFIGURACAO,
                mapeamento_tipos=MapeamentoTipos(historia_usuario="Product Backlog Item"),
            ),
        ),
    ],
    ids=["conteudo", "quantidade", "destino", "mapeamento"],
)
def test_autorizacao_vincula_conteudo_quantidade_e_destino(
    plano_divergente: PlanoPublicacao,
) -> None:
    autorizacao = _autorizacao_inteira()

    assert autorizacao.valida_para(plano_divergente, plano_divergente.configuracao) is False


def test_autorizacao_inteira_vincula_conjunto_pendente_exato() -> None:
    autorizacao = _autorizacao_inteira()

    assert autorizacao.chaves_autorizadas == frozenset(PENDENTES)
    assert autorizacao.valida_para(PLANO, CONFIGURACAO) is True


def test_autorizacao_por_lote_vincula_faixa_e_conjunto() -> None:
    lote = criar_lotes(total=2, tamanho=1)[1]
    chaves_lote = PENDENTES[lote.inicio : lote.fim]
    confirmacao = criar_frase_confirmacao(PLANO, chaves_lote, numero_lote=lote.numero)

    autorizacao = criar_autorizacao(
        PLANO,
        confirmacao,
        frozenset(chaves_lote),
        modalidade=ModalidadeAutorizacao.LOTES,
        numero_lote=lote.numero,
    )

    assert autorizacao.chaves_autorizadas == frozenset({"1.1.0"})
    assert autorizacao.valida_para(PLANO, CONFIGURACAO) is True


def test_coleta_confirmacao_remove_apenas_quebra_de_linha() -> None:
    esperada = criar_frase_confirmacao(PLANO, PENDENTES)

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
area_path = "projeto-do-arquivo\\\\Area"
iteration_path = "projeto-do-arquivo\\\\Iteracao"
token = "token-do-arquivo"
""",
        encoding="utf-8",
    )
    ambiente = {
        "AZURE_DEVOPS_ORGANIZACAO": "organizacao-do-ambiente",
        "AZURE_DEVOPS_PROJETO": "projeto-do-ambiente",
        "AZURE_DEVOPS_AREA_PATH": "projeto-do-ambiente\\Area",
        "AZURE_DEVOPS_ITERATION_PATH": "projeto-do-ambiente\\Iteracao",
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
    assert configuracao.obter_token() == "token-do-arquivo"


def test_multiplos_area_paths_exigem_escolha_explicita() -> None:
    ambiente = {
        "AZURE_DEVOPS_ORGANIZACAO": "organizacao",
        "AZURE_DEVOPS_PROJETO": "Projeto",
        "AZURE_DEVOPS_TOKEN": "token",
        "AZURE_DEVOPS_AREA_PATHS": "Projeto\\Sustentacao,Projeto\\Produto",
        "AZURE_DEVOPS_ITERATION_PATH": "Projeto\\Sprint 18",
    }

    configuracao = carregar_configuracao(
        ambiente=ambiente,
        entrada=StringIO("Projeto\\Produto\n"),
        saida=StringIO(),
    )

    assert configuracao.publicacao.area_path == "Projeto\\Produto"


def test_area_path_relativo_e_normalizado_com_o_projeto() -> None:
    configuracao = carregar_configuracao(
        ambiente={
            "AZURE_DEVOPS_ORGANIZACAO": "organizacao",
            "AZURE_DEVOPS_PROJETO": "MeuProjeto",
            "AZURE_DEVOPS_TOKEN": "token",
            "AZURE_DEVOPS_AREA_PATH": "Sustentacao",
            "AZURE_DEVOPS_ITERATION_PATH": "MeuProjeto\\Sprint 18",
        },
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert configuracao.publicacao.area_path == "MeuProjeto\\Sustentacao"


def test_token_interativo_usa_leitura_sem_eco() -> None:
    prompts: list[str] = []

    configuracao = carregar_configuracao(
        ambiente={
            "AZURE_DEVOPS_ORGANIZACAO": "organizacao",
            "AZURE_DEVOPS_PROJETO": "Projeto",
            "AZURE_DEVOPS_AREA_PATH": "Projeto",
            "AZURE_DEVOPS_ITERATION_PATH": "Projeto\\Sprint 18",
        },
        entrada=StringIO("segredo-que-nao-deve-ser-lido\n"),
        saida=StringIO(),
        ler_segredo=lambda prompt: prompts.append(prompt) or "token-seguro",
    )

    assert configuracao.obter_token() == "token-seguro"
    assert prompts == ["Credencial do Azure DevOps: "]


def test_configuracao_sem_token_e_permitida_quando_nao_ha_http() -> None:
    configuracao = carregar_configuracao(
        ambiente={
            "AZURE_DEVOPS_ORGANIZACAO": "organizacao",
            "AZURE_DEVOPS_PROJETO": "Projeto",
            "AZURE_DEVOPS_AREA_PATH": "Projeto",
            "AZURE_DEVOPS_ITERATION_PATH": "Projeto\\Sprint 18",
            "AZURE_DEVOPS_TOKEN": "nao-deve-ser-lido",
        },
        entrada=StringIO(),
        saida=StringIO(),
        exigir_token=False,
    )

    assert configuracao.token is None


def test_mapeamento_remoto_e_carregado_do_ambiente() -> None:
    configuracao = carregar_configuracao(
        ambiente={
            "AZURE_DEVOPS_ORGANIZACAO": "organizacao",
            "AZURE_DEVOPS_PROJETO": "Projeto",
            "AZURE_DEVOPS_AREA_PATH": "Projeto",
            "AZURE_DEVOPS_ITERATION_PATH": "Projeto\\Sprint 18",
            "AZURE_DEVOPS_TOKEN": "token",
            "AZURE_DEVOPS_TIPO_USER_STORY": "Product Backlog Item",
        },
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert configuracao.publicacao.mapeamento_tipos.historia_usuario == "Product Backlog Item"


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

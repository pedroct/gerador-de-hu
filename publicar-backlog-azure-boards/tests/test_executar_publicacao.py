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
    ErroReconciliacaoPendente,
    Manifesto,
    ReconciliacaoManualNecessaria,
    ReconciliacaoPendente,
    gravar_manifesto,
    ler_manifesto,
)
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemPreexistente,
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
        self.predecessores_por_chave: dict[str, tuple[int, ...]] = {}

    def criar_item(
        self,
        operacao: OperacaoCriacao,
        id_pai: int | None = None,
        ids_predecessores: tuple[int, ...] = (),
    ):
        if operacao.chave == self.falhar_na_chave:
            raise self.erro
        self.chaves_criadas.append(operacao.chave)
        self.predecessores_por_chave[operacao.chave] = tuple(ids_predecessores)
        return RegistroManifesto(
            len(self.chaves_criadas), operacao.tipo, f"https://exemplo/{operacao.chave}"
        )

    def url_do_item(self, id_item: int) -> str:
        return f"https://exemplo/workItems/{id_item}"


def plano_com_dependencia() -> PlanoPublicacao:
    return PlanoPublicacao(
        operacoes=(
            OperacaoCriacao("1.0.0", TipoItem.EPIC, "Épico", "", "", None, "Epic"),
            OperacaoCriacao("1.1.0", TipoItem.FEATURE, "Feature", "", "", "1.0.0", "Feature"),
            OperacaoCriacao(
                "1.1.2", TipoItem.HISTORIA_USUARIO, "Design", "", "", "1.1.0", "User Story"
            ),
            OperacaoCriacao(
                "1.1.1",
                TipoItem.HISTORIA_USUARIO,
                "Funcional",
                "",
                "",
                "1.1.0",
                "User Story",
                depende_de=("1.1.2",),
            ),
        ),
        hash_plano="hash-dependencia",
        configuracao=CONFIGURACAO,
    )


def autorizacao_com_dependencia(chaves_pendentes: tuple[str, ...]):
    plano_atual = plano_com_dependencia()
    confirmacao = criar_frase_confirmacao(plano_atual, chaves_pendentes)
    return criar_autorizacao(plano_atual, confirmacao, frozenset(chaves_pendentes))


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
    assert manifesto.reconciliacao_pendente.destino == CONFIGURACAO
    assert manifesto.reconciliacao_pendente.tipo is TipoItem.EPIC
    assert manifesto.reconciliacao_pendente.hash_plano == "hash"
    assert manifesto.reconciliacao_pendente.timestamp
    assert manifesto.reconciliacao_pendente.motivo
    assert manifesto.reconciliacao_pendente.resolucao == "pendente"

    cliente_novo = ClienteFalso()
    with pytest.raises(ReconciliacaoManualNecessaria):
        executar_plano(plano(), autorizacao(), cliente_novo, caminho)
    assert cliente_novo.chaves_criadas == []


def test_reconciliacao_pendente_bloqueia_nova_criacao_com_erro_especifico(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    pendencia = ReconciliacaoPendente(
        chave="1.0.0",
        tipo_remoto="Epic",
        titulo="Épico",
        destino=CONFIGURACAO,
        hash_plano="hash",
        timestamp="2026-09-16T15:00:00+00:00",
        motivo="timeout após envio",
    )
    gravar_manifesto(
        caminho,
        Manifesto(
            hash_plano="hash",
            configuracao=CONFIGURACAO,
            reconciliacoes={"1.0.0": pendencia},
        ),
    )
    cliente = ClienteFalso()

    with pytest.raises(ErroReconciliacaoPendente):
        executar_plano(plano(), autorizacao(), cliente, caminho)

    assert cliente.chaves_criadas == []


def test_passa_o_id_do_predecessor_criado_na_mesma_rodada(tmp_path) -> None:
    cliente = ClienteFalso()

    executar_plano(
        plano_com_dependencia(),
        autorizacao_com_dependencia(("1.0.0", "1.1.0", "1.1.2", "1.1.1")),
        cliente,
        tmp_path / "mapa.json",
    )

    id_do_design = ler_manifesto(tmp_path / "mapa.json").itens["1.1.2"].id
    assert cliente.predecessores_por_chave["1.1.1"] == (id_do_design,)


def test_resolve_predecessor_publicado_em_rodada_anterior(tmp_path) -> None:
    caminho = tmp_path / "mapa.json"
    cliente_com_falha = ClienteFalso("1.1.1")

    with pytest.raises(FalhaPublicacao):
        executar_plano(
            plano_com_dependencia(),
            autorizacao_com_dependencia(("1.0.0", "1.1.0", "1.1.2", "1.1.1")),
            cliente_com_falha,
            caminho,
        )

    id_do_design = ler_manifesto(caminho).itens["1.1.2"].id
    cliente_sem_falha = ClienteFalso()
    executar_plano(
        plano_com_dependencia(), autorizacao_com_dependencia(("1.1.1",)), cliente_sem_falha, caminho
    )

    assert cliente_sem_falha.chaves_criadas == ["1.1.1"]
    assert cliente_sem_falha.predecessores_por_chave["1.1.1"] == (id_do_design,)


def test_recusa_quando_o_predecessor_nao_foi_publicado(tmp_path) -> None:
    cliente = ClienteFalso()

    with pytest.raises(ValueError, match="predecessor 1.1.2"):
        executar_plano(
            plano_com_dependencia(),
            autorizacao_com_dependencia(("1.1.1",)),
            cliente,
            tmp_path / "mapa.json",
        )


def test_item_preexistente_nao_e_recriado_e_serve_de_pai(tmp_path) -> None:
    plano_com_epic_existente = PlanoPublicacao(
        operacoes=(
            OperacaoCriacao("1.1.0", TipoItem.FEATURE, "Feature", "", "", "1.0.0", "Feature"),
        ),
        hash_plano="hash-preexistente",
        configuracao=CONFIGURACAO,
        preexistentes=(ItemPreexistente("1.0.0", TipoItem.EPIC, 4721),),
    )
    confirmacao = criar_frase_confirmacao(plano_com_epic_existente, ("1.1.0",))
    autorizacao_atual = criar_autorizacao(
        plano_com_epic_existente, confirmacao, frozenset(("1.1.0",))
    )
    cliente = ClienteFalso()

    executar_plano(plano_com_epic_existente, autorizacao_atual, cliente, tmp_path / "mapa.json")

    assert cliente.chaves_criadas == ["1.1.0"]
    manifesto = ler_manifesto(tmp_path / "mapa.json")
    assert manifesto.itens["1.0.0"].id == 4721
    assert manifesto.itens["1.0.0"].preexistente is True
    assert manifesto.itens["1.1.0"].preexistente is False


def test_segunda_rodada_sobre_manifesto_com_preexistente_nao_estoura(tmp_path) -> None:
    """Ponta a ponta: executar, gravar, e executar de novo sobre o mesmo manifesto.

    Reproduz o cenário que motiva a Tarefa 7 inteira — a segunda rodada sobre o mesmo
    backlog encontra o Epic já publicado — e prova que `executar_plano` (que chama
    `validar_manifesto` internamente a cada rodada) não estoura ao reencontrar o registro
    pré-existente que a primeira rodada persistiu.
    """
    plano_com_epic_existente = PlanoPublicacao(
        operacoes=(
            OperacaoCriacao("1.1.0", TipoItem.FEATURE, "Feature", "", "", "1.0.0", "Feature"),
            OperacaoCriacao(
                "1.1.1", TipoItem.HISTORIA_USUARIO, "História", "", "", "1.1.0", "User Story"
            ),
        ),
        hash_plano="hash-preexistente-rodada-2",
        configuracao=CONFIGURACAO,
        preexistentes=(ItemPreexistente("1.0.0", TipoItem.EPIC, 4721),),
    )
    caminho = tmp_path / "mapa.json"
    cliente = ClienteFalso()

    confirmacao_1 = criar_frase_confirmacao(plano_com_epic_existente, ("1.1.0",))
    autorizacao_1 = criar_autorizacao(
        plano_com_epic_existente, confirmacao_1, frozenset(("1.1.0",))
    )
    executar_plano(plano_com_epic_existente, autorizacao_1, cliente, caminho)

    confirmacao_2 = criar_frase_confirmacao(plano_com_epic_existente, ("1.1.1",))
    autorizacao_2 = criar_autorizacao(
        plano_com_epic_existente, confirmacao_2, frozenset(("1.1.1",))
    )
    executar_plano(plano_com_epic_existente, autorizacao_2, cliente, caminho)

    assert cliente.chaves_criadas == ["1.1.0", "1.1.1"]
    manifesto = ler_manifesto(caminho)
    assert manifesto.itens["1.0.0"].preexistente is True
    assert set(manifesto.itens) == {"1.0.0", "1.1.0", "1.1.1"}

"""Orquestra a CLI de publicação autorizada."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, TextIO, cast

from publicar_backlog_demanda_azure_boards.autorizacao import (
    Autorizacao,
    ErroAutorizacao,
    Lote,
    ModalidadeAutorizacao,
    coletar_confirmacao,
    criar_autorizacao,
    criar_frase_confirmacao,
    escolher_modalidade,
)
from publicar_backlog_demanda_azure_boards.cliente_azure_devops import ClienteAzureDevOps
from publicar_backlog_demanda_azure_boards.configuracao import (
    ConfiguracaoAzureDevOps,
    carregar_configuracao,
)
from publicar_backlog_demanda_azure_boards.executar_publicacao import executar_plano
from publicar_backlog_demanda_azure_boards.interpretar_markdown import (
    extrair_data_geracao,
    interpretar_backlog,
)
from publicar_backlog_demanda_azure_boards.leitor_demanda import ler_demanda
from publicar_backlog_demanda_azure_boards.manifesto import ler_manifesto, validar_manifesto
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    Demanda,
    ItemBacklog,
    ItemPreexistente,
    OperacaoCriacao,
    PlanoPublicacao,
)
from publicar_backlog_demanda_azure_boards.planejar_publicacao import criar_plano
from publicar_backlog_demanda_azure_boards.validacao_estrutural import validar_estrutura_backlog

_MAX_TENTATIVAS_CONFIRMACAO = 3


class IdentidadeCriada(Protocol):
    """Campos mínimos retornados por uma criação."""

    id: int
    url: str


class ClientePublicacao(Protocol):
    """Interface mínima consumida pela orquestração da CLI."""

    configuracao: ConfiguracaoPublicacao

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> object: ...

    def validar_operacao(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> None: ...

    def verificar_item_existente(self, id_item: int, tipo_esperado: str) -> None: ...

    def tipos_sem_criterios_aceitacao(self) -> frozenset[str]: ...

    def criar_item(
        self,
        operacao: OperacaoCriacao,
        id_pai: int | None = None,
        ids_predecessores: tuple[int, ...] = (),
    ) -> IdentidadeCriada: ...

    def url_do_item(self, id_item: int) -> str: ...


def construir_parser() -> argparse.ArgumentParser:
    """Monta a interface de comandos da ferramenta."""
    parser = argparse.ArgumentParser(
        prog="publicar-backlog-demanda-azure-boards",
        description="Valida, planeja e publica um backlog com autorização explícita.",
    )
    comandos = parser.add_subparsers(dest="comando", required=True)

    validar = comandos.add_parser("validar", help="valida o contrato Markdown localmente")
    validar.add_argument("backlog", type=Path)

    planejar = comandos.add_parser(
        "planejar", help="lê a Demanda e apresenta o plano, sem autorização nem criação"
    )
    planejar.add_argument("backlog", type=Path)
    _adicionar_opcoes_configuracao(planejar)

    publicar = comandos.add_parser("publicar", help="verifica e publica após confirmação")
    publicar.add_argument("backlog", type=Path)
    _adicionar_opcoes_configuracao(publicar)
    publicar.add_argument(
        "--manifesto",
        type=Path,
        default=Path("manifesto-publicacao.json"),
        help="arquivo local para retomada da publicação",
    )
    modos = publicar.add_mutually_exclusive_group()
    modos.add_argument(
        "--simulacao",
        action="store_true",
        help="lê a Demanda e planeja; não pede autorização e não cria item algum",
    )
    modos.add_argument(
        "--validar-apenas",
        action="store_true",
        help="executa a verificação remota e não solicita autorização",
    )
    return parser


def _adicionar_opcoes_configuracao(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--organizacao")
    parser.add_argument("--projeto")
    parser.add_argument("--demanda", dest="demanda_id")
    parser.add_argument("--tipo-demanda")
    parser.add_argument("--tipo-epic")
    parser.add_argument("--tipo-feature")
    parser.add_argument("--tipo-user-story")
    parser.add_argument("--tipo-bug")
    parser.add_argument("--config", dest="caminho_configuracao", type=Path)
    parser.add_argument("--env-file", dest="caminho_env", type=Path, default=Path(".env"))


def principal(
    argumentos: Sequence[str] | None = None,
    *,
    cliente: ClientePublicacao | None = None,
    entrada: TextIO | None = None,
    saida: TextIO | None = None,
) -> int:
    """Executa um comando e devolve seu código, sem esconder falhas operacionais."""
    argumentos_parseados = construir_parser().parse_args(argumentos)
    entrada_real = sys.stdin if entrada is None else entrada
    saida_real = sys.stdout if saida is None else saida
    try:
        itens, data_geracao = _carregar_backlog_validado(argumentos_parseados.backlog)
        if argumentos_parseados.comando == "validar":
            _escrever(saida_real, f"Backlog válido: {len(itens)} itens.\n")
            return 0

        configuracao = _carregar_configuracao(
            argumentos_parseados, cliente, entrada_real, saida_real
        )
        demanda: Demanda | None = None
        if isinstance(configuracao, _ConfiguracaoLocal):
            # Destino já pronto, vindo de cliente injetado: não há token para ler a
            # Demanda, e o cliente é a autoridade sobre onde publicar.
            destino = configuracao.publicacao
        else:
            demanda = ler_demanda(
                configuracao.organizacao,
                configuracao.projeto,
                configuracao.obter_token(),
                configuracao.demanda_id,
                configuracao.tipo_demanda,
            )
            destino = configuracao.publicacao_para(demanda)
        plano = criar_plano(itens, destino, data_geracao)
        if argumentos_parseados.comando == "publicar":
            manifesto = ler_manifesto(argumentos_parseados.manifesto)
            pendentes = validar_manifesto(manifesto, plano, destino)
            caminho_manifesto: Path | None = argumentos_parseados.manifesto
            registrados = len(manifesto.itens)
        else:
            pendentes = plano.operacoes
            caminho_manifesto = None
            registrados = 0
        _apresentar_plano(
            plano,
            pendentes,
            len(itens),
            registrados,
            caminho_manifesto,
            saida_real,
            demanda,
            data_geracao,
        )

        if argumentos_parseados.comando == "planejar":
            return 0
        if argumentos_parseados.simulacao:
            _escrever(
                saida_real,
                "Simulação concluída: a Demanda foi lida; "
                "nenhuma autorização foi solicitada e nenhum item foi criado.\n",
            )
            return 0

        cliente_real = cliente or cast(
            ClientePublicacao,
            ClienteAzureDevOps(
                destino,
                configuracao.obter_token(),
            ),
        )
        _verificar_preliminar(
            cliente_real,
            destino,
            pendentes,
            plano.preexistentes,
        )
        _avisar_criterios_descartados(cliente_real, pendentes, saida_real)
        if argumentos_parseados.validar_apenas:
            _escrever(saida_real, "Validação preliminar concluída sem chamadas de criação.\n")
            return 0
        return _publicar(
            plano,
            pendentes,
            cliente_real,
            argumentos_parseados.manifesto,
            entrada_real,
            saida_real,
        )
    except (OSError, ValueError, RuntimeError, PermissionError) as erro:
        _escrever(saida_real, f"Erro: {erro}\n")
        return 1


def _carregar_backlog_validado(caminho: Path) -> tuple[list[ItemBacklog], str]:
    validar_estrutura_backlog(caminho)
    return interpretar_backlog(caminho), extrair_data_geracao(caminho)


def _carregar_configuracao(
    argumentos: argparse.Namespace,
    cliente: ClientePublicacao | None,
    entrada: TextIO,
    saida: TextIO,
) -> ConfiguracaoAzureDevOps | _ConfiguracaoLocal:
    nomes = (
        "organizacao",
        "projeto",
        "demanda_id",
        "tipo_demanda",
        "tipo_epic",
        "tipo_feature",
        "tipo_user_story",
        "tipo_bug",
    )
    if cliente is not None and not any(
        getattr(argumentos, nome, None) for nome in (*nomes, "caminho_configuracao")
    ):
        return _ConfiguracaoLocal(cliente.configuracao)
    valores = {nome: getattr(argumentos, nome, None) for nome in nomes}
    # `planejar` e `--simulacao` passaram a exigir token porque ambos precisam ler a
    # Demanda para derivar Area Path e Iteration Path; sem isso não há plano nem hash.
    exige_token = argumentos.comando in {"planejar", "publicar"} and cliente is None
    return carregar_configuracao(
        argumentos=valores,
        caminho_arquivo=getattr(argumentos, "caminho_configuracao", None),
        caminho_env=getattr(argumentos, "caminho_env", Path(".env")),
        entrada=entrada,
        saida=saida,
        exigir_token=exige_token,
    )


class _ConfiguracaoLocal:
    """Destino já fornecido por cliente injetado em testes e integrações locais."""

    def __init__(self, publicacao: ConfiguracaoPublicacao) -> None:
        self.publicacao = publicacao

    def obter_token(self) -> str:
        raise RuntimeError("Um fluxo local não possui token.")


def _verificar_preliminar(
    cliente: ClientePublicacao,
    configuracao: ConfiguracaoPublicacao,
    operacoes: Sequence[OperacaoCriacao],
    preexistentes: Sequence[ItemPreexistente] = (),
) -> None:
    cliente.verificar_destino(configuracao)
    for preexistente in preexistentes:
        # Confere o ID declarado antes de qualquer autorização: pendurar um filho num
        # work item errado (ou inexistente) é caro de desfazer depois de criado.
        tipo_remoto = configuracao.mapeamento_tipos.nome_remoto(preexistente.tipo)
        cliente.verificar_item_existente(preexistente.id, tipo_remoto)
    for operacao in operacoes:
        # Item sem pai documental é um Épico, e o pai dele — a Demanda — já existe no
        # Azure Boards. Features e Histórias validam sem pai: os seus ainda não foram
        # criados.
        id_pai = configuracao.demanda_id if operacao.chave_pai is None else None
        cliente.validar_operacao(operacao, id_pai=id_pai)


def _avisar_criterios_descartados(
    cliente: ClientePublicacao,
    pendentes: Sequence[OperacaoCriacao],
    saida: TextIO,
) -> None:
    """Denuncia, antes da autorização, o conteúdo que a criação vai descartar.

    Quando o processo remoto não expõe o campo de critérios para um tipo, a criação
    omite o campo em vez de falhar. Sem este aviso, quem autoriza acredita estar
    publicando critérios que nunca chegam ao Azure Boards.
    """
    tipos_limitados = cliente.tipos_sem_criterios_aceitacao()
    if not tipos_limitados:
        return
    afetados = [
        operacao
        for operacao in pendentes
        if operacao.criterios_aceitacao.strip() and operacao.tipo_remoto in tipos_limitados
    ]
    if not afetados:
        return
    _escrever(
        saida,
        "\nATENÇÃO: os critérios de aceitação destes itens NÃO serão publicados, "
        "porque o tipo remoto não expõe o campo neste projeto:\n",
    )
    for operacao in afetados:
        _escrever(saida, f"  {operacao.chave} [{operacao.tipo_remoto}] {operacao.titulo}\n")
    _escrever(
        saida,
        "O restante do item é publicado normalmente. Cancele se isso não for aceitável.\n\n",
    )


def _apresentar_plano(
    plano: PlanoPublicacao,
    pendentes: Sequence[OperacaoCriacao],
    total: int,
    registrados: int,
    caminho_manifesto: Path | None,
    saida: TextIO,
    demanda: Demanda | None = None,
    data_geracao: str = "",
) -> None:
    configuracao = plano.configuracao
    contagem = Counter(operacao.tipo_remoto for operacao in pendentes)
    _escrever(saida, "Plano de publicação\n")
    rotulo_demanda = f"#{configuracao.demanda_id}"
    if demanda is not None:
        rotulo_demanda = f"#{demanda.id} — {demanda.titulo}"
    _escrever(saida, f"Demanda de Negócio: {rotulo_demanda}\n")
    _escrever(saida, f"Organização: {configuracao.organizacao}\n")
    _escrever(saida, f"Projeto: {configuracao.projeto}\n")
    heranca = f" (herdado da Demanda #{configuracao.demanda_id})"
    _escrever(saida, f"Area Path: {configuracao.area_path}{heranca}\n")
    _escrever(saida, f"Iteration Path: {configuracao.iteration_path}{heranca}\n")
    if data_geracao:
        # Sem a data no título, esta linha é o único sinal na tela de qual geração do
        # backlog está sendo autorizada; o hash protege, mas não se lê.
        _escrever(saida, f"Backlog gerado em: {data_geracao}\n")
    _escrever(saida, f"Mapeamento de tipos: {configuracao.mapeamento_tipos.como_dict()}\n")
    _escrever(saida, f"Itens totais: {total}\n")
    _escrever(saida, f"Itens novos: {len(pendentes)}\n")
    _escrever(saida, f"Itens registrados no manifesto: {registrados}\n")
    _escrever(saida, f"Por tipo remoto: {dict(contagem)}\n")
    _escrever(saida, f"Ordem: {', '.join(op.chave for op in pendentes) or 'nenhuma'}\n")
    relacoes = ", ".join(
        f"{operacao.chave} <- {operacao.chave_pai}"
        for operacao in pendentes
        if operacao.chave_pai is not None
    )
    _escrever(saida, f"Relações pai-filho: {relacoes or 'nenhuma'}\n")
    epicos = ", ".join(operacao.chave for operacao in pendentes if operacao.chave_pai is None)
    _escrever(
        saida,
        f"Épicos filhos da Demanda #{configuracao.demanda_id}: {epicos or 'nenhum'}\n",
    )
    _escrever(saida, f"Hash do plano: {plano.hash_plano}\n")
    if caminho_manifesto is not None:
        _escrever(saida, f"Manifesto: {caminho_manifesto}\n")


def _publicar(
    plano: PlanoPublicacao,
    pendentes: Sequence[OperacaoCriacao],
    cliente: ClientePublicacao,
    caminho_manifesto: Path,
    entrada: TextIO,
    saida: TextIO,
) -> int:
    chaves_pendentes = tuple(operacao.chave for operacao in pendentes)
    if not chaves_pendentes:
        _escrever(saida, "Nenhum item novo para publicar.\n")
        return 0

    modalidade = escolher_modalidade(entrada, saida)
    if modalidade is ModalidadeAutorizacao.CANCELADA:
        _escrever(saida, "Publicação cancelada; nenhuma chamada de criação foi realizada.\n")
        return 0
    if modalidade is ModalidadeAutorizacao.INTEIRA:
        autorizacao = _solicitar_autorizacao(
            plano,
            chaves_pendentes,
            ModalidadeAutorizacao.INTEIRA,
            entrada,
            saida,
        )
        if autorizacao is None:
            return 2
        resultado = executar_plano(plano, autorizacao, cliente, caminho_manifesto)
        _escrever(saida, f"Publicação concluída: {len(resultado.itens)} itens.\n")
        return 0

    tamanho = _solicitar_tamanho_lote(entrada, saida)
    restantes = chaves_pendentes
    numero_lote = 1
    while restantes:
        lote = Lote(numero=numero_lote, inicio=0, fim=min(tamanho, len(restantes)))
        chaves_lote = restantes[lote.inicio : lote.fim]
        _escrever(saida, f"Lote {numero_lote}: {', '.join(chaves_lote)}\n")
        autorizacao = _solicitar_autorizacao(
            plano,
            restantes,
            ModalidadeAutorizacao.LOTES,
            entrada,
            saida,
            lote=lote,
        )
        if autorizacao is None:
            return 2
        executar_plano(plano, autorizacao, cliente, caminho_manifesto)
        restantes = restantes[lote.fim :]
        numero_lote += 1
    _escrever(saida, "Publicação concluída por lotes.\n")
    return 0


def _solicitar_autorizacao(
    plano: PlanoPublicacao,
    chaves_pendentes: Sequence[str],
    modalidade: ModalidadeAutorizacao,
    entrada: TextIO,
    saida: TextIO,
    *,
    lote: Lote | None = None,
) -> Autorizacao | None:
    chaves = tuple(chaves_pendentes)
    autorizadas = chaves if lote is None else chaves[lote.inicio : lote.fim]
    numero_lote = None if lote is None else lote.numero
    frase = criar_frase_confirmacao(plano, autorizadas, numero_lote)
    _escrever(saida, f"Digite exatamente: {frase}\n")
    for tentativa in range(1, _MAX_TENTATIVAS_CONFIRMACAO + 1):
        confirmacao = coletar_confirmacao(entrada, saida)
        if confirmacao is None:
            break
        try:
            autorizacao = criar_autorizacao(
                plano,
                confirmacao,
                frozenset(autorizadas),
                modalidade=modalidade,
                numero_lote=numero_lote,
            )
        except ErroAutorizacao:
            autorizacao = None
        if autorizacao is not None and autorizacao.valida_para(plano, plano.configuracao):
            return autorizacao
        if tentativa < _MAX_TENTATIVAS_CONFIRMACAO:
            _escrever(
                saida,
                "Confirmação não corresponde ao texto exibido (a comparação diferencia "
                f"maiúsculas de minúsculas). Tentativa {tentativa} de "
                f"{_MAX_TENTATIVAS_CONFIRMACAO}; digite novamente.\n",
            )
    _escrever(saida, "Confirmação inválida; nenhuma chamada de criação foi realizada.\n")
    return None


def _solicitar_tamanho_lote(entrada: TextIO, saida: TextIO) -> int:
    while True:
        _escrever(saida, "Tamanho do lote: ")
        valor = entrada.readline()
        if not valor:
            raise ValueError("A entrada foi encerrada antes do tamanho do lote.")
        try:
            tamanho = int(valor.strip())
            if tamanho <= 0:
                raise ValueError
            return tamanho
        except (AttributeError, ValueError):
            _escrever(saida, "Informe um tamanho de lote inteiro e positivo.\n")


def _escrever(saida: TextIO, texto: str) -> None:
    saida.write(texto)

"""Orquestra a CLI de publicação autorizada."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, TextIO, cast

from publicar_backlog_azure_boards.autorizacao import (
    Autorizacao,
    ErroAutorizacao,
    Lote,
    ModalidadeAutorizacao,
    coletar_confirmacao,
    criar_autorizacao,
    criar_frase_confirmacao,
    escolher_modalidade,
)
from publicar_backlog_azure_boards.cliente_azure_devops import ClienteAzureDevOps
from publicar_backlog_azure_boards.configuracao import (
    ConfiguracaoAzureDevOps,
    carregar_configuracao,
)
from publicar_backlog_azure_boards.executar_publicacao import executar_plano
from publicar_backlog_azure_boards.interpretar_markdown import (
    extrair_data_geracao,
    interpretar_backlog,
)
from publicar_backlog_azure_boards.manifesto import ler_manifesto, validar_manifesto
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    OperacaoCriacao,
    PlanoPublicacao,
)
from publicar_backlog_azure_boards.planejar_publicacao import criar_plano
from publicar_backlog_azure_boards.validacao_estrutural import validar_estrutura_backlog

_MAX_TENTATIVAS_CONFIRMACAO = 3


class IdentidadeCriada(Protocol):
    """Campos mínimos retornados por uma criação."""

    id: int
    url: str


class ClientePublicacao(Protocol):
    """Interface mínima consumida pela orquestração da CLI."""

    configuracao: ConfiguracaoPublicacao

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> object: ...

    def validar_operacao(self, operacao: OperacaoCriacao) -> None: ...

    def criar_item(
        self, operacao: OperacaoCriacao, id_pai: int | None = None
    ) -> IdentidadeCriada: ...


def construir_parser() -> argparse.ArgumentParser:
    """Monta a interface de comandos da ferramenta."""
    parser = argparse.ArgumentParser(
        prog="publicar-backlog-azure-boards",
        description="Valida, planeja e publica um backlog com autorização explícita.",
    )
    comandos = parser.add_subparsers(dest="comando", required=True)

    validar = comandos.add_parser("validar", help="valida o contrato Markdown localmente")
    validar.add_argument("backlog", type=Path)

    planejar = comandos.add_parser("planejar", help="apresenta o plano sem chamadas remotas")
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
        help="planeja localmente sem token, autorização ou HTTP",
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
    parser.add_argument("--area-path")
    parser.add_argument("--iteration-path")
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
        plano = criar_plano(itens, configuracao.publicacao, data_geracao)
        if argumentos_parseados.comando == "publicar":
            manifesto = ler_manifesto(argumentos_parseados.manifesto)
            pendentes = validar_manifesto(manifesto, plano, configuracao.publicacao)
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
        )

        if argumentos_parseados.comando == "planejar":
            return 0
        if argumentos_parseados.simulacao:
            _escrever(
                saida_real,
                "Simulação local concluída: token não solicitado; "
                "nenhuma chamada HTTP realizada.\n",
            )
            return 0

        cliente_real = cliente or cast(
            ClientePublicacao,
            ClienteAzureDevOps(
                configuracao.publicacao,
                configuracao.obter_token(),
            ),
        )
        _verificar_preliminar(
            cliente_real,
            configuracao.publicacao,
            pendentes,
        )
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
        "area_path",
        "iteration_path",
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
    exige_token = (
        argumentos.comando == "publicar"
        and not getattr(argumentos, "simulacao", False)
        and cliente is None
    )
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
) -> None:
    cliente.verificar_destino(configuracao)
    for operacao in operacoes:
        cliente.validar_operacao(operacao)


def _apresentar_plano(
    plano: PlanoPublicacao,
    pendentes: Sequence[OperacaoCriacao],
    total: int,
    registrados: int,
    caminho_manifesto: Path | None,
    saida: TextIO,
) -> None:
    configuracao = plano.configuracao
    contagem = Counter(operacao.tipo_remoto for operacao in pendentes)
    _escrever(saida, "Plano de publicação\n")
    _escrever(saida, f"Organização: {configuracao.organizacao}\n")
    _escrever(saida, f"Projeto: {configuracao.projeto}\n")
    _escrever(saida, f"Area Path: {configuracao.area_path}\n")
    _escrever(saida, f"Iteration Path: {configuracao.iteration_path}\n")
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

"""Ponto de entrada da CLI de publicação autorizada."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, TextIO

if __package__ in {None, ""}:
    _raiz_projeto = Path(__file__).resolve().parents[1]
    _origem = str(_raiz_projeto / "src")
    if _origem not in sys.path:
        sys.path.insert(0, _origem)

from publicar_backlog_azure_boards.autorizacao import (  # noqa: E402
    ModalidadeAutorizacao,
    coletar_confirmacao,
    criar_autorizacao,
    criar_frase_confirmacao,
    criar_lotes,
    escolher_modalidade,
)
from publicar_backlog_azure_boards.cliente_azure_devops import (  # noqa: E402
    ClienteAzureDevOps,
)
from publicar_backlog_azure_boards.configuracao import (  # noqa: E402
    ConfiguracaoAzureDevOps,
    carregar_configuracao,
)
from publicar_backlog_azure_boards.executar_publicacao import (  # noqa: E402
    executar_plano,
)
from publicar_backlog_azure_boards.interpretar_markdown import (  # noqa: E402
    interpretar_backlog,
)
from publicar_backlog_azure_boards.manifesto import ler_manifesto  # noqa: E402
from publicar_backlog_azure_boards.modelos import (  # noqa: E402
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    PlanoPublicacao,
)
from publicar_backlog_azure_boards.planejar_publicacao import (  # noqa: E402
    criar_plano,
)


class ClientePublicacao(Protocol):
    """Interface mínima consumida pela orquestração da CLI."""

    configuracao: ConfiguracaoPublicacao

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> object: ...

    def validar_operacao(self, operacao: OperacaoCriacao) -> None: ...


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
        help="executa a verificação preliminar sem chamadas de criação",
    )
    modos.add_argument(
        "--validar-apenas",
        action="store_true",
        help="executa a verificação preliminar e não solicita autorização",
    )
    return parser


def _adicionar_opcoes_configuracao(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--organizacao")
    parser.add_argument("--projeto")
    parser.add_argument("--area-path")
    parser.add_argument("--iteration-path")
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
    parser = construir_parser()
    argumentos_parseados = parser.parse_args(argumentos)
    entrada_real = sys.stdin if entrada is None else entrada
    saida_real = sys.stdout if saida is None else saida

    try:
        if argumentos_parseados.comando == "validar":
            return _validar(argumentos_parseados.backlog, saida_real)
        configuracao = _carregar_configuracao(
            argumentos_parseados, cliente, entrada_real, saida_real
        )
        itens = interpretar_backlog(argumentos_parseados.backlog)
        manifesto = (
            ler_manifesto(argumentos_parseados.manifesto)
            if hasattr(argumentos_parseados, "manifesto")
            else None
        )
        registros = {} if manifesto is None else manifesto.itens
        plano = criar_plano(itens, configuracao.publicacao, registros)
        _apresentar_plano(
            plano,
            configuracao.publicacao,
            len(itens),
            len(registros),
            argumentos_parseados.manifesto if manifesto is not None else None,
            saida_real,
        )

        if argumentos_parseados.comando == "planejar":
            return 0

        cliente_real = cliente or ClienteAzureDevOps(
            configuracao.publicacao,
            configuracao.token.get_secret_value(),
        )
        _verificar_preliminar(cliente_real, configuracao.publicacao, plano)
        if argumentos_parseados.simulacao:
            _escrever(
                saida_real,
                "Simulação concluída: nenhuma chamada de criação foi realizada.\n",
            )
            return 0
        if argumentos_parseados.validar_apenas:
            _escrever(saida_real, "Validação preliminar concluída sem chamadas de criação.\n")
            return 0
        return _publicar(
            plano,
            configuracao.publicacao,
            cliente_real,
            argumentos_parseados.manifesto,
            entrada_real,
            saida_real,
        )
    except (OSError, ValueError, RuntimeError, PermissionError) as erro:
        _escrever(saida_real, f"Erro: {erro}\n")
        return 1


def _carregar_configuracao(
    argumentos: argparse.Namespace,
    cliente: ClientePublicacao | None,
    entrada: TextIO,
    saida: TextIO,
) -> ConfiguracaoAzureDevOps | _ConfiguracaoSimulada:
    """Carrega a configuração pelo componente central, incluindo injeção de simulação."""
    if (
        cliente is not None
        and getattr(argumentos, "simulacao", False)
        and not any(
            getattr(argumentos, nome, None)
            for nome in (
                "organizacao",
                "projeto",
                "area_path",
                "iteration_path",
                "caminho_configuracao",
            )
        )
    ):
        return _ConfiguracaoSimulada(cliente.configuracao)
    valores = {
        nome: getattr(argumentos, nome, None)
        for nome in ("organizacao", "projeto", "area_path", "iteration_path")
    }
    return carregar_configuracao(
        argumentos=valores,
        caminho_arquivo=getattr(argumentos, "caminho_configuracao", None),
        caminho_env=getattr(argumentos, "caminho_env", Path(".env")),
        entrada=entrada,
        saida=saida,
    )


class _ConfiguracaoSimulada:
    """Adaptador interno para uma simulação com cliente fornecido pelo chamador."""

    def __init__(self, publicacao: ConfiguracaoPublicacao) -> None:
        self.publicacao = publicacao


def _validar(caminho: Path, saida: TextIO) -> int:
    itens = interpretar_backlog(caminho)
    _escrever(saida, f"Backlog válido: {len(itens)} itens.\n")
    return 0


def _verificar_preliminar(
    cliente: ClientePublicacao, configuracao: ConfiguracaoPublicacao, plano: PlanoPublicacao
) -> None:
    cliente.verificar_destino(configuracao)
    for operacao in plano.operacoes:
        cliente.validar_operacao(operacao)


def _apresentar_plano(
    plano: PlanoPublicacao,
    configuracao: ConfiguracaoPublicacao,
    total: int,
    registrados: int,
    caminho_manifesto: Path | None,
    saida: TextIO,
) -> None:
    contagem = Counter(operacao.tipo.value for operacao in plano.operacoes)
    _escrever(saida, "Plano de publicação\n")
    _escrever(saida, f"Organização: {configuracao.organizacao}\n")
    _escrever(saida, f"Projeto: {configuracao.projeto}\n")
    _escrever(saida, f"Area Path: {configuracao.area_path}\n")
    _escrever(saida, f"Iteration Path: {configuracao.iteration_path}\n")
    _escrever(saida, f"Itens totais: {total}\n")
    _escrever(saida, f"Itens novos: {len(plano.operacoes)}\n")
    _escrever(saida, f"Itens registrados no manifesto: {registrados}\n")
    _escrever(saida, f"Por tipo: {dict(contagem)}\n")
    _escrever(saida, f"Ordem: {', '.join(op.chave for op in plano.operacoes) or 'nenhuma'}\n")
    relacoes = ", ".join(
        f"{operacao.chave} <- {operacao.chave_pai}"
        for operacao in plano.operacoes
        if operacao.chave_pai is not None
    )
    _escrever(saida, f"Relações pai-filho: {relacoes or 'nenhuma'}\n")
    _escrever(saida, f"Hash do plano: {plano.hash_plano}\n")
    if caminho_manifesto is not None:
        _escrever(saida, f"Manifesto: {caminho_manifesto}\n")


def _publicar(
    plano: PlanoPublicacao,
    configuracao: ConfiguracaoPublicacao,
    cliente: ClientePublicacao,
    caminho_manifesto: Path,
    entrada: TextIO,
    saida: TextIO,
) -> int:
    if not plano.operacoes:
        _escrever(saida, "Nenhum item novo para publicar.\n")
        return 0

    modalidade = escolher_modalidade(entrada, saida)
    if modalidade is ModalidadeAutorizacao.CANCELADA:
        _escrever(saida, "Publicação cancelada; nenhuma chamada de criação foi realizada.\n")
        return 0
    if modalidade is ModalidadeAutorizacao.INTEIRA:
        autorizacao = _solicitar_autorizacao(
            plano.hash_plano,
            len(plano.operacoes),
            configuracao,
            entrada,
            saida,
        )
        if autorizacao is None:
            return 2
        resultado = executar_plano(plano, autorizacao, cliente, caminho_manifesto)
        _escrever(saida, f"Publicação concluída: {len(resultado.itens)} itens.\n")
        return 0

    tamanho = _solicitar_tamanho_lote(entrada, saida)
    for lote in criar_lotes(len(plano.operacoes), tamanho):
        chaves = tuple(op.chave for op in plano.operacoes[lote.inicio : lote.fim])
        _escrever(saida, f"Lote {lote.numero}: {', '.join(chaves)}\n")
        autorizacao = _solicitar_autorizacao(
            plano.hash_plano,
            lote.quantidade,
            configuracao,
            entrada,
            saida,
            numero_lote=lote.numero,
            chaves=chaves,
            lote=lote,
        )
        if autorizacao is None:
            return 2
        executar_plano(plano, autorizacao, cliente, caminho_manifesto)
    _escrever(saida, "Publicação concluída por lotes.\n")
    return 0


def _solicitar_autorizacao(
    plano_hash: str,
    quantidade: int,
    configuracao: ConfiguracaoPublicacao,
    entrada: TextIO,
    saida: TextIO,
    *,
    numero_lote: int | None = None,
    chaves: Sequence[str] | None = None,
    lote: object | None = None,
):
    frase = criar_frase_confirmacao(plano_hash, quantidade, configuracao, numero_lote)
    _escrever(saida, f"Digite exatamente: {frase}\n")
    confirmacao = coletar_confirmacao(entrada, saida)
    autorizacao = criar_autorizacao(
        plano_hash=plano_hash,
        modalidade=(
            ModalidadeAutorizacao.LOTES
            if numero_lote is not None
            else ModalidadeAutorizacao.INTEIRA
        ),
        confirmacao=confirmacao,
        quantidade=quantidade,
        configuracao=configuracao,
        numero_lote=numero_lote,
        chaves_autorizadas=chaves,
        lote=lote,
    )
    if not autorizacao.valida_para(plano_hash):
        _escrever(saida, "Confirmação inválida; nenhuma chamada de criação foi realizada.\n")
        return None
    return autorizacao


def _solicitar_tamanho_lote(entrada: TextIO, saida: TextIO) -> int:
    while True:
        _escrever(saida, "Tamanho do lote: ")
        valor = entrada.readline()
        if not valor:
            raise ValueError("A entrada foi encerrada antes do tamanho do lote.")
        try:
            return int(valor.strip())
        except (AttributeError, ValueError):
            _escrever(saida, "Informe um tamanho de lote inteiro e positivo.\n")


def _escrever(saida: TextIO, texto: str) -> None:
    saida.write(texto)


if __name__ == "__main__":
    raise SystemExit(principal())

"""Executa um plano autorizado, com retomada segura pelo manifesto."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from publicar_backlog_azure_boards.autorizacao import Autorizacao
from publicar_backlog_azure_boards.cliente_azure_devops import ClienteAzureDevOps
from publicar_backlog_azure_boards.manifesto import Manifesto, gravar_manifesto, ler_manifesto
from publicar_backlog_azure_boards.modelos import PlanoPublicacao, RegistroManifesto


class FalhaPublicacao(RuntimeError):
    """Indica que a publicação parou no item informado, sem rollback."""

    def __init__(self, chave: str, erro: Exception) -> None:
        super().__init__(f"A publicação falhou no item {chave}: {erro}")
        self.chave = chave
        self.erro = erro


@dataclass(frozen=True)
class ResultadoPublicacao:
    """Resumo dos itens publicados nesta execução."""

    itens: tuple[str, ...]


def executar_plano(
    plano: PlanoPublicacao,
    autorizacao: Autorizacao,
    cliente: ClienteAzureDevOps,
    caminho_manifesto: Path,
) -> ResultadoPublicacao:
    """Publica sequencialmente apenas o conjunto exato autorizado do plano."""
    if not autorizacao.valida_para(plano.hash_plano):
        raise PermissionError("A autorização não é válida para o hash deste plano.")
    chaves_plano = tuple(operacao.chave for operacao in plano.operacoes)
    if not autorizacao.valida_conjunto(chaves_plano):
        raise PermissionError("A autorização não cobre exatamente o conjunto deste plano.")
    chaves_autorizadas = (
        autorizacao.chaves_autorizadas
        if autorizacao.chaves_autorizadas is not None
        else frozenset(chaves_plano)
    )

    manifesto = ler_manifesto(caminho_manifesto)
    _validar_manifesto(manifesto, plano, cliente)
    registros = dict(manifesto.itens)
    titulos = dict(manifesto.titulos)
    criados: list[str] = []
    for operacao in plano.operacoes:
        if operacao.chave not in chaves_autorizadas:
            continue
        existente = registros.get(operacao.chave)
        if existente is not None:
            continue
        if operacao.chave_pai is not None and operacao.chave_pai not in registros:
            raise ValueError(
                f"O pai {operacao.chave_pai} do item {operacao.chave} não foi publicado."
            )
        id_pai = registros[operacao.chave_pai].id if operacao.chave_pai is not None else None
        try:
            criado = cliente.criar_item(operacao, id_pai=id_pai)
        except Exception as erro:
            raise FalhaPublicacao(operacao.chave, erro) from erro
        registros[operacao.chave] = RegistroManifesto(criado.id, operacao.tipo, criado.url)
        titulos[operacao.chave] = operacao.titulo
        manifesto = Manifesto(
            hash_plano=plano.hash_plano,
            configuracao=cliente.configuracao,
            itens=registros,
            titulos=titulos,
            origem=manifesto.origem,
        )
        gravar_manifesto(caminho_manifesto, manifesto)
        criados.append(operacao.chave)
    return ResultadoPublicacao(tuple(criados))


def _validar_manifesto(
    manifesto: Manifesto, plano: PlanoPublicacao, cliente: ClienteAzureDevOps
) -> None:
    if not manifesto.itens and not manifesto.hash_plano:
        return
    if manifesto.hash_plano != plano.hash_plano:
        raise ValueError("O hash do manifesto não corresponde ao plano atual.")
    if manifesto.configuracao != cliente.configuracao:
        raise ValueError("O destino do manifesto não corresponde ao cliente atual.")
    operacoes = {operacao.chave: operacao for operacao in plano.operacoes}
    for chave, registro in manifesto.itens.items():
        operacao = operacoes.get(chave)
        if operacao is None:
            raise ValueError(f"O item {chave} do manifesto não pertence ao plano atual.")
        if registro.tipo is not operacao.tipo or manifesto.titulos.get(chave) != operacao.titulo:
            raise ValueError(f"O item {chave} do manifesto diverge do plano atual.")

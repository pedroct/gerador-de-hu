"""Executa um plano integralmente autorizado, com retomada e reconciliação seguras."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from publicar_backlog_azure_boards.autorizacao import Autorizacao
from publicar_backlog_azure_boards.cliente_azure_devops import ErroCriacaoAmbigua
from publicar_backlog_azure_boards.manifesto import (
    Manifesto,
    ReconciliacaoManualNecessaria,
    ReconciliacaoPendente,
    gravar_manifesto,
    ler_manifesto,
    validar_manifesto,
)
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    PlanoPublicacao,
    RegistroManifesto,
)


class IdentidadeCriada(Protocol):
    """Campos de identidade exigidos de uma resposta de criação."""

    id: int
    url: str


class ClientePublicador(Protocol):
    """Contrato mínimo usado pelo executor, sem acoplar os testes ao transporte HTTP."""

    configuracao: ConfiguracaoPublicacao

    def criar_item(
        self, operacao: OperacaoCriacao, id_pai: int | None = None
    ) -> IdentidadeCriada: ...


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
    cliente: ClientePublicador,
    caminho_manifesto: Path,
) -> ResultadoPublicacao:
    """Publica somente o conjunto confirmado e bloqueia toda divergência posterior."""
    if not autorizacao.valida_para(plano):
        raise PermissionError("A autorização não corresponde ao plano executável completo.")

    manifesto = ler_manifesto(caminho_manifesto)
    pendentes = validar_manifesto(manifesto, plano, cliente.configuracao)
    chaves_pendentes = tuple(operacao.chave for operacao in pendentes)
    if chaves_pendentes != autorizacao.chaves_pendentes:
        raise PermissionError("O conjunto pendente divergiu desde a autorização.")

    autorizadas = set(autorizacao.chaves_autorizadas)
    if not autorizadas or not autorizadas.issubset(chaves_pendentes):
        raise PermissionError("A autorização não cobre um conjunto pendente válido.")

    registros = dict(manifesto.itens)
    titulos = dict(manifesto.titulos)
    criados: list[str] = []
    for operacao in plano.operacoes:
        if operacao.chave not in autorizadas:
            continue
        if operacao.chave_pai is not None and operacao.chave_pai not in registros:
            raise ValueError(
                f"O pai {operacao.chave_pai} do item {operacao.chave} não foi publicado."
            )
        id_pai = registros[operacao.chave_pai].id if operacao.chave_pai is not None else None
        marcador = ReconciliacaoPendente(
            chave=operacao.chave,
            tipo_remoto=operacao.tipo_remoto,
            titulo=operacao.titulo,
        )
        manifesto_em_escrita = _manifesto_atualizado(
            manifesto,
            plano,
            cliente.configuracao,
            registros,
            titulos,
            reconciliacao=marcador,
        )
        gravar_manifesto(caminho_manifesto, manifesto_em_escrita)
        try:
            criado = cliente.criar_item(operacao, id_pai=id_pai)
        except ErroCriacaoAmbigua as erro:
            raise FalhaPublicacao(operacao.chave, erro) from erro
        except Exception as erro:
            _limpar_marcador_apos_falha_definitiva(
                caminho_manifesto,
                manifesto,
                plano,
                cliente.configuracao,
                registros,
                titulos,
                operacao.chave,
            )
            raise FalhaPublicacao(operacao.chave, erro) from erro

        novos_registros = dict(registros)
        novos_titulos = dict(titulos)
        novos_registros[operacao.chave] = RegistroManifesto(criado.id, operacao.tipo, criado.url)
        novos_titulos[operacao.chave] = operacao.titulo
        manifesto_confirmado = _manifesto_atualizado(
            manifesto,
            plano,
            cliente.configuracao,
            novos_registros,
            novos_titulos,
        )
        try:
            gravar_manifesto(caminho_manifesto, manifesto_confirmado)
        except Exception as erro:
            raise FalhaPublicacao(
                operacao.chave,
                ReconciliacaoManualNecessaria(
                    "O item respondeu como criado, mas o manifesto não pôde confirmar o registro."
                ),
            ) from erro
        registros = novos_registros
        titulos = novos_titulos
        manifesto = manifesto_confirmado
        criados.append(operacao.chave)
    return ResultadoPublicacao(tuple(criados))


def _manifesto_atualizado(
    anterior: Manifesto,
    plano: PlanoPublicacao,
    configuracao: ConfiguracaoPublicacao,
    registros: dict[str, RegistroManifesto],
    titulos: dict[str, str],
    *,
    reconciliacao: ReconciliacaoPendente | None = None,
) -> Manifesto:
    return Manifesto(
        hash_plano=plano.hash_plano,
        configuracao=configuracao,
        itens=registros,
        titulos=titulos,
        reconciliacao_pendente=reconciliacao,
        origem=anterior.origem,
    )


def _limpar_marcador_apos_falha_definitiva(
    caminho: Path,
    anterior: Manifesto,
    plano: PlanoPublicacao,
    configuracao: ConfiguracaoPublicacao,
    registros: dict[str, RegistroManifesto],
    titulos: dict[str, str],
    chave: str,
) -> None:
    try:
        gravar_manifesto(
            caminho,
            _manifesto_atualizado(anterior, plano, configuracao, registros, titulos),
        )
    except Exception as erro:
        raise ReconciliacaoManualNecessaria(
            f"O manifesto manteve o item {chave} em reconciliação manual."
        ) from erro

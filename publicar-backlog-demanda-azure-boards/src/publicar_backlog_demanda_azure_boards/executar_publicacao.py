"""Executa um plano integralmente autorizado, com retomada e reconciliação seguras."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from publicar_backlog_demanda_azure_boards.autorizacao import Autorizacao, ErroAutorizacao
from publicar_backlog_demanda_azure_boards.cliente_azure_devops import ErroCriacaoAmbigua
from publicar_backlog_demanda_azure_boards.interpretar_markdown import ErroContratoMarkdown
from publicar_backlog_demanda_azure_boards.manifesto import (
    Manifesto,
    ReconciliacaoManualNecessaria,
    ReconciliacaoPendente,
    gravar_manifesto,
    ler_manifesto,
    validar_manifesto,
)
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    PlanoPublicacao,
    RegistroManifesto,
)

_DEMANDA_ORIGEM_RE = re.compile(r"^- Demanda de Negócio de origem: (?P<valor>.+)$", re.MULTILINE)
_DEMANDA_ID_RE = re.compile(r"^`#(\d+)`$")


def extrair_demanda_origem(caminho: Path) -> int | None:
    """Lê o ID da Demanda declarado nos Metadados; ``None`` quando o backlog não nasceu de uma.

    Vive aqui, e não em ``interpretar_markdown.py``, porque este módulo é espelhado byte a
    byte no pacote ``publicar-backlog-azure-boards`` (ver ``test_sincronia_com_origem.py``),
    e a checagem cruzada do `demanda_id` é exclusiva da publicadora de Demanda: a
    publicadora solta precisa continuar aceitando um backlog com Demanda declarada (o
    backlog de débitos técnicos declara a origem só para rastreabilidade e publica solto de
    propósito, pelo `Iteration Path`).
    """
    texto = caminho.read_text(encoding="utf-8")
    correspondencia = _DEMANDA_ORIGEM_RE.search(texto)
    if correspondencia is None:
        raise ErroContratoMarkdown("Metadados e cobertura não possui Demanda de Negócio de origem")
    valor = correspondencia.group("valor").strip()
    if valor.startswith("Não se aplica"):
        return None
    id_declarado = _DEMANDA_ID_RE.match(valor)
    if id_declarado is None:
        raise ErroContratoMarkdown(
            f"Demanda de Negócio de origem inválida: {valor!r}; use `#<id>` ou 'Não se aplica'"
        )
    return int(id_declarado.group(1))


def conferir_demanda_de_origem(caminho: Path, demanda_id: int) -> None:
    """Recusa publicar sob uma Demanda diferente da que o backlog declara.

    Sem flag de sobreposição de propósito: pendurar épicos na Demanda errada é caro de
    desfazer, e uma flag para forçar existiria para ser usada justamente sob a pressão em
    que o engano acontece. Republicar sob outra Demanda passa por corrigir o documento.
    """
    declarada = extrair_demanda_origem(caminho)
    if declarada is None:
        raise ValueError(
            "O backlog declara 'Não se aplica' em Demanda de Negócio de origem: ele não "
            "nasceu de uma Demanda, e esta não é a publicadora dele."
        )
    if declarada != demanda_id:
        raise ValueError(
            f"O backlog declara a Demanda #{declarada}, e a configuração informa "
            f"#{demanda_id}. Corrija o documento ou a configuração antes de publicar."
        )


class IdentidadeCriada(Protocol):
    """Campos de identidade exigidos de uma resposta de criação."""

    id: int
    url: str


class ClientePublicador(Protocol):
    """Contrato mínimo usado pelo executor, sem acoplar os testes ao transporte HTTP."""

    configuracao: ConfiguracaoPublicacao

    def criar_item(
        self,
        operacao: OperacaoCriacao,
        id_pai: int | None = None,
        ids_predecessores: tuple[int, ...] = (),
    ) -> IdentidadeCriada: ...

    def url_do_item(self, id_item: int) -> str: ...


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
    if cliente.configuracao != plano.configuracao:
        raise ErroAutorizacao("O destino do cliente não corresponde ao plano executável completo.")
    if not autorizacao.valida_para(plano, cliente.configuracao):
        raise ErroAutorizacao("A autorização não corresponde ao plano executável completo.")

    manifesto = ler_manifesto(caminho_manifesto)
    pendentes = validar_manifesto(manifesto, plano, cliente.configuracao)
    chaves_pendentes = tuple(operacao.chave for operacao in pendentes)
    autorizadas = set(autorizacao.chaves_autorizadas)
    if not autorizadas or not autorizadas.issubset(chaves_pendentes):
        raise ErroAutorizacao("A autorização não cobre um conjunto pendente válido.")

    registros = dict(manifesto.itens)
    titulos = dict(manifesto.titulos)
    for preexistente in plano.preexistentes:
        registros[preexistente.chave] = RegistroManifesto(
            preexistente.id,
            preexistente.tipo,
            cliente.url_do_item(preexistente.id),
            preexistente=True,
        )
        # ItemPreexistente não carrega título: o backlog só declarou o ID publicado.
        # O manifesto exige um título não vazio para round-trip, e este é só um rótulo
        # informativo, nunca comparado ao backlog (a chave não está em plano.operacoes).
        titulos.setdefault(
            preexistente.chave, f"(item pré-existente, Azure Boards #{preexistente.id})"
        )
    criados: list[str] = []
    for operacao in plano.operacoes:
        if operacao.chave not in autorizadas:
            continue
        for chave_predecessor in operacao.depende_de:
            if chave_predecessor not in registros:
                raise ValueError(
                    f"O predecessor {chave_predecessor} do item {operacao.chave} não foi publicado."
                )
        if operacao.chave_pai is not None and operacao.chave_pai not in registros:
            raise ValueError(
                f"O pai {operacao.chave_pai} do item {operacao.chave} não foi publicado."
            )
        # Item sem pai documental é um Épico, e o pai dele é a Demanda de Negócio.
        # Depois desta skill, nenhum item publicado sobe sem pai.
        id_pai = (
            registros[operacao.chave_pai].id
            if operacao.chave_pai is not None
            else cliente.configuracao.demanda_id
        )
        ids_predecessores = tuple(registros[chave].id for chave in operacao.depende_de)
        marcador = ReconciliacaoPendente(
            chave=operacao.chave,
            tipo_remoto=operacao.tipo_remoto,
            titulo=operacao.titulo,
            tipo=operacao.tipo,
            destino=cliente.configuracao,
            hash_plano=plano.hash_plano,
            timestamp=datetime.now(UTC).isoformat(),
            motivo="resultado da criação ainda não confirmado",
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
            criado = cliente.criar_item(
                operacao, id_pai=id_pai, ids_predecessores=ids_predecessores
            )
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
            chave_reconciliacao=operacao.chave,
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
    chave_reconciliacao: str | None = None,
) -> Manifesto:
    reconciliacoes = dict(anterior.reconciliacoes)
    if reconciliacao is not None:
        reconciliacoes[reconciliacao.chave] = reconciliacao
    elif chave_reconciliacao is not None:
        reconciliacoes.pop(chave_reconciliacao, None)
    return Manifesto(
        hash_plano=plano.hash_plano,
        configuracao=configuracao,
        itens=registros,
        titulos=titulos,
        origem=anterior.origem,
        reconciliacoes=reconciliacoes,
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
            _manifesto_atualizado(
                anterior,
                plano,
                configuracao,
                registros,
                titulos,
                chave_reconciliacao=chave,
            ),
        )
    except Exception as erro:
        raise ReconciliacaoManualNecessaria(
            f"O manifesto manteve o item {chave} em reconciliação manual."
        ) from erro

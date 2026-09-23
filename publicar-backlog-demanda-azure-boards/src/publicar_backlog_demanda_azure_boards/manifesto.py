"""Leitura, validação e gravação segura do manifesto de publicação."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    EstadoReconciliacao,
    MapeamentoTipos,
    OperacaoCriacao,
    PlanoPublicacao,
    ReconciliacaoPendente,
    RegistroManifesto,
    TipoItem,
)

__all__ = [
    "ErroReconciliacaoPendente",
    "Manifesto",
    "ReconciliacaoManualNecessaria",
    "ReconciliacaoPendente",
    "gravar_manifesto",
    "ler_manifesto",
    "validar_manifesto",
]


class ReconciliacaoManualNecessaria(RuntimeError):
    """Bloqueia novas escritas enquanto uma criação anterior permanecer ambígua."""


class ErroReconciliacaoPendente(ReconciliacaoManualNecessaria):
    """Indica que uma reconciliação pendente impede qualquer nova criação."""


@dataclass(frozen=True)
class Manifesto:
    """Registra a identidade do plano, os itens criados e o estado de reconciliação."""

    hash_plano: str = ""
    configuracao: ConfiguracaoPublicacao | None = None
    itens: dict[str, RegistroManifesto] = field(default_factory=dict)
    titulos: dict[str, str] = field(default_factory=dict)
    reconciliacao_pendente: ReconciliacaoPendente | None = None
    origem: str = "backlog.md"
    versao: int = 1
    reconciliacoes: dict[str, ReconciliacaoPendente] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normaliza o mapa novo e o campo singular legado no mesmo estado lógico."""
        reconciliacoes = dict(self.reconciliacoes)
        sem_destino = tuple(
            reconciliacao.chave
            for reconciliacao in reconciliacoes.values()
            if reconciliacao.destino is None
        )
        if sem_destino:
            raise ValueError(
                "Reconciliações novas exigem contexto de destino completo: "
                + ", ".join(sem_destino)
                + "."
            )
        if self.reconciliacao_pendente is not None:
            chave = self.reconciliacao_pendente.chave
            existente = reconciliacoes.get(chave)
            if existente is not None and existente != self.reconciliacao_pendente:
                raise ValueError(f"Há duas reconciliações diferentes para o item {chave}.")
            reconciliacoes.setdefault(chave, self.reconciliacao_pendente)
        pendente = next(
            (
                reconciliacao
                for reconciliacao in reconciliacoes.values()
                if reconciliacao.resolucao == EstadoReconciliacao.PENDENTE.value
            ),
            None,
        )
        if reconciliacoes != self.reconciliacoes:
            object.__setattr__(self, "reconciliacoes", reconciliacoes)
        if self.reconciliacao_pendente is None and pendente is not None:
            object.__setattr__(self, "reconciliacao_pendente", pendente)


def ler_manifesto(caminho: Path) -> Manifesto:
    """Lê um manifesto existente ou retorna um manifesto vazio."""
    if not caminho.is_file():
        return Manifesto()
    try:
        return _converter(json.loads(caminho.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as erro:
        raise ValueError(f"O manifesto {caminho} é inválido.") from erro


def gravar_manifesto(caminho: Path, manifesto: Manifesto) -> None:
    """Grava em arquivo temporário no mesmo diretório e o substitui atomicamente."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=caminho.parent,
            prefix=f".{caminho.name}.",
            delete=False,
        ) as arquivo:
            temporario = arquivo.name
            json.dump(_serializar(manifesto), arquivo, ensure_ascii=False, indent=2, sort_keys=True)
            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
        temporario = None
        _sincronizar_diretorio(caminho.parent)
    finally:
        if temporario is not None:
            try:
                os.unlink(temporario)
            except FileNotFoundError:
                pass


def validar_manifesto(
    manifesto: Manifesto,
    plano: PlanoPublicacao,
    configuracao: ConfiguracaoPublicacao,
) -> tuple[OperacaoCriacao, ...]:
    """Valida registros contra o backlog completo e só então devolve os pendentes."""
    pendencias = tuple(
        reconciliacao
        for reconciliacao in manifesto.reconciliacoes.values()
        if reconciliacao.resolucao == EstadoReconciliacao.PENDENTE.value
    )
    if pendencias:
        chaves = ", ".join(reconciliacao.chave for reconciliacao in pendencias)
        raise ErroReconciliacaoPendente(
            f"Os itens {chaves} exigem reconciliação manual no Azure Boards "
            "antes de qualquer nova escrita."
        )
    for reconciliacao in manifesto.reconciliacoes.values():
        chave_criada = reconciliacao.chave in manifesto.itens
        if (
            reconciliacao.resolucao == EstadoReconciliacao.RESOLVIDA_CRIADA.value
            and not chave_criada
        ):
            raise ValueError(
                f"O item {reconciliacao.chave} está marcado como "
                f"{EstadoReconciliacao.RESOLVIDA_CRIADA.value}, mas não existe em "
                "manifesto.itens; corrija o manifesto antes de qualquer nova escrita."
            )
        if (
            reconciliacao.resolucao == EstadoReconciliacao.RESOLVIDA_NAO_CRIADA.value
            and chave_criada
        ):
            raise ValueError(
                f"O item {reconciliacao.chave} está marcado como "
                f"{EstadoReconciliacao.RESOLVIDA_NAO_CRIADA.value}, mas já existe em "
                "manifesto.itens; corrija o manifesto antes de qualquer nova escrita."
            )
    if not manifesto.itens and not manifesto.hash_plano and manifesto.configuracao is None:
        return plano.operacoes
    if manifesto.hash_plano != plano.hash_plano:
        raise ValueError("O hash do manifesto não corresponde ao plano atual.")
    if manifesto.configuracao != configuracao or plano.configuracao != configuracao:
        raise ValueError("O destino do manifesto não corresponde ao plano atual.")

    operacoes = {operacao.chave: operacao for operacao in plano.operacoes}
    for chave, registro in manifesto.itens.items():
        operacao = operacoes.get(chave)
        if operacao is None:
            raise ValueError(f"O item {chave} do manifesto não pertence ao backlog completo.")
        if registro.tipo is not operacao.tipo or manifesto.titulos.get(chave) != operacao.titulo:
            raise ValueError(f"O item {chave} do manifesto diverge do backlog completo.")
    return tuple(operacao for operacao in plano.operacoes if operacao.chave not in manifesto.itens)


def _serializar(manifesto: Manifesto) -> dict[str, Any]:
    configuracao = manifesto.configuracao
    destino = None if configuracao is None else _serializar_configuracao(configuracao)
    reconciliacao = manifesto.reconciliacao_pendente
    return {
        "versao": manifesto.versao,
        "origem": manifesto.origem,
        "hash_plano": manifesto.hash_plano,
        "destino": destino,
        "reconciliacao_pendente": (
            None if reconciliacao is None else _serializar_reconciliacao(reconciliacao)
        ),
        "reconciliacoes": {
            chave: _serializar_reconciliacao(reconciliacao)
            for chave, reconciliacao in manifesto.reconciliacoes.items()
            if reconciliacao.destino is not None
        },
        "itens": {
            chave: {
                "id": registro.id,
                "tipo": registro.tipo.value,
                "titulo": manifesto.titulos.get(chave),
                "url": registro.url,
            }
            for chave, registro in manifesto.itens.items()
        },
    }


def _serializar_configuracao(configuracao: ConfiguracaoPublicacao) -> dict[str, object]:
    return {
        "organizacao": configuracao.organizacao,
        "projeto": configuracao.projeto,
        "area_path": configuracao.area_path,
        "iteration_path": configuracao.iteration_path,
        "demanda_id": configuracao.demanda_id,
        "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
    }


def _converter(dados: object) -> Manifesto:
    if not isinstance(dados, dict):
        raise ValueError("A raiz do manifesto deve ser um objeto JSON.")
    if dados.get("versao") != 1 or not isinstance(dados.get("origem"), str):
        raise ValueError("A versão ou a origem do manifesto é inválida.")
    hash_plano = dados.get("hash_plano")
    destino = dados.get("destino")
    itens = dados.get("itens")
    if (
        not isinstance(hash_plano, str)
        or not isinstance(destino, (dict, type(None)))
        or not isinstance(itens, dict)
    ):
        raise ValueError("O manifesto não contém seus campos obrigatórios.")
    if destino is None:
        if (
            hash_plano
            or itens
            or dados.get("reconciliacao_pendente") is not None
            or dados.get("reconciliacoes")
        ):
            raise ValueError("Um manifesto com dados exige um destino completo.")
        configuracao = None
    else:
        configuracao = _configuracao(destino)

    reconciliacao_legada = _converter_reconciliacao(
        dados.get("reconciliacao_pendente"), exigir_destino=False
    )
    reconciliacoes = _converter_reconciliacoes(dados.get("reconciliacoes"))
    if reconciliacao_legada is not None:
        existente = reconciliacoes.get(reconciliacao_legada.chave)
        if existente is not None and existente != reconciliacao_legada:
            raise ValueError("O manifesto contém reconciliações divergentes para a mesma chave.")

    registros: dict[str, RegistroManifesto] = {}
    titulos: dict[str, str] = {}
    for chave, dados_item in itens.items():
        if not isinstance(chave, str) or not isinstance(dados_item, dict):
            raise ValueError("Um item do manifesto é inválido.")
        item_id = dados_item.get("id")
        tipo = dados_item.get("tipo")
        titulo = dados_item.get("titulo")
        url = dados_item.get("url")
        if (
            isinstance(item_id, bool)
            or not isinstance(item_id, int)
            or item_id <= 0
            or not isinstance(tipo, str)
            or not isinstance(titulo, str)
            or not titulo
            or not isinstance(url, str)
            or not url
        ):
            raise ValueError("Um item do manifesto não contém identidade completa.")
        try:
            tipo_item = TipoItem(tipo)
        except ValueError as erro:
            raise ValueError("Um item do manifesto tem tipo inválido.") from erro
        registros[chave] = RegistroManifesto(item_id, tipo_item, url)
        titulos[chave] = titulo
    return Manifesto(
        hash_plano=hash_plano,
        configuracao=configuracao,
        itens=registros,
        titulos=titulos,
        origem=dados["origem"],
        reconciliacao_pendente=reconciliacao_legada,
        reconciliacoes=reconciliacoes,
    )


def _serializar_reconciliacao(reconciliacao: ReconciliacaoPendente) -> dict[str, object]:
    return {
        "chave": reconciliacao.chave,
        "tipo_remoto": reconciliacao.tipo_remoto,
        "tipo": None if reconciliacao.tipo is None else reconciliacao.tipo.value,
        "titulo": reconciliacao.titulo,
        "destino": (
            None
            if reconciliacao.destino is None
            else _serializar_configuracao(reconciliacao.destino)
        ),
        "hash_plano": reconciliacao.hash_plano,
        "timestamp": reconciliacao.timestamp,
        "motivo": reconciliacao.motivo,
        "resolucao": reconciliacao.resolucao,
    }


def _converter_reconciliacoes(
    dados: object,
) -> dict[str, ReconciliacaoPendente]:
    if dados is None:
        return {}
    if not isinstance(dados, dict):
        raise ValueError("O mapa de reconciliações do manifesto é inválido.")
    reconciliacoes: dict[str, ReconciliacaoPendente] = {}
    for chave, dados_reconciliacao in dados.items():
        if not isinstance(chave, str) or not chave:
            raise ValueError("Uma chave de reconciliação do manifesto é inválida.")
        reconciliacao = _converter_reconciliacao(dados_reconciliacao, exigir_destino=True)
        if reconciliacao is None or reconciliacao.chave != chave:
            raise ValueError("Uma reconciliação do manifesto não corresponde à sua chave.")
        reconciliacoes[chave] = reconciliacao
    return reconciliacoes


def _converter_reconciliacao(
    dados: object, *, exigir_destino: bool
) -> ReconciliacaoPendente | None:
    if dados is None:
        return None
    if not isinstance(dados, dict):
        raise ValueError("O estado de reconciliação do manifesto é inválido.")
    chave = dados.get("chave")
    tipo_remoto = dados.get("tipo_remoto")
    titulo = dados.get("titulo")
    if not isinstance(chave, str) or not chave:
        raise ValueError("O estado de reconciliação do manifesto é incompleto.")
    if not isinstance(tipo_remoto, str) or not tipo_remoto:
        raise ValueError("O estado de reconciliação do manifesto é incompleto.")
    if not isinstance(titulo, str) or not titulo:
        raise ValueError("O estado de reconciliação do manifesto é incompleto.")
    tipo = dados.get("tipo")
    if tipo is not None:
        if not isinstance(tipo, str):
            raise ValueError("O tipo da reconciliação do manifesto é inválido.")
        try:
            tipo_item: TipoItem | None = TipoItem(tipo)
        except ValueError as erro:
            raise ValueError("O tipo da reconciliação do manifesto é inválido.") from erro
    else:
        tipo_item = None

    destino_dados = dados.get("destino")
    if destino_dados is None:
        if exigir_destino:
            raise ValueError("Uma reconciliação nova exige destino completo.")
        destino = None
    elif isinstance(destino_dados, dict):
        destino = _configuracao(destino_dados)
    else:
        raise ValueError("O destino da reconciliação do manifesto é inválido.")
    hash_plano = dados.get("hash_plano", "")
    timestamp = dados.get("timestamp", "")
    motivo = dados.get("motivo", "")
    resolucao = dados.get("resolucao", "pendente")
    if not all(isinstance(valor, str) for valor in (hash_plano, timestamp, motivo, resolucao)):
        raise ValueError("Os metadados da reconciliação do manifesto são inválidos.")
    return ReconciliacaoPendente(
        chave=chave,
        tipo_remoto=tipo_remoto,
        titulo=titulo,
        tipo=tipo_item,
        destino=destino,
        hash_plano=hash_plano,
        timestamp=timestamp,
        motivo=motivo,
        resolucao=resolucao,
    )


def _configuracao(destino: dict[str, object]) -> ConfiguracaoPublicacao:
    campos = ("organizacao", "projeto", "area_path", "iteration_path")
    valores = [destino.get(campo) for campo in campos]
    if not all(isinstance(valor, str) and valor for valor in valores):
        raise ValueError("O destino do manifesto é inválido.")
    demanda_id = destino.get("demanda_id")
    if not isinstance(demanda_id, int) or isinstance(demanda_id, bool) or demanda_id <= 0:
        raise ValueError("O destino do manifesto não identifica a Demanda de Negócio.")
    mapeamento_dados = destino.get("mapeamento_tipos", {})
    if not isinstance(mapeamento_dados, dict):
        raise ValueError("O mapeamento de tipos do manifesto é inválido.")
    mapeamento = MapeamentoTipos(
        epic=_tipo_remoto(mapeamento_dados, "Epic", "Epic"),
        feature=_tipo_remoto(mapeamento_dados, "Feature", "Feature"),
        historia_usuario=_tipo_remoto(mapeamento_dados, "User Story", "User Story"),
        bug=_tipo_remoto(mapeamento_dados, "Bug", "Bug"),
    )
    organizacao, projeto, area_path, iteration_path = (cast(str, valor) for valor in valores)
    return ConfiguracaoPublicacao(
        organizacao=organizacao,
        projeto=projeto,
        area_path=area_path,
        iteration_path=iteration_path,
        demanda_id=demanda_id,
        mapeamento_tipos=mapeamento,
    )


def _tipo_remoto(dados: dict[str, object], chave: str, padrao: str) -> str:
    valor = dados.get(chave, padrao)
    if not isinstance(valor, str) or not valor:
        raise ValueError("O mapeamento de tipos do manifesto é inválido.")
    return valor


def _sincronizar_diretorio(diretorio: Path) -> None:
    descritor = os.open(diretorio, os.O_RDONLY)
    try:
        os.fsync(descritor)
    finally:
        os.close(descritor)

"""Define a autorização explícita vinculada ao plano executável completo."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Collection
from dataclasses import dataclass, field
from enum import StrEnum
from hmac import compare_digest
from typing import TextIO

from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    PlanoPublicacao,
)


class ModalidadeAutorizacao(StrEnum):
    """Modalidades oferecidas antes de qualquer chamada de criação."""

    INTEIRA = "inteira"
    LOTES = "lotes"
    CANCELADA = "cancelada"


class ErroAutorizacao(PermissionError):
    """Indica que a confirmação não autoriza a escrita solicitada."""


class _SentinelaFabrica:
    """Marcador de identidade único, criado apenas neste módulo.

    Nenhum código fora de ``autorizacao.py`` consegue produzir outra instância desta
    classe; portanto, possuir o objeto exato ``_SENTINELA_FABRICA`` só é possível para
    quem passou por ``criar_autorizacao``.
    """

    __slots__ = ()


_SENTINELA_FABRICA = _SentinelaFabrica()


@dataclass(frozen=True)
class Lote:
    """Representa uma faixa de operações a ser confirmada separadamente."""

    numero: int
    inicio: int
    fim: int

    @property
    def quantidade(self) -> int:
        """Retorna a quantidade de operações pertencentes ao lote."""
        return self.fim - self.inicio


@dataclass(frozen=True)
class Autorizacao:
    """Associa consentimento ao conteúdo, destino, quantidade e conjunto exibidos."""

    hash_plano: str
    quantidade: int
    modalidade: ModalidadeAutorizacao
    chaves_autorizadas: frozenset[str]
    impressao_destino: str
    impressao_conteudo: str
    confirmacao: str
    numero_lote: int | None = None
    _sentinela_fabrica: _SentinelaFabrica | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Recusa qualquer instância que não tenha passado por ``criar_autorizacao``."""
        if self._sentinela_fabrica is not _SENTINELA_FABRICA:
            raise ErroAutorizacao(
                "Autorizacao só pode ser criada pela fábrica criar_autorizacao; "
                "construção direta da dataclass não é permitida."
            )

    def valida_para(self, plano: PlanoPublicacao, destino: ConfiguracaoPublicacao) -> bool:
        """Recalcula a impressão integral e bloqueia qualquer divergência executável."""
        if not isinstance(self.chaves_autorizadas, frozenset):
            return False
        if self.hash_plano != plano.hash_plano or self.quantidade != len(self.chaves_autorizadas):
            return False
        if self.impressao_destino != imprimir_destino(destino):
            return False
        if self.impressao_conteudo != imprimir_operacoes(plano, self.chaves_autorizadas):
            return False
        if not self.chaves_autorizadas <= {operacao.chave for operacao in plano.operacoes}:
            return False
        if self.modalidade is ModalidadeAutorizacao.INTEIRA:
            if self.numero_lote is not None:
                return False
        elif self.modalidade is ModalidadeAutorizacao.LOTES:
            if self.numero_lote is None or self.numero_lote < 1:
                return False
        else:
            return False
        esperada = criar_frase_confirmacao(plano, self.chaves_autorizadas, self.numero_lote)
        return validar_confirmacao(self.confirmacao, esperada)


def imprimir_destino(configuracao: ConfiguracaoPublicacao) -> str:
    """Resume criptograficamente todos os campos que identificam o destino remoto."""
    conteudo = {
        "organizacao": configuracao.organizacao,
        "projeto": configuracao.projeto,
        "area_path": configuracao.area_path,
        "iteration_path": configuracao.iteration_path,
        "demanda_id": configuracao.demanda_id,
        "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
    }
    return _resumir(conteudo)


def imprimir_operacoes(plano: PlanoPublicacao, chaves: Collection[str]) -> str:
    """Resume criptograficamente as operações autorizadas na ordem do plano."""
    autorizadas = frozenset(chaves)
    operacoes = [
        _operacao_para_impressao(operacao)
        for operacao in plano.operacoes
        if operacao.chave in autorizadas
    ]
    return _resumir(operacoes)


def _operacao_para_impressao(operacao: OperacaoCriacao) -> dict[str, str | None]:
    return {
        "chave": operacao.chave,
        "tipo": operacao.tipo.value,
        "titulo": operacao.titulo,
        "descricao": operacao.descricao,
        "criterios_aceitacao": operacao.criterios_aceitacao,
        "chave_pai": operacao.chave_pai,
        "tipo_remoto": operacao.tipo_remoto,
    }


def _resumir(conteudo: object) -> str:
    serializado = json.dumps(conteudo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serializado.encode()).hexdigest()


def validar_confirmacao(confirmacao: str, esperada: str) -> bool:
    """Aceita somente a frase integral apresentada para a pessoa executora."""
    return compare_digest(confirmacao.encode(), esperada.encode())


def coletar_confirmacao(entrada: TextIO, saida: TextIO) -> str | None:
    """Coleta a frase e remove somente a quebra de linha inserida pelo terminal."""
    saida.write("Digite a frase de confirmação: ")
    confirmacao = entrada.readline()
    if not confirmacao:
        return None
    return confirmacao.rstrip("\r\n")


def escolher_modalidade(entrada: TextIO, saida: TextIO) -> ModalidadeAutorizacao:
    """Obtém a modalidade inteira, por lotes ou o cancelamento explícito."""
    saida.write(
        "Como deseja autorizar a publicação?\n\n[1] Backlog inteiro\n[2] Por lotes\n[C] Cancelar\n"
    )
    while True:
        escolha = entrada.readline()
        if not escolha:
            return ModalidadeAutorizacao.CANCELADA
        modalidade = {
            "1": ModalidadeAutorizacao.INTEIRA,
            "2": ModalidadeAutorizacao.LOTES,
            "C": ModalidadeAutorizacao.CANCELADA,
            "CANCELAR": ModalidadeAutorizacao.CANCELADA,
        }.get(escolha.strip().upper())
        if modalidade is not None:
            return modalidade
        saida.write("Opção inválida. Escolha 1, 2 ou C.\n")


def criar_lotes(total: int, tamanho: int) -> tuple[Lote, ...]:
    """Divide o total de operações em lotes positivos e consecutivos."""
    if total < 0:
        raise ValueError("O total de itens não pode ser negativo.")
    if tamanho <= 0:
        raise ValueError("O tamanho do lote deve ser positivo.")
    return tuple(
        Lote(numero=numero, inicio=inicio, fim=min(inicio + tamanho, total))
        for numero, inicio in enumerate(range(0, total, tamanho), start=1)
    )


def criar_frase_confirmacao(
    plano: PlanoPublicacao,
    chaves_autorizadas: Collection[str],
    numero_lote: int | None = None,
) -> str:
    """Gera a frase que vincula quantidade, Demanda, destino e código do plano completo."""
    configuracao = plano.configuracao
    inicio = "AUTORIZAR PUBLICAÇÃO" if numero_lote is None else f"AUTORIZAR LOTE {numero_lote}"
    return (
        f"{inicio} {len(chaves_autorizadas)} ITENS "
        f"DEMANDA {configuracao.demanda_id} {configuracao.projeto} "
        f"{configuracao.area_path} {configuracao.iteration_path} "
        f"{plano.hash_plano[:4].upper()}"
    )


def criar_autorizacao(
    plano: PlanoPublicacao,
    confirmacao: str | None,
    chaves: frozenset[str],
    *,
    modalidade: ModalidadeAutorizacao = ModalidadeAutorizacao.INTEIRA,
    numero_lote: int | None = None,
) -> Autorizacao:
    """Cria autorização somente após validar a frase exibida para o conjunto selecionado."""
    if modalidade is ModalidadeAutorizacao.CANCELADA:
        raise ValueError("Uma publicação cancelada não pode gerar autorização.")
    if not isinstance(chaves, frozenset):
        raise ValueError("As chaves autorizadas devem formar um conjunto imutável.")
    if not chaves or not chaves <= {operacao.chave for operacao in plano.operacoes}:
        raise ValueError("As chaves autorizadas divergem do plano completo.")
    if modalidade is ModalidadeAutorizacao.INTEIRA and numero_lote is not None:
        raise ValueError("A publicação inteira não aceita número de lote.")
    if modalidade is ModalidadeAutorizacao.LOTES and (numero_lote is None or numero_lote < 1):
        raise ValueError("A modalidade por lotes exige um número de lote positivo.")

    esperada = criar_frase_confirmacao(plano, chaves, numero_lote)
    if confirmacao is None or not validar_confirmacao(confirmacao, esperada):
        raise ErroAutorizacao("A frase de confirmação não corresponde à autorização exibida.")
    return Autorizacao(
        hash_plano=plano.hash_plano,
        quantidade=len(chaves),
        modalidade=modalidade,
        chaves_autorizadas=chaves,
        impressao_destino=imprimir_destino(plano.configuracao),
        impressao_conteudo=imprimir_operacoes(plano, chaves),
        confirmacao=confirmacao,
        numero_lote=numero_lote,
        _sentinela_fabrica=_SENTINELA_FABRICA,
    )

"""Define a autorização explícita e vinculada a um plano de publicação."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from hmac import compare_digest
from typing import TextIO

from publicar_backlog_azure_boards.modelos import ConfiguracaoPublicacao


class ModalidadeAutorizacao(StrEnum):
    """Modalidades oferecidas antes de qualquer chamada de criação."""

    INTEIRA = "inteira"
    LOTES = "lotes"
    CANCELADA = "cancelada"


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
    """Associa uma decisão explícita ao hash e ao conjunto do plano apresentado."""

    plano_hash: str
    modalidade: ModalidadeAutorizacao
    chaves_autorizadas: frozenset[str] | None = None
    numero_lote: int | None = None
    faixa: tuple[int, int] | None = None
    _confirmada: bool = field(default=False, init=False, repr=False)

    def valida_para(self, plano_hash: str, chaves_plano: Iterable[str] | None = None) -> bool:
        """Valida hash e, quando informado, o conjunto de operações do plano."""
        if not self._confirmada or not compare_digest(self.plano_hash, plano_hash):
            return False
        if self.modalidade is ModalidadeAutorizacao.LOTES and self.chaves_autorizadas is None:
            return False
        return chaves_plano is None or self.valida_conjunto(chaves_plano)

    def valida_conjunto(self, chaves_plano: Iterable[str]) -> bool:
        """Confirma que a autorização cobre exatamente as operações permitidas."""
        chaves = tuple(chaves_plano)
        conjunto_plano = frozenset(chaves)
        autorizadas = self.chaves_autorizadas
        if not self._confirmada:
            return False
        if autorizadas is None:
            return self.modalidade is ModalidadeAutorizacao.INTEIRA
        if not autorizadas.issubset(conjunto_plano):
            return False
        if self.modalidade is ModalidadeAutorizacao.INTEIRA and autorizadas != conjunto_plano:
            return False
        if self.faixa is not None:
            inicio, fim = self.faixa
            if inicio < 0 or inicio >= fim or fim > len(chaves):
                return False
            if autorizadas != frozenset(chaves[inicio:fim]):
                return False
        return True


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
        "Como deseja autorizar a publicação?\n\n"
        "[1] Backlog inteiro\n"
        "[2] Por lotes\n"
        "[C] Cancelar\n"
    )
    while True:
        escolha = entrada.readline()
        if not escolha:
            return ModalidadeAutorizacao.CANCELADA
        correspondencias = {
            "1": ModalidadeAutorizacao.INTEIRA,
            "2": ModalidadeAutorizacao.LOTES,
            "C": ModalidadeAutorizacao.CANCELADA,
            "CANCELAR": ModalidadeAutorizacao.CANCELADA,
        }
        modalidade = correspondencias.get(escolha.strip().upper())
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
    plano_hash: str,
    quantidade: int,
    configuracao: ConfiguracaoPublicacao,
    numero_lote: int | None = None,
) -> str:
    """Gera a frase integral que vincula quantidade, destino e código do plano."""
    codigo_plano = plano_hash[:4].upper()
    if numero_lote is None:
        inicio = "AUTORIZAR PUBLICAÇÃO"
    else:
        inicio = f"AUTORIZAR LOTE {numero_lote}"
    return (
        f"{inicio} {quantidade} ITENS {configuracao.projeto} {configuracao.area_path} "
        f"{configuracao.iteration_path} {codigo_plano}"
    )


def criar_autorizacao(
    plano_hash: str,
    modalidade: ModalidadeAutorizacao = ModalidadeAutorizacao.INTEIRA,
    confirmacao: str | None = None,
    quantidade: int | None = None,
    configuracao: ConfiguracaoPublicacao | None = None,
    numero_lote: int | None = None,
    chaves_autorizadas: Iterable[str] | None = None,
    lote: Lote | None = None,
) -> Autorizacao:
    """Cria uma autorização operacional apenas após validar a frase derivada do plano."""
    if not plano_hash:
        raise ValueError("O hash do plano é obrigatório para autorizar a publicação.")
    if modalidade is ModalidadeAutorizacao.CANCELADA:
        raise ValueError("Uma publicação cancelada não pode gerar autorização.")
    if lote is not None:
        if modalidade is not ModalidadeAutorizacao.LOTES:
            raise ValueError("Uma faixa só pode ser usada na modalidade por lotes.")
        if numero_lote is not None and numero_lote != lote.numero:
            raise ValueError("O número do lote diverge da faixa informada.")
        numero_lote = lote.numero
        faixa = (lote.inicio, lote.fim)
    else:
        faixa = None
    chaves = None if chaves_autorizadas is None else frozenset(chaves_autorizadas)
    if chaves is not None and not all(isinstance(chave, str) and chave for chave in chaves):
        raise ValueError("O conjunto autorizado contém uma chave inválida.")
    autorizacao = Autorizacao(
        plano_hash=plano_hash,
        modalidade=modalidade,
        chaves_autorizadas=chaves,
        numero_lote=numero_lote,
        faixa=faixa,
    )
    if confirmacao is None:
        return autorizacao
    if quantidade is None or configuracao is None:
        raise ValueError("A quantidade e o destino são obrigatórios para validar a confirmação.")

    if modalidade is ModalidadeAutorizacao.LOTES and (
        numero_lote is None or chaves is None or quantidade != len(chaves)
    ):
        return autorizacao
    esperada = criar_frase_confirmacao(plano_hash, quantidade, configuracao, numero_lote)
    if validar_confirmacao(confirmacao, esperada):
        object.__setattr__(autorizacao, "_confirmada", True)
    return autorizacao

"""Define a autorização explícita vinculada ao plano executável completo."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from hmac import compare_digest
from typing import TextIO

from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    PlanoPublicacao,
    assinatura_plano,
)


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
    """Associa consentimento ao conteúdo, destino, quantidade e conjunto exibidos."""

    plano_hash: str
    assinatura: str
    configuracao: ConfiguracaoPublicacao
    quantidade_total: int
    chaves_plano: tuple[str, ...]
    chaves_pendentes: tuple[str, ...]
    chaves_autorizadas: tuple[str, ...]
    modalidade: ModalidadeAutorizacao
    numero_lote: int | None = None
    faixa: tuple[int, int] | None = None
    _confirmada: bool = field(default=False, repr=False)

    def valida_para(self, plano: PlanoPublicacao) -> bool:
        """Recalcula a identidade integral e bloqueia qualquer divergência executável."""
        chaves_atuais = tuple(operacao.chave for operacao in plano.operacoes)
        if not self._confirmada:
            return False
        if not compare_digest(self.plano_hash, plano.hash_plano):
            return False
        if not compare_digest(self.assinatura, assinatura_plano(plano)):
            return False
        if self.configuracao != plano.configuracao:
            return False
        if self.quantidade_total != len(plano.operacoes) or self.chaves_plano != chaves_atuais:
            return False
        if len(set(self.chaves_pendentes)) != len(self.chaves_pendentes):
            return False
        if not set(self.chaves_pendentes).issubset(chaves_atuais):
            return False
        if self.modalidade is ModalidadeAutorizacao.INTEIRA:
            return self.chaves_autorizadas == self.chaves_pendentes and self.faixa is None
        if self.modalidade is not ModalidadeAutorizacao.LOTES or self.faixa is None:
            return False
        inicio, fim = self.faixa
        return (
            0 <= inicio < fim <= len(self.chaves_pendentes)
            and self.chaves_autorizadas == self.chaves_pendentes[inicio:fim]
        )


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
    chaves_autorizadas: Sequence[str],
    numero_lote: int | None = None,
) -> str:
    """Gera a frase que vincula quantidade, destino e código do plano completo."""
    configuracao = plano.configuracao
    inicio = "AUTORIZAR PUBLICAÇÃO" if numero_lote is None else f"AUTORIZAR LOTE {numero_lote}"
    return (
        f"{inicio} {len(chaves_autorizadas)} ITENS {configuracao.projeto} "
        f"{configuracao.area_path} {configuracao.iteration_path} {plano.hash_plano[:4].upper()}"
    )


def criar_autorizacao(
    *,
    plano: PlanoPublicacao,
    chaves_pendentes: Sequence[str],
    modalidade: ModalidadeAutorizacao,
    confirmacao: str | None = None,
    lote: Lote | None = None,
) -> Autorizacao:
    """Cria autorização somente a partir do plano e da seleção efetivamente exibidos."""
    if modalidade is ModalidadeAutorizacao.CANCELADA:
        raise ValueError("Uma publicação cancelada não pode gerar autorização.")
    chaves_plano = tuple(operacao.chave for operacao in plano.operacoes)
    pendentes = tuple(chaves_pendentes)
    if len(set(pendentes)) != len(pendentes) or not set(pendentes).issubset(chaves_plano):
        raise ValueError("As chaves pendentes divergem do plano completo.")

    if modalidade is ModalidadeAutorizacao.INTEIRA:
        if lote is not None:
            raise ValueError("A publicação inteira não aceita faixa de lote.")
        autorizadas = pendentes
        faixa = None
        numero_lote = None
    else:
        if lote is None or not 0 <= lote.inicio < lote.fim <= len(pendentes):
            raise ValueError("A modalidade por lotes exige uma faixa válida.")
        autorizadas = pendentes[lote.inicio : lote.fim]
        faixa = (lote.inicio, lote.fim)
        numero_lote = lote.numero

    autorizacao = Autorizacao(
        plano_hash=plano.hash_plano,
        assinatura=assinatura_plano(plano),
        configuracao=plano.configuracao,
        quantidade_total=len(plano.operacoes),
        chaves_plano=chaves_plano,
        chaves_pendentes=pendentes,
        chaves_autorizadas=autorizadas,
        modalidade=modalidade,
        numero_lote=numero_lote,
        faixa=faixa,
    )
    if confirmacao is None:
        return autorizacao
    esperada = criar_frase_confirmacao(plano, autorizadas, numero_lote)
    if validar_confirmacao(confirmacao, esperada):
        object.__setattr__(autorizacao, "_confirmada", True)
    return autorizacao

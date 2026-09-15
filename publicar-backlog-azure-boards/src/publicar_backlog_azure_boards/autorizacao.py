"""Define a autorização explícita e vinculada a um plano de publicação."""

from __future__ import annotations

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
    """Associa uma decisão explícita ao hash exato do plano apresentado."""

    plano_hash: str
    modalidade: ModalidadeAutorizacao
    _confirmada: bool = field(default=False, init=False, repr=False)

    def valida_para(self, plano_hash: str) -> bool:
        """Invalida a autorização se o plano foi alterado após a confirmação."""
        return self._confirmada and compare_digest(self.plano_hash, plano_hash)


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
) -> Autorizacao:
    """Cria uma autorização operacional apenas após validar a frase derivada do plano."""
    if not plano_hash:
        raise ValueError("O hash do plano é obrigatório para autorizar a publicação.")
    if modalidade is ModalidadeAutorizacao.CANCELADA:
        raise ValueError("Uma publicação cancelada não pode gerar autorização.")
    autorizacao = Autorizacao(plano_hash=plano_hash, modalidade=modalidade)
    if confirmacao is None:
        return autorizacao
    if quantidade is None or configuracao is None:
        raise ValueError("A quantidade e o destino são obrigatórios para validar a confirmação.")

    esperada = criar_frase_confirmacao(plano_hash, quantidade, configuracao, numero_lote)
    if validar_confirmacao(confirmacao, esperada):
        object.__setattr__(autorizacao, "_confirmada", True)
    return autorizacao

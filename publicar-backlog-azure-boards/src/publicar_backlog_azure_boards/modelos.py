"""Modelos imutáveis do backlog e de sua publicação planejada."""

from dataclasses import dataclass
from enum import StrEnum


class TipoItem(StrEnum):
    """Tipos de work item aceitos pelo contrato de backlog."""

    EPIC = "Epic"
    FEATURE = "Feature"
    HISTORIA_USUARIO = "User Story"
    BUG = "Bug"


@dataclass(frozen=True)
class ItemBacklog:
    """Representa os campos copiáveis de um item do backlog Markdown."""

    chave: str
    tipo: TipoItem
    titulo: str
    pai: str | None
    descricao: str
    criterios_aceitacao: str


@dataclass(frozen=True)
class OperacaoCriacao:
    """Representa uma criação planejada, sem executar qualquer escrita."""

    chave: str
    tipo: TipoItem
    titulo: str
    descricao: str
    criterios_aceitacao: str
    chave_pai: str | None


@dataclass(frozen=True)
class PlanoPublicacao:
    """Agrupa as operações imutáveis que poderão ser autorizadas posteriormente."""

    operacoes: tuple[OperacaoCriacao, ...]
    hash_plano: str

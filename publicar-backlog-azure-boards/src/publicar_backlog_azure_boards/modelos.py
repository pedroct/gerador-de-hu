"""Modelos imutáveis do backlog e de sua publicação planejada."""

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum


class TipoItem(StrEnum):
    """Tipos de work item aceitos pelo contrato de backlog."""

    EPIC = "Epic"
    FEATURE = "Feature"
    HISTORIA_USUARIO = "User Story"
    BUG = "Bug"


class EstadoReconciliacao(StrEnum):
    """Estados aceitos para uma reconciliação registrada no manifesto.

    Os dois estados terminais são distintos de propósito: ``RESOLVIDA_CRIADA`` afirma
    que o item existe no Azure Boards e por isso precisa estar em ``Manifesto.itens``;
    ``RESOLVIDA_NAO_CRIADA`` afirma o oposto, que o item não foi criado e por isso a
    chave deve continuar ausente de ``Manifesto.itens``. ``validar_manifesto`` rejeita
    qualquer manifesto em que a resolução registrada divirja dessa exigência, para que
    uma reconciliação marcada sem a atualização correspondente de ``itens`` nunca
    libere silenciosamente uma nova criação nem esconda um item já publicado.
    """

    PENDENTE = "pendente"
    RESOLVIDA_CRIADA = "resolvida_criada"
    RESOLVIDA_NAO_CRIADA = "resolvida_nao_criada"


@dataclass(frozen=True)
class MapeamentoTipos:
    """Mapeia os tipos documentais para os nomes reais do processo remoto."""

    epic: str = "Epic"
    feature: str = "Feature"
    historia_usuario: str = "User Story"
    bug: str = "Bug"

    def nome_remoto(self, tipo: TipoItem) -> str:
        """Devolve o tipo remoto configurado para o tipo documental."""
        return {
            TipoItem.EPIC: self.epic,
            TipoItem.FEATURE: self.feature,
            TipoItem.HISTORIA_USUARIO: self.historia_usuario,
            TipoItem.BUG: self.bug,
        }[tipo]

    def nomes_remotos(self) -> tuple[str, ...]:
        """Lista nomes remotos únicos em ordem hierárquica."""
        return tuple(dict.fromkeys((self.epic, self.feature, self.historia_usuario, self.bug)))

    def como_dict(self) -> dict[str, str]:
        """Serializa o mapeamento em chaves estáveis para hashes e relatórios."""
        return {
            "Epic": self.epic,
            "Feature": self.feature,
            "User Story": self.historia_usuario,
            "Bug": self.bug,
        }


@dataclass(frozen=True)
class ItemBacklog:
    """Representa os campos copiáveis de um item do backlog Markdown."""

    chave: str
    tipo: TipoItem
    titulo: str
    pai: str | None
    descricao: str
    criterios_aceitacao: str
    titulo_curto: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConfiguracaoPublicacao:
    """Representa o destino já validado para uma publicação."""

    organizacao: str
    projeto: str
    area_path: str
    iteration_path: str
    mapeamento_tipos: MapeamentoTipos = field(default_factory=MapeamentoTipos)


@dataclass(frozen=True)
class RegistroManifesto:
    """Associa uma chave documental a um work item já publicado."""

    id: int
    tipo: TipoItem
    url: str


@dataclass(frozen=True)
class ReconciliacaoPendente:
    """Preserva o contexto necessário para resolver uma criação incerta manualmente."""

    chave: str
    tipo_remoto: str
    titulo: str
    tipo: TipoItem | None = None
    destino: ConfiguracaoPublicacao | None = None
    hash_plano: str = ""
    timestamp: str = ""
    motivo: str = ""
    resolucao: str = EstadoReconciliacao.PENDENTE.value

    def __post_init__(self) -> None:
        """Rejeita typos que poderiam liberar uma criação sem resolução manual."""
        try:
            EstadoReconciliacao(self.resolucao)
        except (TypeError, ValueError) as erro:
            permitidos = ", ".join(estado.value for estado in EstadoReconciliacao)
            raise ValueError(
                f"A resolução da reconciliação é inválida; use um destes estados: {permitidos}."
            ) from erro


@dataclass(frozen=True)
class OperacaoCriacao:
    """Representa uma criação planejada, sem executar qualquer escrita."""

    chave: str
    tipo: TipoItem
    titulo: str
    descricao: str
    criterios_aceitacao: str
    chave_pai: str | None
    tipo_remoto: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanoPublicacao:
    """Agrupa as operações imutáveis que poderão ser autorizadas posteriormente."""

    operacoes: tuple[OperacaoCriacao, ...]
    hash_plano: str
    configuracao: ConfiguracaoPublicacao


def assinatura_plano(plano: PlanoPublicacao) -> str:
    """Calcula a identidade executável, incluindo destino e payload integral."""
    configuracao = plano.configuracao
    conteudo = {
        "hash_plano": plano.hash_plano,
        "configuracao": {
            "organizacao": configuracao.organizacao,
            "projeto": configuracao.projeto,
            "area_path": configuracao.area_path,
            "iteration_path": configuracao.iteration_path,
            "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
        },
        "operacoes": [
            {
                "chave": operacao.chave,
                "tipo": operacao.tipo.value,
                "tipo_remoto": operacao.tipo_remoto,
                "titulo": operacao.titulo,
                "descricao": operacao.descricao,
                "criterios_aceitacao": operacao.criterios_aceitacao,
                "chave_pai": operacao.chave_pai,
            }
            for operacao in plano.operacoes
        ],
    }
    serializado = json.dumps(conteudo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serializado.encode()).hexdigest()

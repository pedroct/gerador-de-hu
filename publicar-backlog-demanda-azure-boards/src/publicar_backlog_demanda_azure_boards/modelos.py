"""Modelos imutáveis do backlog e de sua publicação planejada."""

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
    depende_de: tuple[str, ...] = ()
    azure_boards_id: int | None = None


@dataclass(frozen=True)
class ItemPreexistente:
    """Item que o backlog declara já publicado, e que esta ferramenta não cria."""

    chave: str
    tipo: TipoItem
    id: int


@dataclass(frozen=True)
class Demanda:
    """Demanda de Negócio lida do Azure Boards, usada para derivar e exibir o destino.

    ``titulo`` e ``url`` existem apenas para apresentação no plano. Eles ficam de fora de
    hash, impressão de destino e manifesto de propósito: uma edição cosmética do título no
    Azure Boards invalidaria um manifesto válido e bloquearia uma retomada legítima.
    """

    id: int
    titulo: str
    area_path: str
    iteration_path: str
    url: str


@dataclass(frozen=True)
class ConfiguracaoPublicacao:
    """Representa o destino já validado para uma publicação vinculada a uma Demanda."""

    organizacao: str
    projeto: str
    area_path: str
    iteration_path: str
    demanda_id: int
    mapeamento_tipos: MapeamentoTipos = field(default_factory=MapeamentoTipos)


@dataclass(frozen=True)
class RegistroManifesto:
    """Associa uma chave documental a um work item já publicado."""

    id: int
    tipo: TipoItem
    url: str
    # Um registro pré-existente veio declarado no backlog, não de uma criação nossa.
    # Ele serve de pai para os filhos e nada mais: não conta como criação, não entra em
    # reconciliação e não é recriado numa retomada.
    preexistente: bool = False


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
    depende_de: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanoPublicacao:
    """Agrupa as operações imutáveis que poderão ser autorizadas posteriormente."""

    operacoes: tuple[OperacaoCriacao, ...]
    hash_plano: str
    configuracao: ConfiguracaoPublicacao
    preexistentes: tuple[ItemPreexistente, ...] = ()

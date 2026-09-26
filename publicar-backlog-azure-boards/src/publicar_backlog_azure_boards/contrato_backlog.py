"""Regras determinísticas do contrato Markdown de backlog."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

ITEM_RE = re.compile(
    r"^(?P<marks>#{1,6}) (?P<key>[1-9]\d*\.\d+\.\d+) "
    r"\[(?P<kind>Epic|Feature|User Story|Bug)\] (?P<title>\S.*)$"
)
WORK_ITEM_HINT_RE = re.compile(r"^#+ .*(?:\[Epic\]|\[Feature\]|\[User Story\]|\[Bug\])")
TAGS = "Tags"
LIMITE_TAG = 400
DEPENDE_DE = "Depende de"
CHAVE_RE = re.compile(r"^[1-9]\d*\.\d+\.\d+$")
AZURE_BOARDS_ID = "Azure Boards ID"
CONTAINER_KINDS = ("Epic", "Feature")

SECTION_NAMES = {
    "Parent",
    "Título curto",
    "Description",
    "Acceptance Criteria",
    "Refinement Status",
    TAGS,
    DEPENDE_DE,
    AZURE_BOARDS_ID,
}
IMPLEMENTATION_EVIDENCE = "Implementation Evidence"
ACCEPTANCE_CRITERIA = "Acceptance Criteria"
REFINEMENT_STATUS = "Refinement Status"
USER_STORY = "User Story"
BUG = "Bug"
LEAF_KINDS = (USER_STORY, BUG)


@dataclass
class BacklogItem:
    key: str
    kind: str
    title: str
    level: int
    sections: dict[str, list[str]] = field(default_factory=dict)

    def section(self, name: str) -> str:
        return "\n".join(self.sections.get(name, [])).strip()


def normalizar_tags(bruto: str) -> tuple[tuple[str, ...], list[str]]:
    """Normaliza a seção ``Tags`` e devolve também os erros de formato encontrados.

    Uma seção ausente é legítima e devolve vazio sem erro; uma seção presente e vazia
    é erro de quem a valida, não desta função, porque só o chamador sabe distinguir
    "sem heading" de "heading sem conteúdo".
    """
    texto = bruto.strip()
    if not texto:
        return (), []

    erros: list[str] = []
    tags: list[str] = []
    for parte in texto.split(","):
        tag = parte.strip()
        if not tag:
            erros.append("a seção Tags possui uma tag vazia entre vírgulas")
            continue
        if ";" in tag:
            erros.append(f"a tag '{tag}' contém ';', que o Azure Boards usa como separador")
            continue
        if len(tag) > LIMITE_TAG:
            erros.append(
                f"a tag '{tag}' passa de {LIMITE_TAG} caracteres, o limite do Azure Boards"
            )
            continue
        if tag not in tags:
            tags.append(tag)

    if erros:
        return (), erros
    return tuple(tags), []


def normalizar_chaves(bruto: str) -> tuple[tuple[str, ...], list[str]]:
    """Normaliza uma lista de chaves documentais separadas por vírgula."""
    texto = bruto.strip()
    if not texto:
        return (), []

    erros: list[str] = []
    chaves: list[str] = []
    for parte in texto.split(","):
        chave = parte.strip().strip("`").strip()
        if not chave:
            erros.append("a seção Depende de possui uma chave vazia entre vírgulas")
            continue
        if not CHAVE_RE.match(chave):
            erros.append(f"'{chave}' não é uma chave documental no formato E.F.S")
            continue
        if chave not in chaves:
            chaves.append(chave)

    if erros:
        return (), erros
    return tuple(chaves), []


def normalizar_id(bruto: str) -> tuple[int | None, list[str]]:
    """Lê o ID de um work item já publicado, recusando o que não for inteiro positivo.

    Um ID digitado com um dígito a menos aponta para outro work item qualquer, então a
    conversão nunca pode estourar ``ValueError`` cru no meio do planejamento. ``str.isdigit()``
    sozinho não bastaria: aceita sobrescritos como "²" (categoria Unicode "No", não "Nd"), que
    fazem ``int()`` estourar, e dígitos não-ASCII como "٣", que ``int()`` converteria em
    silêncio para outro work item. A checagem ASCII fecha as duas portas.
    """
    texto = bruto.strip().strip("`").strip()
    if not texto:
        return None, []
    if not texto.isascii() or not texto.isdigit() or int(texto) <= 0:
        return None, [f"'{texto}' não é um ID de work item inteiro e positivo"]
    return int(texto), []


def detectar_ciclo(pares: Sequence[tuple[str, Sequence[str]]]) -> list[str] | None:
    """Devolve o ciclo de dependências encontrado, em ordem, ou ``None``.

    Um item que depende de si mesmo é um ciclo de um nó e precisa ser pego aqui:
    uma detecção que só compare pares distintos deixa esse caso passar.
    """
    arestas = {chave: list(destinos) for chave, destinos in pares}
    estado: dict[str, int] = {}
    pilha: list[str] = []

    def visitar(chave: str) -> list[str] | None:
        if estado.get(chave) == 2:
            return None
        if estado.get(chave) == 1:
            return pilha[pilha.index(chave) :]
        estado[chave] = 1
        pilha.append(chave)
        for destino in arestas.get(chave, []):
            ciclo = visitar(destino)
            if ciclo is not None:
                return ciclo
        pilha.pop()
        estado[chave] = 2
        return None

    for chave in arestas:
        ciclo = visitar(chave)
        if ciclo is not None:
            return ciclo
    return None


def _new_item(match: re.Match[str]) -> BacklogItem:
    return BacklogItem(
        key=match.group("key"),
        kind=match.group("kind"),
        title=match.group("title"),
        level=len(match.group("marks")),
    )


def _section_heading(raw: str, level: int) -> str | None:
    prefix = "#" * (level + 1) + " "
    if not raw.startswith(prefix):
        return None
    section_name = raw[len(prefix) :]
    if section_name in SECTION_NAMES:
        return section_name
    # Mesma normalização usada por ``interpretar_markdown._nome_secao``: um heading
    # "Implementation Evidence <sufixo>" é uma seção própria, separada da Description
    # anterior, para que os dois parsers concordem sobre onde a Description termina.
    if section_name.startswith(f"{IMPLEMENTATION_EVIDENCE} "):
        return IMPLEMENTATION_EVIDENCE
    return None


def parse_backlog(text: str) -> list[BacklogItem]:
    """Extrai itens e seções do Markdown sem acessar o filesystem."""
    items: list[BacklogItem] = []
    current: BacklogItem | None = None
    section: str | None = None
    in_fence = False
    for raw in text.splitlines():
        if raw.startswith("```"):
            in_fence = not in_fence
        match = ITEM_RE.match(raw) if not in_fence else None
        if match:
            current = _new_item(match)
            items.append(current)
            section = None
            continue
        if not current or in_fence:
            continue
        section_name = _section_heading(raw, current.level)
        if section_name:
            section = section_name
            current.sections.setdefault(section, [])
            continue
        if section:
            current.sections[section].append(raw)
    return items


def _malformed_work_item_headings(text: str) -> list[str]:
    malformed: list[str] = []
    in_fence = False
    for raw in text.splitlines():
        if raw.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and WORK_ITEM_HINT_RE.match(raw) and not ITEM_RE.match(raw):
            malformed.append(raw)
    return malformed


def _has_origin_reference(text: str) -> bool:
    marker = "Origem na spec:"
    for line in text.splitlines():
        if marker in line and line.split(marker, 1)[1].strip():
            return True
    return False


def _parts(key: str) -> tuple[int, int, int]:
    parts = tuple(int(part) for part in key.split("."))
    return parts[0], parts[1], parts[2]


def _parent_value(item: BacklogItem) -> str:
    return item.section("Parent").strip().strip("`")


def _validate_hierarchy(item: BacklogItem, keys: set[str]) -> list[str]:
    errors: list[str] = []
    expected = {
        "Epic": (2, "épicos"),
        "Feature": (3, "features"),
        USER_STORY: (4, "histórias"),
        BUG: (4, "bugs"),
    }
    marks, _ = expected[item.kind]
    if item.level != marks:
        errors.append(f"{item.key} tem nível de título incorreto para {item.kind}")

    e, f, s = _parts(item.key)
    if item.kind == "Epic":
        if (f, s) != (0, 0):
            errors.append(f"{item.key} não é uma chave Epic válida")
        return errors

    if f == 0 or (item.kind == "Feature" and s != 0) or (item.kind in LEAF_KINDS and s == 0):
        errors.append(f"{item.key} não é uma chave {item.kind} válida")
    expected_parent = f"{e}.0.0" if item.kind == "Feature" else f"{e}.{f}.0"
    actual = _parent_value(item)
    if actual != expected_parent:
        errors.append(
            f"{item.key} esperava o pai {expected_parent}, recebeu {actual or '<ausente>'}"
        )
    if expected_parent not in keys:
        errors.append(f"{item.key} não possui o pai {expected_parent}")
    return errors


def _validate_leaf_item(item: BacklogItem) -> list[str]:
    status = item.section(REFINEMENT_STATUS)
    errors: list[str] = []
    # Backlogs novos não serializam o status 3C. Se um backlog antigo ainda o trouxer,
    # preserve a validação para evitar aceitar uma inconsistência durante a migração.
    if status:
        errors.extend(
            f"{item.key} não possui o campo de refinamento {field_name}"
            for field_name in ("Card", "Conversation", "Confirmation", "Prontidão")
            if f"{field_name}:" not in status
        )
        confirmation = next(
            (state for state in ("Ausente", "Parcial") if f"Confirmation: {state}" in status),
            None,
        )
        if confirmation and item.section(ACCEPTANCE_CRITERIA):
            errors.append(
                f"{item.key} possui Acceptance Criteria enquanto Confirmation está {confirmation}"
            )
    if ACCEPTANCE_CRITERIA not in item.sections:
        errors.append(f"{item.key} não possui o título Acceptance Criteria")
    return errors


def _validate_item(
    item: BacklogItem, keys: set[str], folhas: set[str], com_id: set[str]
) -> list[str]:
    errors = _validate_hierarchy(item, keys)
    if item.kind in LEAF_KINDS:
        errors.extend(_validate_leaf_item(item))
    if not item.section("Description"):
        errors.append(f"{item.key} possui Description vazia")
    origin_text = item.section("Description") + "\n" + item.section(REFINEMENT_STATUS)
    if not _has_origin_reference(origin_text):
        errors.append(f"{item.key} não possui Origem na spec")
    if TAGS in item.sections:
        tags, erros_tags = normalizar_tags(item.section(TAGS))
        errors.extend(f"{item.key}: {erro}" for erro in erros_tags)
        if not tags and not erros_tags:
            errors.append(f"{item.key} possui a seção Tags presente e vazia")
    if DEPENDE_DE in item.sections:
        if item.key not in folhas:
            errors.append(f"{item.key} declara Depende de, permitido só em item de folha")
        chaves, erros_chaves = normalizar_chaves(item.section(DEPENDE_DE))
        errors.extend(f"{item.key}: {erro}" for erro in erros_chaves)
        if not chaves and not erros_chaves:
            errors.append(f"{item.key} possui a seção Depende de presente e vazia")
        for chave in chaves:
            if chave not in keys:
                errors.append(f"{item.key} depende de {chave}, que não existe no backlog")
            elif chave not in folhas:
                errors.append(f"{item.key} depende de {chave}, que não é item de folha")
    if AZURE_BOARDS_ID in item.sections:
        valor, erros_id = normalizar_id(item.section(AZURE_BOARDS_ID))
        errors.extend(f"{item.key}: {erro}" for erro in erros_id)
        if valor is None and not erros_id:
            errors.append(f"{item.key} possui a seção Azure Boards ID presente e vazia")
        if item.kind not in CONTAINER_KINDS:
            errors.append(f"{item.key} declara Azure Boards ID, permitido só em Epic e Feature")
        elif valor is not None and item.kind == "Feature" and _parent_value(item) not in com_id:
            errors.append(
                f"{item.key} declara Azure Boards ID, mas seu pai {_parent_value(item)} não declara"
            )
    return errors


def _group_key(item: BacklogItem) -> tuple[tuple[str, str], int]:
    e, f, s = _parts(item.key)
    if item.kind == "Epic":
        return ("épicos", "raiz"), e
    if item.kind == "Feature":
        return ("features", f"{e}.0.0"), f
    return ("itens", f"{e}.{f}.0"), s


def _validate_groups(groups: dict[tuple[str, str], list[int]], update_mode: bool) -> list[str]:
    errors: list[str] = []
    for (label, parent), numbers in groups.items():
        if numbers != sorted(numbers):
            errors.append(f"{label} sob {parent} deve estar em ordem crescente")
        if update_mode:
            continue
        ordered = sorted(set(numbers))
        if not ordered or ordered == list(range(1, len(ordered) + 1)):
            continue
        if ordered[0] != 1:
            errors.append(f"{label} sob {parent} deve começar em 1")
        else:
            errors.append(f"{label} sob {parent} deve ser contíguo")
    return errors


def validate_backlog(text: str, update_mode: bool = False) -> list[str]:
    """Valida a estrutura de um backlog e devolve todos os erros encontrados."""
    items = parse_backlog(text)
    errors: list[str] = []
    if not items:
        errors.append("o backlog deve conter pelo menos um item de trabalho")
    for heading in _malformed_work_item_headings(text):
        errors.append(f"título de item de trabalho inválido: {heading}")
    seen: set[str] = set()
    keys = {item.key for item in items}
    folhas = {item.key for item in items if item.kind in LEAF_KINDS}
    com_id = {
        item.key
        for item in items
        if AZURE_BOARDS_ID in item.sections and normalizar_id(item.section(AZURE_BOARDS_ID))[0]
    }
    groups: dict[tuple[str, str], list[int]] = {}
    for item in items:
        if item.key in seen:
            errors.append(f"chave duplicada: {item.key}")
        seen.add(item.key)
        errors.extend(_validate_item(item, keys, folhas, com_id))
        group, number = _group_key(item)
        groups.setdefault(group, []).append(number)
    errors.extend(_validate_groups(groups, update_mode))
    ciclo = detectar_ciclo(
        [(item.key, normalizar_chaves(item.section(DEPENDE_DE))[0]) for item in items]
    )
    if ciclo is not None:
        errors.append(f"ciclo de dependência entre {' → '.join(ciclo)}")
    return errors

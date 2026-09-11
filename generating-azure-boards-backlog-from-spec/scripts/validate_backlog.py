from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ITEM_RE = re.compile(
    r"^(?P<marks>#{1,6}) (?P<key>[1-9]\d*\.\d+\.\d+) "
    r"\[(?P<kind>Epic|Feature|User Story)\] (?P<title>\S.*)$"
)
WORK_ITEM_HINT_RE = re.compile(r"^#+ .*(?:\[Epic\]|\[Feature\]|\[User Story\])")
SECTION_NAMES = {"Parent", "Description", "Acceptance Criteria", "Refinement Status"}
ACCEPTANCE_CRITERIA = "Acceptance Criteria"
REFINEMENT_STATUS = "Refinement Status"
USER_STORY = "User Story"


@dataclass
class BacklogItem:
    key: str
    kind: str
    title: str
    level: int
    sections: dict[str, list[str]] = field(default_factory=dict)

    def section(self, name: str) -> str:
        return "\n".join(self.sections.get(name, [])).strip()


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
    return section_name if section_name in SECTION_NAMES else None


def parse_backlog(text: str) -> list[BacklogItem]:
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
    expected = {"Epic": (2, "epics"), "Feature": (3, "features"), USER_STORY: (4, "stories")}
    marks, _ = expected[item.kind]
    if item.level != marks:
        errors.append(f"{item.key} has wrong heading level for {item.kind}")

    e, f, s = _parts(item.key)
    if item.kind == "Epic":
        if (f, s) != (0, 0):
            errors.append(f"{item.key} is not a valid Epic key")
        return errors

    if f == 0 or (item.kind == "Feature" and s != 0) or (item.kind == USER_STORY and s == 0):
        errors.append(f"{item.key} is not a valid {item.kind} key")
    expected_parent = f"{e}.0.0" if item.kind == "Feature" else f"{e}.{f}.0"
    actual = _parent_value(item)
    if actual != expected_parent:
        errors.append(f"{item.key} expected parent {expected_parent}, got {actual or '<missing>'}")
    if expected_parent not in keys:
        errors.append(f"{item.key} parent {expected_parent} does not exist")
    return errors


def _validate_user_story(item: BacklogItem) -> list[str]:
    status = item.section(REFINEMENT_STATUS)
    errors = [
        f"{item.key} is missing refinement field {field_name}"
        for field_name in ("Card", "Conversation", "Confirmation", "Prontidão")
        if f"{field_name}:" not in status
    ]
    confirmation = next(
        (state for state in ("Ausente", "Parcial") if f"Confirmation: {state}" in status),
        None,
    )
    if confirmation and item.section(ACCEPTANCE_CRITERIA):
        errors.append(
            f"{item.key} has Acceptance Criteria while Confirmation is {confirmation}"
        )
    if ACCEPTANCE_CRITERIA not in item.sections:
        errors.append(f"{item.key} is missing Acceptance Criteria heading")
    if REFINEMENT_STATUS not in item.sections:
        errors.append(f"{item.key} is missing Refinement Status")
    return errors


def _validate_item(item: BacklogItem, keys: set[str]) -> list[str]:
    errors = _validate_hierarchy(item, keys)
    if item.kind == USER_STORY:
        errors.extend(_validate_user_story(item))
    if not item.section("Description"):
        errors.append(f"{item.key} has empty Description")
    origin_text = item.section("Description") + "\n" + item.section(REFINEMENT_STATUS)
    if not _has_origin_reference(origin_text):
        errors.append(f"{item.key} is missing Origem na spec")
    return errors


def _group_key(item: BacklogItem) -> tuple[tuple[str, str], int]:
    e, f, s = _parts(item.key)
    if item.kind == "Epic":
        return ("epics", "root"), e
    if item.kind == "Feature":
        return ("features", f"{e}.0.0"), f
    return ("stories", f"{e}.{f}.0"), s


def _validate_groups(groups: dict[tuple[str, str], list[int]], update_mode: bool) -> list[str]:
    errors: list[str] = []
    for (label, parent), numbers in groups.items():
        if numbers != sorted(numbers):
            errors.append(f"{label} under {parent} must be ascending")
        if update_mode:
            continue
        ordered = sorted(set(numbers))
        if not ordered or ordered == list(range(1, len(ordered) + 1)):
            continue
        if ordered[0] != 1:
            errors.append(f"{label} under {parent} must start at 1")
        else:
            errors.append(f"{label} under {parent} must be contiguous")
    return errors


def validate_backlog(text: str, update_mode: bool = False) -> list[str]:
    items = parse_backlog(text)
    errors: list[str] = []
    if not items:
        errors.append("backlog must contain at least one work item")
    for heading in _malformed_work_item_headings(text):
        errors.append(f"invalid work item heading: {heading}")
    seen: set[str] = set()
    keys = {item.key for item in items}
    groups: dict[tuple[str, str], list[int]] = {}
    for item in items:
        if item.key in seen:
            errors.append(f"duplicate key: {item.key}")
        seen.add(item.key)
        errors.extend(_validate_item(item, keys))
        group, number = _group_key(item)
        groups.setdefault(group, []).append(number)
    errors.extend(_validate_groups(groups, update_mode))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an Azure Boards backlog Markdown file")
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--update",
        action="store_true",
        help="allow numbering gaps in an updated backlog",
    )
    args = parser.parse_args(argv)
    try:
        text = args.path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors = validate_backlog(text, update_mode=args.update)
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("Backlog structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

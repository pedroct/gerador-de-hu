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


@dataclass
class BacklogItem:
    key: str
    kind: str
    title: str
    level: int
    sections: dict[str, list[str]] = field(default_factory=dict)

    def section(self, name: str) -> str:
        return "\n".join(self.sections.get(name, [])).strip()


def parse_backlog(text: str) -> list[BacklogItem]:
    items: list[BacklogItem] = []
    current: BacklogItem | None = None
    section: str | None = None
    in_fence = False
    for raw in text.splitlines():
        if raw.startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else ITEM_RE.match(raw)
        if match:
            current = BacklogItem(
                key=match.group("key"),
                kind=match.group("kind"),
                title=match.group("title"),
                level=len(match.group("marks")),
            )
            items.append(current)
            section = None
            continue
        if current and not in_fence:
            prefix = "#" * (current.level + 1) + " "
            if raw.startswith(prefix) and raw[len(prefix) :] in SECTION_NAMES:
                section = raw[len(prefix) :]
                current.sections.setdefault(section, [])
                continue
        if current and section:
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
    expected = {"Epic": (2, "epics"), "Feature": (3, "features"), "User Story": (4, "stories")}

    for item in items:
        if item.key in seen:
            errors.append(f"duplicate key: {item.key}")
        seen.add(item.key)
        marks, label = expected[item.kind]
        if item.level != marks:
            errors.append(f"{item.key} has wrong heading level for {item.kind}")
        e, f, s = _parts(item.key)
        if item.kind == "Epic":
            if (f, s) != (0, 0):
                errors.append(f"{item.key} is not a valid Epic key")
            groups.setdefault((label, "root"), []).append(e)
        elif item.kind == "Feature":
            if f == 0 or s != 0:
                errors.append(f"{item.key} is not a valid Feature key")
            expected_parent = f"{e}.0.0"
            actual = _parent_value(item)
            if actual != expected_parent:
                errors.append(
                    f"{item.key} expected parent {expected_parent}, got {actual or '<missing>'}"
                )
            if expected_parent not in keys:
                errors.append(f"{item.key} parent {expected_parent} does not exist")
            groups.setdefault((label, expected_parent), []).append(f)
        else:
            if f == 0 or s == 0:
                errors.append(f"{item.key} is not a valid User Story key")
            expected_parent = f"{e}.{f}.0"
            actual = _parent_value(item)
            if actual != expected_parent:
                errors.append(
                    f"{item.key} expected parent {expected_parent}, got {actual or '<missing>'}"
                )
            if expected_parent not in keys:
                errors.append(f"{item.key} parent {expected_parent} does not exist")
            groups.setdefault((label, expected_parent), []).append(s)
            status = item.section("Refinement Status")
            for field_name in ("Card", "Conversation", "Confirmation", "Prontidão"):
                if f"{field_name}:" not in status:
                    errors.append(f"{item.key} is missing refinement field {field_name}")
            for confirmation in ("Ausente", "Parcial"):
                if f"Confirmation: {confirmation}" in status and item.section(
                    "Acceptance Criteria"
                ):
                    errors.append(
                        f"{item.key} has Acceptance Criteria while Confirmation is {confirmation}"
                    )
            if "Acceptance Criteria" not in item.sections:
                errors.append(f"{item.key} is missing Acceptance Criteria heading")
            if "Refinement Status" not in item.sections:
                errors.append(f"{item.key} is missing Refinement Status")
        if not item.section("Description"):
            errors.append(f"{item.key} has empty Description")
        origin_text = item.section("Description") + "\n" + item.section("Refinement Status")
        if not _has_origin_reference(origin_text):
            errors.append(f"{item.key} is missing Origem na spec")

    for (label, parent), numbers in groups.items():
        if numbers != sorted(numbers):
            errors.append(f"{label} under {parent} must be ascending")
        if not update_mode:
            ordered = sorted(set(numbers))
            if ordered and ordered != list(range(1, len(ordered) + 1)):
                if ordered[0] != 1:
                    errors.append(f"{label} under {parent} must start at 1")
                else:
                    errors.append(f"{label} under {parent} must be contiguous")
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

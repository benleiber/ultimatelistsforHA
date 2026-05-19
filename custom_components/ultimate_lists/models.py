"""Domain models for Ultimate Lists."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .const import DEFAULT_LIST_TYPE, DEFAULT_SORT_MODE


def utcnow_iso() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(UTC).isoformat()


def new_id() -> str:
    """Generate a short opaque id."""
    return uuid4().hex


@dataclass(slots=True)
class UltimateListSection:
    """A named section inside a list."""

    id: str
    title: str
    type: str = "normal"
    sort_order: int = 0


@dataclass(slots=True)
class UltimateListItem:
    """A single list item."""

    id: str
    text: str
    checked: bool = False
    important: bool = False
    section_id: str | None = None
    notes: str = ""
    quantity: str = ""
    tags: list[str] = field(default_factory=list)
    sort_order: int = 0
    created_at: str = field(default_factory=utcnow_iso)
    completed_at: str | None = None


@dataclass(slots=True)
class UltimateList:
    """A household list."""

    id: str
    title: str
    type: str = DEFAULT_LIST_TYPE
    icon: str = "mdi:note-text-outline"
    color: str = ""
    sort_mode: str = DEFAULT_SORT_MODE
    archived: bool = False
    sections: list[UltimateListSection] = field(default_factory=list)
    items: list[UltimateListItem] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow_iso)
    updated_at: str = field(default_factory=utcnow_iso)

    @property
    def incomplete_count(self) -> int:
        """Return the number of incomplete items."""
        return sum(1 for item in self.items if not item.checked)


def item_from_dict(data: dict[str, Any]) -> UltimateListItem:
    """Create an item from persisted data."""
    return UltimateListItem(
        id=str(data["id"]),
        text=str(data["text"]),
        checked=bool(data.get("checked", False)),
        important=bool(data.get("important", False)),
        section_id=data.get("section_id"),
        notes=str(data.get("notes", "")),
        quantity=str(data.get("quantity", "")),
        tags=[str(tag) for tag in data.get("tags", [])],
        sort_order=int(data.get("sort_order", 0)),
        created_at=str(data.get("created_at", utcnow_iso())),
        completed_at=data.get("completed_at"),
    )


def section_from_dict(data: dict[str, Any]) -> UltimateListSection:
    """Create a section from persisted data."""
    return UltimateListSection(
        id=str(data["id"]),
        title=str(data["title"]),
        type=str(data.get("type", "normal")),
        sort_order=int(data.get("sort_order", 0)),
    )


def list_from_dict(data: dict[str, Any]) -> UltimateList:
    """Create a list from persisted data."""
    return UltimateList(
        id=str(data["id"]),
        title=str(data["title"]),
        type=str(data.get("type", DEFAULT_LIST_TYPE)),
        icon=str(data.get("icon", "mdi:note-text-outline")),
        color=str(data.get("color", "")),
        sort_mode=str(data.get("sort_mode", DEFAULT_SORT_MODE)),
        archived=bool(data.get("archived", False)),
        sections=[section_from_dict(section) for section in data.get("sections", [])],
        items=[item_from_dict(item) for item in data.get("items", [])],
        created_at=str(data.get("created_at", utcnow_iso())),
        updated_at=str(data.get("updated_at", utcnow_iso())),
    )


def item_to_dict(item: UltimateListItem) -> dict[str, Any]:
    """Serialize an item."""
    return asdict(item)


def section_to_dict(section: UltimateListSection) -> dict[str, Any]:
    """Serialize a section."""
    return asdict(section)


def list_to_dict(ultimate_list: UltimateList) -> dict[str, Any]:
    """Serialize a list."""
    return {
        **asdict(ultimate_list),
        "sections": [section_to_dict(section) for section in ultimate_list.sections],
        "items": [item_to_dict(item) for item in ultimate_list.items],
    }


def make_list(
    title: str,
    *,
    list_type: str = DEFAULT_LIST_TYPE,
    icon: str = "mdi:cart-outline",
    color: str = "",
    sort_mode: str = DEFAULT_SORT_MODE,
) -> UltimateList:
    """Create a new list."""
    return UltimateList(
        id=new_id(),
        title=title,
        type=list_type,
        icon=icon,
        color=color,
        sort_mode=sort_mode,
    )


def make_item(
    text: str,
    *,
    quantity: str = "",
    notes: str = "",
    section_id: str | None = None,
    important: bool = False,
    tags: list[str] | None = None,
    sort_order: int = 0,
) -> UltimateListItem:
    """Create a new list item."""
    return UltimateListItem(
        id=new_id(),
        text=text,
        quantity=quantity,
        notes=notes,
        section_id=section_id,
        important=important,
        tags=tags or [],
        sort_order=sort_order,
    )


def make_section(title: str, *, section_type: str = "normal", sort_order: int = 0) -> UltimateListSection:
    """Create a new list section."""
    return UltimateListSection(
        id=new_id(),
        title=title,
        type=section_type,
        sort_order=sort_order,
    )


def sort_items_for_display(ultimate_list: UltimateList) -> list[UltimateListItem]:
    """Return items in UI display order."""
    items = list(ultimate_list.items)
    if ultimate_list.sort_mode == "unchecked_first":
        return sorted(
            items,
            key=lambda item: (
                item.checked,
                0 if item.important else 1,
                item.sort_order,
                item.text.lower(),
            ),
        )
    if ultimate_list.sort_mode == "priority":
        return sorted(
            items,
            key=lambda item: (
                item.checked,
                0 if item.important else 1,
                item.sort_order,
                item.text.lower(),
            ),
        )
    if ultimate_list.sort_mode == "sectioned":
        return sorted(
            items,
            key=lambda item: (
                item.section_id or "",
                item.checked,
                item.sort_order,
                item.text.lower(),
            ),
        )
    return sorted(items, key=lambda item: (item.sort_order, item.text.lower()))

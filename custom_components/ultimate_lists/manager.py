"""Runtime manager for Ultimate Lists."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from homeassistant.exceptions import HomeAssistantError

from .const import LIST_TYPES, SECTION_TYPES, SORT_MODES
from .models import (
    UltimateList,
    UltimateListItem,
    UltimateListSection,
    item_to_dict,
    list_to_dict,
    make_item,
    make_list,
    make_section,
    sort_items_for_display,
)
from .storage import UltimateListsStore

type Listener = Callable[[], None]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class UltimateListsManager:
    """Coordinate in-memory list operations and persistence."""

    def __init__(self, store: UltimateListsStore) -> None:
        self.store = store
        self._listeners: list[Listener] = []

    def async_add_listener(self, listener: Listener) -> Callable[[], None]:
        """Register a callback for list updates."""
        self._listeners.append(listener)

        def remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    async def async_initialize(self) -> None:
        """Load initial data."""
        await self.store.async_load()

    def get_lists(self, *, include_archived: bool = False) -> list[UltimateList]:
        """Return all lists."""
        lists = list(self.store.lists.values())
        if not include_archived:
            lists = [ultimate_list for ultimate_list in lists if not ultimate_list.archived]
        return sorted(lists, key=lambda ultimate_list: ultimate_list.title.lower())

    def get_list(self, list_id: str) -> UltimateList:
        """Return a single list."""
        try:
            return self.store.lists[list_id]
        except KeyError as err:
            msg = f"Unknown list_id {list_id}"
            raise HomeAssistantError(msg) from err

    def get_list_by_entity_id(self, entity_id: str) -> UltimateList | None:
        """Resolve a list from an entity id."""
        slug = entity_id.removeprefix("todo.")
        for ultimate_list in self.store.lists.values():
            if self.slugify(ultimate_list.title) == slug:
                return ultimate_list
        return None

    @staticmethod
    def slugify(value: str) -> str:
        """Create a Home Assistant-style slug."""
        return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")

    async def _commit(self) -> None:
        await self.store.async_save()
        self._notify()

    def _touch(self, ultimate_list: UltimateList) -> None:
        ultimate_list.updated_at = _now_iso()

    async def async_create_list(
        self,
        title: str,
        *,
        list_type: str = "dynamic",
        icon: str = "mdi:cart-outline",
        color: str = "",
        sort_mode: str = "unchecked_first",
    ) -> UltimateList:
        """Create a list."""
        if list_type not in LIST_TYPES:
            raise HomeAssistantError(f"Unsupported list type: {list_type}")
        if sort_mode not in SORT_MODES:
            raise HomeAssistantError(f"Unsupported sort mode: {sort_mode}")
        ultimate_list = make_list(
            title,
            list_type=list_type,
            icon=icon,
            color=color,
            sort_mode=sort_mode,
        )
        self.store.lists[ultimate_list.id] = ultimate_list
        await self._commit()
        return ultimate_list

    async def async_rename_list(self, list_id: str, title: str) -> UltimateList:
        """Rename a list."""
        ultimate_list = self.get_list(list_id)
        ultimate_list.title = title
        self._touch(ultimate_list)
        await self._commit()
        return ultimate_list

    async def async_delete_list(self, list_id: str) -> None:
        """Delete a list."""
        if list_id not in self.store.lists:
            raise HomeAssistantError(f"Unknown list_id {list_id}")
        del self.store.lists[list_id]
        if not self.store.lists:
            default_list = make_list("Grocery")
            self.store.lists[default_list.id] = default_list
        await self._commit()

    async def async_archive_list(self, list_id: str, archived: bool = True) -> UltimateList:
        """Archive or restore a list."""
        ultimate_list = self.get_list(list_id)
        ultimate_list.archived = archived
        self._touch(ultimate_list)
        await self._commit()
        return ultimate_list

    async def async_duplicate_list(self, list_id: str, title: str | None = None) -> UltimateList:
        """Duplicate an existing list."""
        source = self.get_list(list_id)
        duplicate = make_list(
            title or f"{source.title} Copy",
            list_type=source.type,
            icon=source.icon,
            color=source.color,
            sort_mode=source.sort_mode,
        )
        section_map: dict[str, str] = {}
        for index, section in enumerate(source.sections):
            new_section = make_section(section.title, section_type=section.type, sort_order=index)
            duplicate.sections.append(new_section)
            section_map[section.id] = new_section.id
        for index, item in enumerate(source.items):
            duplicate_item = make_item(
                item.text,
                quantity=item.quantity,
                notes=item.notes,
                section_id=section_map.get(item.section_id) if item.section_id else None,
                important=item.important,
                tags=list(item.tags),
                sort_order=index,
            )
            duplicate_item.checked = item.checked
            duplicate_item.completed_at = item.completed_at
            duplicate.items.append(duplicate_item)
        self.store.lists[duplicate.id] = duplicate
        await self._commit()
        return duplicate

    async def async_add_item(
        self,
        list_id: str,
        text: str,
        *,
        quantity: str = "",
        notes: str = "",
        section_id: str | None = None,
        important: bool = False,
        tags: list[str] | None = None,
    ) -> UltimateListItem:
        """Append an item to a list."""
        ultimate_list = self.get_list(list_id)
        item = make_item(
            text,
            quantity=quantity,
            notes=notes,
            section_id=section_id,
            important=important,
            tags=tags or [],
            sort_order=len(ultimate_list.items),
        )
        ultimate_list.items.append(item)
        self._touch(ultimate_list)
        await self._commit()
        return item

    async def async_update_item(self, list_id: str, item_id: str, updates: dict[str, Any]) -> UltimateListItem:
        """Update an item."""
        ultimate_list = self.get_list(list_id)
        item = self._get_item(ultimate_list, item_id)
        for key in ("text", "notes", "quantity", "section_id"):
            if key in updates and updates[key] is not None:
                setattr(item, key, str(updates[key]))
        if "important" in updates:
            item.important = bool(updates["important"])
        if "tags" in updates and updates["tags"] is not None:
            item.tags = [str(tag) for tag in updates["tags"]]
        if "checked" in updates:
            item.checked = bool(updates["checked"])
            item.completed_at = _now_iso() if item.checked else None
        self._touch(ultimate_list)
        await self._commit()
        return item

    async def async_delete_item(self, list_id: str, item_id: str) -> None:
        """Delete an item."""
        ultimate_list = self.get_list(list_id)
        before = len(ultimate_list.items)
        ultimate_list.items = [item for item in ultimate_list.items if item.id != item_id]
        if len(ultimate_list.items) == before:
            raise HomeAssistantError(f"Unknown item_id {item_id}")
        self._normalize_sort_order(ultimate_list)
        self._touch(ultimate_list)
        await self._commit()

    async def async_check_item(self, list_id: str, item_id: str, checked: bool = True) -> UltimateListItem:
        """Mark an item complete or active."""
        item = await self.async_update_item(list_id, item_id, {"checked": checked})
        return item

    async def async_clear_checked(self, list_id: str) -> UltimateList:
        """Remove completed items from a list."""
        ultimate_list = self.get_list(list_id)
        ultimate_list.items = [item for item in ultimate_list.items if not item.checked]
        self._normalize_sort_order(ultimate_list)
        self._touch(ultimate_list)
        await self._commit()
        return ultimate_list

    async def async_create_section(
        self, list_id: str, title: str, *, section_type: str = "normal"
    ) -> UltimateListSection:
        """Create a section in a list."""
        if section_type not in SECTION_TYPES:
            raise HomeAssistantError(f"Unsupported section type: {section_type}")
        ultimate_list = self.get_list(list_id)
        section = make_section(title, section_type=section_type, sort_order=len(ultimate_list.sections))
        ultimate_list.sections.append(section)
        self._touch(ultimate_list)
        await self._commit()
        return section

    async def async_update_section(
        self, list_id: str, section_id: str, updates: dict[str, Any]
    ) -> UltimateListSection:
        """Update a section."""
        ultimate_list = self.get_list(list_id)
        section = self._get_section(ultimate_list, section_id)
        if "title" in updates and updates["title"] is not None:
            section.title = str(updates["title"])
        if "type" in updates and updates["type"] is not None:
            if updates["type"] not in SECTION_TYPES:
                raise HomeAssistantError(f"Unsupported section type: {updates['type']}")
            section.type = str(updates["type"])
        self._touch(ultimate_list)
        await self._commit()
        return section

    async def async_delete_section(self, list_id: str, section_id: str) -> None:
        """Delete a section and detach its items."""
        ultimate_list = self.get_list(list_id)
        before = len(ultimate_list.sections)
        ultimate_list.sections = [
            section for section in ultimate_list.sections if section.id != section_id
        ]
        if len(ultimate_list.sections) == before:
            raise HomeAssistantError(f"Unknown section_id {section_id}")
        for item in ultimate_list.items:
            if item.section_id == section_id:
                item.section_id = None
        self._touch(ultimate_list)
        await self._commit()

    async def async_duplicate_template(self, list_id: str, title: str | None = None) -> UltimateList:
        """Duplicate a template list into a live list."""
        source = self.get_list(list_id)
        if source.type not in {"template", "hybrid", "static", "dynamic"}:
            raise HomeAssistantError(f"Unsupported source list type: {source.type}")
        duplicate = await self.async_duplicate_list(list_id, title=title or f"{source.title} Active")
        if duplicate.type == "template":
            duplicate.type = "hybrid"
            self._touch(duplicate)
            await self._commit()
        return duplicate

    async def async_move_item(
        self, list_id: str, item_id: str, previous_item_id: str | None
    ) -> UltimateList:
        """Move an item after another item."""
        ultimate_list = self.get_list(list_id)
        item = self._get_item(ultimate_list, item_id)
        remaining = [existing for existing in ultimate_list.items if existing.id != item_id]

        if previous_item_id is None:
            remaining.insert(0, item)
        else:
            for index, existing in enumerate(remaining):
                if existing.id == previous_item_id:
                    remaining.insert(index + 1, item)
                    break
            else:
                raise HomeAssistantError(f"Unknown previous item id {previous_item_id}")

        ultimate_list.items = remaining
        self._normalize_sort_order(ultimate_list)
        self._touch(ultimate_list)
        await self._commit()
        return ultimate_list

    def _normalize_sort_order(self, ultimate_list: UltimateList) -> None:
        for index, item in enumerate(ultimate_list.items):
            item.sort_order = index

    def _get_item(self, ultimate_list: UltimateList, item_id: str) -> UltimateListItem:
        for item in ultimate_list.items:
            if item.id == item_id:
                return item
        raise HomeAssistantError(f"Unknown item_id {item_id}")

    def _get_section(self, ultimate_list: UltimateList, section_id: str) -> UltimateListSection:
        for section in ultimate_list.sections:
            if section.id == section_id:
                return section
        raise HomeAssistantError(f"Unknown section_id {section_id}")

    def serialize_list(self, ultimate_list: UltimateList) -> dict[str, Any]:
        """Serialize a list for the API layer."""
        payload = deepcopy(list_to_dict(ultimate_list))
        payload["items_for_display"] = [item_to_dict(item) for item in sort_items_for_display(ultimate_list)]
        payload["incomplete_count"] = ultimate_list.incomplete_count
        payload["entity_id"] = f"todo.{self.slugify(ultimate_list.title)}"
        return payload

    def serialize_all(self) -> dict[str, Any]:
        """Serialize all lists for the frontend."""
        lists = [self.serialize_list(ultimate_list) for ultimate_list in self.get_lists()]
        return {"lists": lists}

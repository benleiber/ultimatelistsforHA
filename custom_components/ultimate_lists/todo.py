"""Todo entities for Ultimate Lists."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .manager import UltimateListsManager
from .models import UltimateList


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up todo entities."""
    manager: UltimateListsManager = hass.data[DOMAIN]["manager"]
    known_ids: set[str] = set()

    def sync_entities() -> None:
        new_entities: list[UltimateListsTodoEntity] = []
        for ultimate_list in manager.get_lists():
            if ultimate_list.id in known_ids:
                continue
            known_ids.add(ultimate_list.id)
            new_entities.append(UltimateListsTodoEntity(manager, ultimate_list.id))
        if new_entities:
            async_add_entities(new_entities)

    sync_entities()
    manager.async_add_listener(sync_entities)


class UltimateListsTodoEntity(TodoListEntity):
    """Expose a stored list as a Home Assistant todo entity."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.MOVE_TODO_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, manager: UltimateListsManager, list_id: str) -> None:
        self._manager = manager
        self._list_id = list_id
        self._remove_listener: Callable[[], None] | None = None
        self._attr_has_entity_name = True
        self._attr_translation_key = "list"
        self._sync_from_store()

    def _sync_from_store(self) -> None:
        ultimate_list = self._manager.get_list(self._list_id)
        self._attr_unique_id = ultimate_list.id
        self._attr_name = ultimate_list.title
        self._attr_icon = ultimate_list.icon
        self._attr_todo_items = [
            TodoItem(
                uid=item.id,
                summary=item.text,
                status=TodoItemStatus.COMPLETE if item.checked else TodoItemStatus.NEEDS_ACTION,
                description=item.notes or None,
                completed=None,
            )
            for item in ultimate_list.items
        ]

    async def async_added_to_hass(self) -> None:
        """Start listening for list changes."""
        await super().async_added_to_hass()

        @callback
        def handle_update() -> None:
            try:
                self._sync_from_store()
            except Exception:
                return
            self.async_write_ha_state()

        self._remove_listener = self._manager.async_add_listener(handle_update)

    async def async_will_remove_from_hass(self) -> None:
        """Tear down listeners."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return the current list items."""
        self._sync_from_store()
        return self._attr_todo_items

    @property
    def should_poll(self) -> bool:
        """Use push updates."""
        return False

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a Home Assistant todo item."""
        await self._manager.async_add_item(
            self._list_id,
            item.summary or "",
            notes=item.description or "",
        )

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete multiple items."""
        for uid in uids:
            await self._manager.async_delete_item(self._list_id, uid)

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a todo item."""
        updates = {
            "text": item.summary,
            "notes": item.description or "",
            "checked": item.status == TodoItemStatus.COMPLETE,
        }
        await self._manager.async_update_item(self._list_id, item.uid, updates)

    async def async_move_todo_item(self, uid: str, previous_uid: str | None = None) -> None:
        """Move an item in the list."""
        await self._manager.async_move_item(self._list_id, uid, previous_uid)

    @property
    def available(self) -> bool:
        """Hide archived/deleted lists from normal use."""
        try:
            ultimate_list: UltimateList = self._manager.get_list(self._list_id)
        except Exception:
            return False
        return not ultimate_list.archived

"""Persistent storage helpers for Ultimate Lists."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DEFAULT_LIST_NAME, STORAGE_KEY, STORAGE_VERSION
from .models import UltimateList, list_from_dict, list_to_dict, make_list


class UltimateListsStore:
    """Wrapper around Home Assistant persistent storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.lists: dict[str, UltimateList] = {}

    async def async_load(self) -> None:
        """Load lists from disk."""
        raw = await self._store.async_load() or {}
        lists = raw.get("lists", [])
        self.lists = {entry["id"]: list_from_dict(entry) for entry in lists}

        if not self.lists:
            default_list = make_list(DEFAULT_LIST_NAME)
            self.lists[default_list.id] = default_list
            await self.async_save()

    async def async_save(self) -> None:
        """Save current lists to disk."""
        await self._store.async_save(
            {"lists": [list_to_dict(ultimate_list) for ultimate_list in self.lists.values()]}
        )

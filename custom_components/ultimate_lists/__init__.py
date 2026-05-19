"""Ultimate Lists integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import async_setup_api
from .const import (
    ATTR_ARCHIVED,
    ATTR_COLOR,
    ATTR_ICON,
    ATTR_IMPORTANT,
    ATTR_ITEM_ID,
    ATTR_LIST_ID,
    ATTR_LOCKED,
    ATTR_NOTES,
    ATTR_QUANTITY,
    ATTR_SECTION_ID,
    ATTR_SECTION_TITLE,
    ATTR_SECTION_TYPE,
    ATTR_SORT_MODE,
    ATTR_TAGS,
    ATTR_TEXT,
    ATTR_TITLE,
    ATTR_TYPE,
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_ITEM,
    SERVICE_ARCHIVE_LIST,
    SERVICE_CHECK_ITEM,
    SERVICE_CLEAR_CHECKED,
    SERVICE_CREATE_LIST,
    SERVICE_CREATE_SECTION,
    SERVICE_DELETE_ITEM,
    SERVICE_DELETE_LIST,
    SERVICE_DELETE_SECTION,
    SERVICE_DUPLICATE_LIST,
    SERVICE_DUPLICATE_TEMPLATE,
    SERVICE_MOVE_LIST,
    SERVICE_RENAME_LIST,
    SERVICE_SET_LIST_LOCK,
    SERVICE_UNCHECK_ITEM,
    SERVICE_UPDATE_ITEM,
    SERVICE_UPDATE_SECTION,
)
from .manager import UltimateListsManager
from .storage import UltimateListsStore

CREATE_LIST_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TITLE): cv.string,
        vol.Optional(ATTR_TYPE, default="dynamic"): cv.string,
        vol.Optional(ATTR_ICON, default="mdi:cart-outline"): cv.string,
        vol.Optional(ATTR_COLOR, default=""): cv.string,
        vol.Optional(ATTR_SORT_MODE, default="unchecked_first"): cv.string,
    }
)
LIST_ID_SCHEMA = vol.Schema({vol.Required(ATTR_LIST_ID): cv.string})
RENAME_LIST_SCHEMA = vol.Schema(
    {vol.Required(ATTR_LIST_ID): cv.string, vol.Required(ATTR_TITLE): cv.string}
)
ARCHIVE_LIST_SCHEMA = vol.Schema(
    {vol.Required(ATTR_LIST_ID): cv.string, vol.Optional(ATTR_ARCHIVED, default=True): cv.boolean}
)
DUPLICATE_LIST_SCHEMA = vol.Schema(
    {vol.Required(ATTR_LIST_ID): cv.string, vol.Optional(ATTR_TITLE): cv.string}
)
ADD_ITEM_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_LIST_ID): cv.string,
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_QUANTITY, default=""): cv.string,
        vol.Optional(ATTR_NOTES, default=""): cv.string,
        vol.Optional(ATTR_SECTION_ID): vol.Any(None, cv.string),
        vol.Optional(ATTR_IMPORTANT, default=False): cv.boolean,
        vol.Optional(ATTR_TAGS, default=[]): [cv.string],
    }
)
UPDATE_ITEM_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_LIST_ID): cv.string,
        vol.Required(ATTR_ITEM_ID): cv.string,
        vol.Optional(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_NOTES): cv.string,
        vol.Optional(ATTR_QUANTITY): cv.string,
        vol.Optional(ATTR_SECTION_ID): vol.Any(None, cv.string),
        vol.Optional(ATTR_IMPORTANT): cv.boolean,
        vol.Optional(ATTR_TAGS): [cv.string],
        vol.Optional("checked"): cv.boolean,
    }
)
DELETE_ITEM_SCHEMA = vol.Schema(
    {vol.Required(ATTR_LIST_ID): cv.string, vol.Required(ATTR_ITEM_ID): cv.string}
)
CHECK_ITEM_SCHEMA = DELETE_ITEM_SCHEMA
CLEAR_CHECKED_SCHEMA = LIST_ID_SCHEMA
CREATE_SECTION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_LIST_ID): cv.string,
        vol.Required(ATTR_SECTION_TITLE): cv.string,
        vol.Optional(ATTR_SECTION_TYPE, default="normal"): cv.string,
    }
)
UPDATE_SECTION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_LIST_ID): cv.string,
        vol.Required(ATTR_SECTION_ID): cv.string,
        vol.Optional(ATTR_TITLE): cv.string,
        vol.Optional(ATTR_TYPE): cv.string,
    }
)
DELETE_SECTION_SCHEMA = vol.Schema(
    {vol.Required(ATTR_LIST_ID): cv.string, vol.Required(ATTR_SECTION_ID): cv.string}
)
MOVE_LIST_SCHEMA = vol.Schema(
    {vol.Required(ATTR_LIST_ID): cv.string, vol.Required("direction"): vol.In(["up", "down"])}
)
SET_LIST_LOCK_SCHEMA = vol.Schema(
    {vol.Required(ATTR_LIST_ID): cv.string, vol.Required(ATTR_LOCKED): cv.boolean}
)


async def async_setup(hass: HomeAssistant, config: Mapping[str, Any]) -> bool:
    """Set up the integration domain."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ultimate Lists from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    store = UltimateListsStore(hass)
    manager = UltimateListsManager(store)
    await manager.async_initialize()
    hass.data[DOMAIN]["manager"] = manager

    await async_setup_api(hass)
    await _async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _get_manager(hass: HomeAssistant) -> UltimateListsManager:
    try:
        return hass.data[DOMAIN]["manager"]
    except KeyError as err:
        raise HomeAssistantError("Ultimate Lists is not loaded") from err


async def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_CREATE_LIST):
        return

    async def async_create_list(call: ServiceCall) -> None:
        await _get_manager(hass).async_create_list(
            call.data[ATTR_TITLE],
            list_type=call.data[ATTR_TYPE],
            icon=call.data[ATTR_ICON],
            color=call.data[ATTR_COLOR],
            sort_mode=call.data[ATTR_SORT_MODE],
        )

    async def async_rename_list(call: ServiceCall) -> None:
        await _get_manager(hass).async_rename_list(call.data[ATTR_LIST_ID], call.data[ATTR_TITLE])

    async def async_delete_list(call: ServiceCall) -> None:
        await _get_manager(hass).async_delete_list(call.data[ATTR_LIST_ID])

    async def async_archive_list(call: ServiceCall) -> None:
        await _get_manager(hass).async_archive_list(
            call.data[ATTR_LIST_ID], call.data[ATTR_ARCHIVED]
        )

    async def async_duplicate_list(call: ServiceCall) -> None:
        await _get_manager(hass).async_duplicate_list(
            call.data[ATTR_LIST_ID], title=call.data.get(ATTR_TITLE)
        )

    async def async_add_item(call: ServiceCall) -> None:
        await _get_manager(hass).async_add_item(
            call.data[ATTR_LIST_ID],
            call.data[ATTR_TEXT],
            quantity=call.data[ATTR_QUANTITY],
            notes=call.data[ATTR_NOTES],
            section_id=call.data.get(ATTR_SECTION_ID),
            important=call.data[ATTR_IMPORTANT],
            tags=call.data[ATTR_TAGS],
        )

    async def async_update_item(call: ServiceCall) -> None:
        await _get_manager(hass).async_update_item(
            call.data[ATTR_LIST_ID],
            call.data[ATTR_ITEM_ID],
            dict(call.data),
        )

    async def async_delete_item(call: ServiceCall) -> None:
        await _get_manager(hass).async_delete_item(call.data[ATTR_LIST_ID], call.data[ATTR_ITEM_ID])

    async def async_check_item(call: ServiceCall) -> None:
        await _get_manager(hass).async_check_item(call.data[ATTR_LIST_ID], call.data[ATTR_ITEM_ID], True)

    async def async_uncheck_item(call: ServiceCall) -> None:
        await _get_manager(hass).async_check_item(
            call.data[ATTR_LIST_ID], call.data[ATTR_ITEM_ID], False
        )

    async def async_clear_checked(call: ServiceCall) -> None:
        await _get_manager(hass).async_clear_checked(call.data[ATTR_LIST_ID])

    async def async_create_section(call: ServiceCall) -> None:
        await _get_manager(hass).async_create_section(
            call.data[ATTR_LIST_ID],
            call.data[ATTR_SECTION_TITLE],
            section_type=call.data[ATTR_SECTION_TYPE],
        )

    async def async_update_section(call: ServiceCall) -> None:
        updates = {}
        if ATTR_TITLE in call.data:
            updates["title"] = call.data[ATTR_TITLE]
        if ATTR_TYPE in call.data:
            updates["type"] = call.data[ATTR_TYPE]
        await _get_manager(hass).async_update_section(
            call.data[ATTR_LIST_ID], call.data[ATTR_SECTION_ID], updates
        )

    async def async_delete_section(call: ServiceCall) -> None:
        await _get_manager(hass).async_delete_section(
            call.data[ATTR_LIST_ID], call.data[ATTR_SECTION_ID]
        )

    async def async_duplicate_template(call: ServiceCall) -> None:
        await _get_manager(hass).async_duplicate_template(
            call.data[ATTR_LIST_ID], title=call.data.get(ATTR_TITLE)
        )

    async def async_move_list(call: ServiceCall) -> None:
        await _get_manager(hass).async_move_list(call.data[ATTR_LIST_ID], call.data["direction"])

    async def async_set_list_lock(call: ServiceCall) -> None:
        await _get_manager(hass).async_set_list_lock(
            call.data[ATTR_LIST_ID], call.data[ATTR_LOCKED]
        )

    hass.services.async_register(DOMAIN, SERVICE_CREATE_LIST, async_create_list, schema=CREATE_LIST_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_RENAME_LIST, async_rename_list, schema=RENAME_LIST_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_LIST, async_delete_list, schema=LIST_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ARCHIVE_LIST, async_archive_list, schema=ARCHIVE_LIST_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_DUPLICATE_LIST, async_duplicate_list, schema=DUPLICATE_LIST_SCHEMA
    )
    hass.services.async_register(DOMAIN, SERVICE_ADD_ITEM, async_add_item, schema=ADD_ITEM_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_ITEM, async_update_item, schema=UPDATE_ITEM_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_ITEM, async_delete_item, schema=DELETE_ITEM_SCHEMA
    )
    hass.services.async_register(DOMAIN, SERVICE_CHECK_ITEM, async_check_item, schema=CHECK_ITEM_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_UNCHECK_ITEM, async_uncheck_item, schema=CHECK_ITEM_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLEAR_CHECKED, async_clear_checked, schema=CLEAR_CHECKED_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CREATE_SECTION, async_create_section, schema=CREATE_SECTION_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_SECTION, async_update_section, schema=UPDATE_SECTION_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_SECTION, async_delete_section, schema=DELETE_SECTION_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DUPLICATE_TEMPLATE,
        async_duplicate_template,
        schema=DUPLICATE_LIST_SCHEMA,
    )
    hass.services.async_register(DOMAIN, SERVICE_MOVE_LIST, async_move_list, schema=MOVE_LIST_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_SET_LIST_LOCK, async_set_list_lock, schema=SET_LIST_LOCK_SCHEMA
    )

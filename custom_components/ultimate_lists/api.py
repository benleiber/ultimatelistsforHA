"""HTTP API and static asset registration for Ultimate Lists."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import API_ACTION_PATH, API_LISTS_PATH, CARD_STATIC_URL, DOMAIN
from .manager import UltimateListsManager


def get_manager(hass: HomeAssistant) -> UltimateListsManager:
    """Return the active runtime manager."""
    return hass.data[DOMAIN]["manager"]


async def async_setup_api(hass: HomeAssistant) -> None:
    """Register API views and frontend assets once."""
    if hass.data[DOMAIN].get("api_registered"):
        return

    frontend_path = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_STATIC_URL, str(frontend_path), False)]
    )
    hass.http.register_view(UltimateListsView(hass))
    hass.http.register_view(UltimateListsActionView(hass))
    hass.data[DOMAIN]["api_registered"] = True


class UltimateListsView(HomeAssistantView):
    """Serve serialized list state to the custom card."""

    url = API_LISTS_PATH
    name = "api:ultimate_lists:lists"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        manager = get_manager(self.hass)
        return web.json_response(manager.serialize_all())


class UltimateListsActionView(HomeAssistantView):
    """Handle action requests from the custom card."""

    url = API_ACTION_PATH
    name = "api:ultimate_lists:action"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        manager = get_manager(self.hass)
        payload = await request.json()
        action = payload.get("action")
        data: dict[str, Any] = payload.get("data", {})

        try:
            if action == "create_list":
                await manager.async_create_list(
                    data["title"],
                    list_type=data.get("type", "dynamic"),
                    icon=data.get("icon", "mdi:cart-outline"),
                    color=data.get("color", ""),
                    sort_mode=data.get("sort_mode", "unchecked_first"),
                )
            elif action == "rename_list":
                await manager.async_rename_list(data["list_id"], data["title"])
            elif action == "delete_list":
                await manager.async_delete_list(data["list_id"])
            elif action == "archive_list":
                await manager.async_archive_list(data["list_id"], data.get("archived", True))
            elif action == "duplicate_list":
                await manager.async_duplicate_list(data["list_id"], title=data.get("title"))
            elif action == "add_item":
                await manager.async_add_item(
                    data["list_id"],
                    data["text"],
                    quantity=data.get("quantity", ""),
                    notes=data.get("notes", ""),
                    section_id=data.get("section_id"),
                    important=data.get("important", False),
                    tags=data.get("tags", []),
                )
            elif action == "update_item":
                await manager.async_update_item(data["list_id"], data["item_id"], data["updates"])
            elif action == "delete_item":
                await manager.async_delete_item(data["list_id"], data["item_id"])
            elif action == "check_item":
                await manager.async_check_item(data["list_id"], data["item_id"], True)
            elif action == "uncheck_item":
                await manager.async_check_item(data["list_id"], data["item_id"], False)
            elif action == "clear_checked":
                await manager.async_clear_checked(data["list_id"])
            elif action == "create_section":
                await manager.async_create_section(
                    data["list_id"],
                    data["title"],
                    section_type=data.get("type", "normal"),
                )
            elif action == "update_section":
                await manager.async_update_section(
                    data["list_id"], data["section_id"], data["updates"]
                )
            elif action == "delete_section":
                await manager.async_delete_section(data["list_id"], data["section_id"])
            elif action == "duplicate_template":
                await manager.async_duplicate_template(data["list_id"], title=data.get("title"))
            else:
                return web.json_response({"error": f"Unsupported action: {action}"}, status=400)
        except HomeAssistantError as err:
            return web.json_response({"error": str(err)}, status=400)

        return web.json_response(manager.serialize_all())

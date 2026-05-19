"""Config flow for Ultimate Lists."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class UltimateListsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Single-instance config flow for the integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Set up the single integration entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="Ultimate Lists", data={})

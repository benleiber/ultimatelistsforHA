"""Constants for Ultimate Lists."""

from __future__ import annotations

try:
    from homeassistant.const import Platform
except ImportError:  # pragma: no cover - fallback for local model tests
    from enum import StrEnum

    class Platform(StrEnum):
        """Local fallback for test environments without Home Assistant."""

        TODO = "todo"

DOMAIN = "ultimate_lists"
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

PLATFORMS: list[Platform] = [Platform.TODO]

DEFAULT_LIST_NAME = "Grocery"
DEFAULT_LIST_TYPE = "dynamic"
DEFAULT_SORT_MODE = "unchecked_first"

LIST_TYPES = {"dynamic", "static", "template", "hybrid"}
SORT_MODES = {"manual", "unchecked_first", "sectioned", "priority"}
SECTION_TYPES = {"normal", "quadrant", "top_items", "room", "category"}

ATTR_LIST_ID = "list_id"
ATTR_TITLE = "title"
ATTR_TYPE = "type"
ATTR_ICON = "icon"
ATTR_COLOR = "color"
ATTR_SORT_MODE = "sort_mode"
ATTR_ARCHIVED = "archived"

ATTR_ITEM_ID = "item_id"
ATTR_TEXT = "text"
ATTR_CHECKED = "checked"
ATTR_IMPORTANT = "important"
ATTR_SECTION_ID = "section_id"
ATTR_NOTES = "notes"
ATTR_QUANTITY = "quantity"
ATTR_TAGS = "tags"

ATTR_SECTION_TITLE = "section_title"
ATTR_SECTION_TYPE = "section_type"

SERVICE_CREATE_LIST = "create_list"
SERVICE_RENAME_LIST = "rename_list"
SERVICE_DELETE_LIST = "delete_list"
SERVICE_ARCHIVE_LIST = "archive_list"
SERVICE_DUPLICATE_LIST = "duplicate_list"
SERVICE_ADD_ITEM = "add_item"
SERVICE_UPDATE_ITEM = "update_item"
SERVICE_DELETE_ITEM = "delete_item"
SERVICE_CHECK_ITEM = "check_item"
SERVICE_UNCHECK_ITEM = "uncheck_item"
SERVICE_CLEAR_CHECKED = "clear_checked"
SERVICE_CREATE_SECTION = "create_section"
SERVICE_UPDATE_SECTION = "update_section"
SERVICE_DELETE_SECTION = "delete_section"
SERVICE_DUPLICATE_TEMPLATE = "duplicate_template"

CARD_STATIC_URL = "/ultimate_lists"
CARD_RESOURCE_NAME = "ultimate-lists-card.js"
API_LISTS_PATH = "/api/ultimate_lists/lists"
API_ACTION_PATH = "/api/ultimate_lists/action"

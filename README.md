# Ultimate Lists for Home Assistant

`ultimate_lists` is a Home Assistant custom integration for household lists that need to work equally well as a quick grocery checklist and as a long-lived reference list.

## MVP features

- Persistent list storage with Home Assistant `Store`
- One Home Assistant `todo` entity per active list
- Create, rename, duplicate, archive, and delete lists
- Add, update, complete, reactivate, and delete items
- Completed items can fall to the bottom in grocery/focus mode
- Custom Lovelace card with compact and focus layouts
- Mobile-friendly focus experience with large tap targets

## Planned next layers

- Static emergency lists with room/quadrant sections
- Top-priority sections
- Template lists
- Better section editing in the card
- Richer item metadata editing

## Installation

1. Copy `custom_components/ultimate_lists` into your Home Assistant config directory.
2. Restart Home Assistant.
3. Add the integration from Settings -> Devices & Services -> Add Integration.
4. Add the custom card resource:

```yaml
url: /ultimate_lists/ultimate-lists-card.js
type: module
```

5. Add the card to a dashboard:

```yaml
type: custom:ultimate-lists-card
entity: todo.grocery
title: Grocery
```

You can also omit `entity` and the card will render the first available Ultimate Lists entity.

## Services

The integration registers these services:

- `ultimate_lists.create_list`
- `ultimate_lists.rename_list`
- `ultimate_lists.delete_list`
- `ultimate_lists.archive_list`
- `ultimate_lists.duplicate_list`
- `ultimate_lists.add_item`
- `ultimate_lists.update_item`
- `ultimate_lists.delete_item`
- `ultimate_lists.check_item`
- `ultimate_lists.uncheck_item`
- `ultimate_lists.clear_checked`
- `ultimate_lists.create_section`
- `ultimate_lists.update_section`
- `ultimate_lists.delete_section`
- `ultimate_lists.duplicate_template`

## Notes

- The current MVP card uses built-in browser prompts for a few edit actions to keep the first version simple and dependable.
- Focus mode is implemented inside the card as a full-screen overlay instead of a separate Home Assistant panel.
- Section editing is supported in the backend model and services, but the frontend only exposes basic rendering in this first pass.

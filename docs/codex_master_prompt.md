# Ultimate Lists for Home Assistant: Long-Run Codex Prompt

Build a production-quality Home Assistant custom integration and frontend called `ultimate_lists`.

This is a long autonomous implementation run. Do not stop at scaffolding. Continue through backend, frontend, tests, documentation, and MVP polish as far as time allows.

## Mission

Create the best family-friendly lists app for Home Assistant.

It must support:
- Dynamic lists like grocery, packing, errands, and project checklists
- Static reference lists like emergency/fire lists
- Hybrid and template-based lists
- A focused mobile-friendly mode for actively working through a list in the real world

The product should feel like:
- the speed and immediacy of sticky notes
- the usefulness of a grocery checklist
- the structure of a preparedness reference list
- a natural Home Assistant dashboard feature

This should not feel like a generic CRUD demo.

## Important run instructions

- Work in the current repository and build the actual code
- Keep going until there is a meaningful working MVP, not just generated files
- Favor Home Assistant conventions and maintainability over shortcuts
- Make reasonable architectural decisions without pausing unless there is a high-risk ambiguity
- Document assumptions and deferred items
- Add tests and a solid README
- If the frontend needs a practical compromise for MVP, choose the simplest good Home Assistant-friendly path and continue

## Primary users

- A household using Home Assistant dashboards on phones and tablets
- A user working through a grocery list in a store
- A family maintaining important static checklists like fire/emergency lists

## Core goals

- Dynamic lists with checkboxes and fast editing
- Static lists for long-term reference and preparedness
- A focused mobile-friendly mode for working through a list
- Dashboard access in Home Assistant
- Strong backend architecture for future expansion

## Architecture

- Backend: Home Assistant custom integration
- Frontend: custom Lovelace card
- Storage: Home Assistant persistent storage using `Store`
- Entity model: one `todo` entity per active list
- Domain: `ultimate_lists`
- Root package: `custom_components/ultimate_lists`

## Functional requirements

### 1. List types

Support:
- `dynamic`
- `static`
- `template`
- `hybrid`

Examples:
- grocery list
- packing list
- errands
- project checklist
- fire evacuation list
- top 10 grab items
- room or quadrant emergency list

### 2. Item behavior

Each item should support:
- checkbox state
- text label
- optional quantity
- optional notes
- optional tags
- optional importance flag
- optional section assignment
- manual ordering
- created timestamp
- completed timestamp

Dynamic behavior:
- checking marks an item complete
- completed items show strikethrough
- completed items move to the bottom in grocery/focus mode
- completed items can be unchecked to reactivate them
- completed items can optionally be hidden

### 3. Static and sectioned lists

Support:
- top-priority item sections
- quadrants/rooms like bedroom, office, garage, kitchen, yard
- pinned important items
- long-lived static lists that do not behave like disposable shopping lists by default

### 4. List actions

Support:
- create
- rename
- duplicate
- archive
- delete
- clear checked
- optional icon/color metadata
- optional sort mode selection

### 5. Item actions

Support:
- add
- edit
- delete
- duplicate
- check
- uncheck
- move section
- reorder

### 6. Focus mode

This is a key product feature.

Focus mode should:
- open a single list in a larger mobile-friendly layout
- prioritize fast checking/unchecking
- keep incomplete items at the top
- move completed items to the bottom
- visibly strike through completed items
- allow quick inline item entry
- feel good to use while shopping

### 7. Dashboard mode

The Lovelace card should support:
- list title
- incomplete count
- compact preview
- quick add
- quick check/uncheck
- open focus mode
- list overflow menu

### 8. Overflow menus

List overflow menu:
- rename
- duplicate
- clear checked
- archive
- delete

Item overflow menu:
- edit
- duplicate
- move section
- delete

## Data model

Design around a model like:

List:
- `id`
- `title`
- `type` = `dynamic | static | template | hybrid`
- `icon`
- `color`
- `sort_mode` = `manual | unchecked_first | sectioned | priority`
- `archived`
- `sections`
- `items`
- `created_at`
- `updated_at`

Item:
- `id`
- `text`
- `checked`
- `important`
- `section_id`
- `notes`
- `quantity`
- `tags`
- `sort_order`
- `created_at`
- `completed_at`

Section:
- `id`
- `title`
- `type` = `normal | quadrant | top_items | room | category`
- `sort_order`

Keep the MVP model simple, but make it easy to extend.

## Backend requirements

Implement:
- integration scaffold
- config flow
- storage manager
- runtime manager/coordinator equivalent
- `todo.py`
- services
- translations
- API or view support for the frontend if useful
- tests

Services to implement:
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

Each service should:
- validate inputs
- update storage safely
- trigger entity/frontend refresh behavior
- follow Home Assistant patterns

Todo integration:
- one `todo` entity per active list
- entity state is incomplete count
- implement create/update/delete/move support where appropriate
- map stored items to HA `TodoItem`

## Frontend requirements

Create a custom Lovelace card named `ultimate-lists-card`.

Support:
- dashboard card mode
- focus mode
- inline item creation
- checkbox interactions
- checked items sorted to bottom with strikethrough
- optional hide/show completed
- responsive mobile-friendly design
- list deletion from a list menu

If a separate dialog or overlay is the best MVP path, use it.

## MVP priorities

Build a working MVP first:
- persistent storage
- create at least one list
- add item
- check item
- uncheck item
- delete item
- delete list
- todo entity support
- Lovelace card rendering a list
- focus mode

This grocery-style interaction pattern is the highest priority.

## Suggested implementation phases

### Phase 1
- Scaffold integration
- Config flow
- Models and storage
- Core list/item services

### Phase 2
- Todo entity support
- Runtime update propagation

### Phase 3
- Lovelace card MVP
- Quick add
- Check/uncheck
- Delete item
- Focus mode

### Phase 4
- Sections
- Static/emergency list rendering
- Top 10 and room/quadrant structures

### Phase 5
- Templates and duplication

### Phase 6
- Tests
- Docs
- Polish

## Testing requirements

Add meaningful tests for:
- storage/model behavior
- list/item CRUD
- check/uncheck behavior
- clear checked behavior
- duplication behavior
- todo state behavior when practical

If frontend tests are too heavy for MVP, keep the frontend simple and well-structured.

## Documentation requirements

Create a README with:
- feature overview
- installation steps
- Lovelace resource setup
- basic card usage
- available services
- roadmap / future ideas
- assumptions and known limitations

## Acceptance criteria

The run is successful when:
- Home Assistant can load the integration structure cleanly
- a user can create a grocery list
- a user can add items
- a user can check and uncheck items
- checked items move to the bottom in focus/grocery mode
- checked items show strikethrough
- a user can delete a list from the UI
- the list is accessible from a dashboard
- the codebase is clean and ready for later features

## Tradeoff guidance

- Prioritize a working grocery-list MVP over advanced future features
- Prefer robust basic interactions over drag-and-drop complexity
- Prioritize maintainability
- Keep building as long as meaningful progress is possible

## Deliverables

Produce:
- complete custom integration scaffold
- backend implementation
- frontend card implementation
- tests
- README
- any required build/config files
- concise notes on completed vs deferred functionality

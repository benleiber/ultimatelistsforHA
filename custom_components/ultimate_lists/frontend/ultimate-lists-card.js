class UltimateListsCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("ultimate-lists-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "title", selector: { text: {} } },
        { name: "entity", selector: { entity: { domain: "todo" } } },
        { name: "show_completed", selector: { boolean: {} } },
      ],
    };
  }

  setConfig(config) {
    this._config = {
      show_completed: true,
      ...config,
    };
    if (!this._root) {
      this._root = this.attachShadow({ mode: "open" });
    }
    this._render();
  }

  set hass(hass) {
    const previousStates = this._hass?.states;
    this._hass = hass;
    const trackedEntity = this._config?.entity;
    const prevState = trackedEntity ? previousStates?.[trackedEntity]?.state : undefined;
    const nextState = trackedEntity ? hass?.states?.[trackedEntity]?.state : undefined;

    if (!this._data) {
      this._loadData();
      return;
    }

    if (trackedEntity && prevState !== nextState) {
      this._loadData(true);
    }
  }

  async _loadData(force = false) {
    if (!this._hass || (this._loading && !force)) {
      return;
    }
    this._loading = true;
    try {
      const payload = await this._hass.callApi("GET", "ultimate_lists/lists");
      this._data = payload;
      this._error = "";
      this._syncSelection();
      this._render();
    } catch (err) {
      this._error = this._formatError(err);
      this._render();
    } finally {
      this._loading = false;
    }
  }

  _getLists() {
    return this._data?.lists || [];
  }

  _syncSelection() {
    const lists = this._getLists();
    if (!lists.length) {
      this._selectedListId = null;
      return;
    }
    if (this._selectedListId && lists.some((list) => list.id === this._selectedListId)) {
      return;
    }
    if (this._config?.entity) {
      const matching = lists.find((list) => list.entity_id === this._config.entity);
      if (matching) {
        this._selectedListId = matching.id;
        return;
      }
    }
    this._selectedListId = lists[0].id;
  }

  _pickList() {
    const lists = this._getLists();
    if (!lists.length) {
      return null;
    }
    return lists.find((list) => list.id === this._selectedListId) || lists[0];
  }

  async _postAction(action, data) {
    try {
      this._data = await this._hass.callApi("POST", "ultimate_lists/action", { action, data });
      this._error = "";
      this._syncSelection();
      this._render();
      return true;
    } catch (err) {
      this._error = this._formatError(err);
      this._render();
      return false;
    }
  }

  _escape(text) {
    return String(text ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  _formatError(err) {
    if (!err) {
      return "Unknown error";
    }
    if (typeof err === "string") {
      return err;
    }
    if (err.message) {
      return err.message;
    }
    if (err.body?.message) {
      return err.body.message;
    }
    if (err.error) {
      return err.error;
    }
    try {
      return JSON.stringify(err);
    } catch (_jsonErr) {
      return String(err);
    }
  }

  _renderSidebar(list, index, total) {
    return `
      <div class="sidebar-row ${this._selectedListId === list.id ? "selected" : ""}">
        <button class="sidebar-main" data-action="select-list" data-list-id="${list.id}" type="button">
          <span class="sidebar-title">${this._escape(list.title)}</span>
          <span class="sidebar-meta">${list.incomplete_count} active${list.locked ? " • locked" : ""}</span>
        </button>
        <div class="sidebar-tools">
          <button class="mini-button" data-action="move-list-up" data-list-id="${list.id}" type="button" ${index === 0 ? "disabled" : ""}>↑</button>
          <button class="mini-button" data-action="move-list-down" data-list-id="${list.id}" type="button" ${index === total - 1 ? "disabled" : ""}>↓</button>
        </div>
      </div>
    `;
  }

  _renderListMenu(list) {
    if (this._menuListId !== list.id) {
      return "";
    }
    return `
      <div class="menu-pop">
        <button class="menu-item" data-action="toggle-create-list" type="button">New List</button>
        <button class="menu-item" data-action="rename-list" data-list-id="${list.id}" type="button">Rename</button>
        <button class="menu-item ${list.locked ? "disabled" : "danger"}" data-action="delete-list" data-list-id="${list.id}" type="button" ${list.locked ? "disabled" : ""}>Delete</button>
      </div>
    `;
  }

  _renderItems(list, focusMode) {
    const showCompleted = this._config.show_completed ?? true;
    const items = (list?.items_for_display || []).filter(
      (item) => showCompleted || !item.checked,
    );

    if (!items.length) {
      return `<div class="empty">No items yet.</div>`;
    }

    return items
      .map(
        (item) => `
          <div class="item-row ${item.checked ? "checked" : ""} ${focusMode ? "focus" : ""}">
            <button class="toggle-hit" data-action="toggle-item" data-list-id="${list.id}" data-item-id="${item.id}" data-checked="${item.checked}" type="button">
              <span class="checkbox">${item.checked ? "&#10003;" : ""}</span>
            </button>
            <span class="item-copy" data-action="toggle-item" data-list-id="${list.id}" data-item-id="${item.id}" data-checked="${item.checked}">
              <span class="item-text">${this._escape(item.text)}</span>
              ${item.quantity ? `<span class="meta">${this._escape(item.quantity)}</span>` : ""}
              ${item.notes ? `<span class="meta">${this._escape(item.notes)}</span>` : ""}
            </span>
            <span class="item-actions">
              <button class="icon-button subtle-button" data-action="edit-item" data-list-id="${list.id}" data-item-id="${item.id}" type="button">Edit</button>
              <button class="icon-button subtle-button danger" data-action="delete-item" data-list-id="${list.id}" data-item-id="${item.id}" type="button">Delete</button>
            </span>
          </div>
        `,
      )
      .join("");
  }

  _renderFocusOverlay(list) {
    if (!this._focusOpen) {
      return "";
    }
    return `
      <div class="overlay" data-action="close-focus">
        <div class="focus-shell">
          <div class="focus-header">
            <div>
              <div class="eyebrow">Focus Mode</div>
              <h2>${this._escape(list.title)}</h2>
              <div class="subtle">${list.incomplete_count} active items</div>
            </div>
            <button class="icon-button subtle-button" data-action="close-focus" type="button">Close</button>
          </div>
          <form class="quick-add large" data-action="submit-item" data-list-id="${list.id}">
            <input name="text" type="text" placeholder="Add item..." />
            <button type="submit">Add</button>
          </form>
          <div class="items focus-list">
            ${this._renderItems(list, true)}
          </div>
        </div>
      </div>
    `;
  }

  _render() {
    if (!this._root || !this._config) {
      return;
    }

    this._syncSelection();
    const lists = this._getLists();
    const activeList = this._pickList();
    const headerTitle = this._config.title || "Ultimate Lists";

    this._root.innerHTML = `
      <style>
        :host {
          display: block;
          --ul-border: rgba(120, 132, 160, 0.22);
          --ul-bg: linear-gradient(180deg, rgba(250,251,253,0.98), rgba(242,245,249,0.98));
          --ul-panel: rgba(255,255,255,0.92);
          --ul-rail: rgba(244, 247, 251, 0.95);
          --ul-text: #18212f;
          --ul-subtle: #637087;
          --ul-accent: #2d6cdf;
          --ul-danger: #b84040;
          --ul-shadow: 0 16px 34px rgba(19, 31, 53, 0.12);
        }
        ha-card {
          background: var(--ul-bg);
          color: var(--ul-text);
          border: 1px solid var(--ul-border);
          box-shadow: var(--ul-shadow);
          border-radius: 22px;
          overflow: hidden;
        }
        .shell {
          display: grid;
          grid-template-columns: minmax(170px, 220px) minmax(0, 1fr);
          min-height: 440px;
        }
        .sidebar {
          background: var(--ul-rail);
          border-right: 1px solid var(--ul-border);
          padding: 16px;
          display: grid;
          gap: 12px;
          align-content: start;
        }
        .content {
          padding: 18px;
          min-width: 0;
        }
        .eyebrow {
          text-transform: uppercase;
          letter-spacing: 0.08em;
          font-size: 0.7rem;
          font-weight: 700;
          color: var(--ul-subtle);
        }
        .sidebar-head {
          display: grid;
          gap: 4px;
          padding-bottom: 4px;
        }
        .sidebar-list {
          display: grid;
          gap: 10px;
        }
        .sidebar-row {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 8px;
          align-items: stretch;
        }
        .sidebar-main {
          border: 1px solid var(--ul-border);
          background: rgba(255,255,255,0.9);
          border-radius: 16px;
          padding: 12px;
          text-align: left;
          cursor: pointer;
          display: grid;
          gap: 4px;
        }
        .sidebar-row.selected .sidebar-main {
          border-color: rgba(45,108,223,0.34);
          box-shadow: inset 0 0 0 1px rgba(45,108,223,0.15);
          background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(236,243,255,0.98));
        }
        .sidebar-title {
          font-weight: 700;
          color: var(--ul-text);
        }
        .sidebar-meta {
          font-size: 0.82rem;
          color: var(--ul-subtle);
        }
        .sidebar-tools {
          display: grid;
          gap: 6px;
        }
        .mini-button,
        .icon-button,
        .menu-item,
        .toggle-hit,
        .sidebar-main,
        .quick-add button {
          font: inherit;
        }
        .mini-button,
        .icon-button,
        .menu-item {
          border: 0;
          border-radius: 12px;
          cursor: pointer;
        }
        .mini-button {
          width: 34px;
          height: 34px;
          background: rgba(33, 48, 74, 0.08);
          color: var(--ul-text);
        }
        .mini-button:disabled,
        .menu-item:disabled {
          opacity: 0.45;
          cursor: default;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 14px;
        }
        .header h1, .list-header h2 {
          margin: 0;
        }
        .subtle, .meta {
          color: var(--ul-subtle);
        }
        .toolbar {
          display: flex;
          gap: 8px;
          align-items: center;
          position: relative;
          flex-wrap: wrap;
          justify-content: flex-end;
        }
        .icon-button {
          background: rgba(33, 48, 74, 0.08);
          color: var(--ul-text);
          padding: 10px 14px;
        }
        .subtle-button {
          background: rgba(33, 48, 74, 0.08);
        }
        .icon-button.danger,
        .menu-item.danger {
          color: var(--ul-danger);
        }
        .list-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 14px;
          position: relative;
          flex-wrap: wrap;
        }
        .list-header-copy {
          display: grid;
          gap: 4px;
          min-width: 0;
        }
        .menu-pop {
          position: absolute;
          top: calc(100% + 8px);
          right: 0;
          background: rgba(255,255,255,0.98);
          border: 1px solid var(--ul-border);
          border-radius: 16px;
          box-shadow: var(--ul-shadow);
          display: grid;
          gap: 4px;
          padding: 8px;
          min-width: 150px;
          z-index: 10;
        }
        .menu-item {
          background: transparent;
          padding: 10px 12px;
          text-align: left;
        }
        .quick-add {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 10px;
          margin-bottom: 14px;
          align-items: stretch;
        }
        .quick-add.large {
          margin-bottom: 18px;
        }
        input {
          width: 100%;
          box-sizing: border-box;
          border: 1px solid var(--ul-border);
          border-radius: 14px;
          padding: 12px 14px;
          background: rgba(255,255,255,0.86);
          color: var(--ul-text);
          font: inherit;
        }
        .quick-add button {
          border: 0;
          border-radius: 14px;
          padding: 10px 14px;
          cursor: pointer;
          background: var(--ul-accent);
          color: white;
          font-weight: 700;
        }
        .items {
          display: grid;
          gap: 10px;
        }
        .item-row {
          width: 100%;
          border: 1px solid var(--ul-border);
          background: var(--ul-panel);
          border-radius: 16px;
          padding: 12px;
          display: grid;
          grid-template-columns: 28px 1fr auto;
          align-items: center;
          gap: 12px;
          text-align: left;
        }
        .item-row.focus {
          min-height: 64px;
          padding: 14px;
        }
        .toggle-hit {
          border: 0;
          background: transparent;
          padding: 0;
          margin: 0;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }
        .checkbox {
          width: 22px;
          height: 22px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          border: 2px solid var(--ul-accent);
          color: var(--ul-accent);
          font-weight: 800;
        }
        .checked .item-text {
          text-decoration: line-through;
          color: var(--ul-subtle);
        }
        .item-copy {
          display: grid;
          gap: 3px;
          cursor: pointer;
          min-width: 0;
        }
        .item-text {
          font-weight: 600;
          overflow-wrap: anywhere;
        }
        .item-actions {
          display: flex;
          gap: 8px;
          align-items: center;
        }
        .empty {
          padding: 12px 0;
          color: var(--ul-subtle);
        }
        .overlay {
          position: fixed;
          inset: 0;
          background: rgba(8, 14, 24, 0.58);
          display: flex;
          align-items: stretch;
          justify-content: center;
          z-index: 9999;
        }
        .focus-shell {
          width: min(760px, 100vw);
          min-height: 100vh;
          background: linear-gradient(180deg, #fbfcfe 0%, #edf2f8 100%);
          color: var(--ul-text);
          padding: 20px;
          box-sizing: border-box;
          overflow: auto;
        }
        .focus-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 18px;
        }
        .focus-header h2 {
          margin: 4px 0;
          font-size: 1.4rem;
        }
        @media (max-width: 840px) {
          .shell {
            grid-template-columns: 1fr;
          }
          .sidebar {
            border-right: 0;
            border-bottom: 1px solid var(--ul-border);
          }
        }
        @media (max-width: 720px) {
          .list-header {
            flex-direction: column;
            align-items: stretch;
          }
          .toolbar {
            justify-content: flex-start;
          }
          .quick-add {
            grid-template-columns: 1fr;
          }
          .quick-add button {
            width: 100%;
          }
        }
        @media (max-width: 640px) {
          .item-row {
            grid-template-columns: 28px 1fr;
          }
          .item-actions {
            grid-column: 1 / -1;
            justify-content: flex-end;
          }
        }
      </style>
      <ha-card>
        <div class="shell">
          <div class="sidebar">
            <div class="sidebar-head">
              <div class="eyebrow">Ultimate Lists</div>
              <div class="subtle">${this._escape(headerTitle)}</div>
            </div>
            ${this._error ? `<div class="empty">${this._escape(this._error)}</div>` : ""}
            ${this._creatingList ? `
              <form class="quick-add" data-action="submit-list">
                <input name="title" type="text" placeholder="New list name..." />
                <button type="submit">Create</button>
              </form>
            ` : ""}
            <div class="sidebar-list">
              ${lists.map((list, index) => this._renderSidebar(list, index, lists.length)).join("")}
            </div>
          </div>
          <div class="content">
            ${activeList ? `
              <div class="list-header">
                <div class="list-header-copy">
                  <div class="eyebrow">${this._escape(activeList.type)}</div>
                  <h2>${this._escape(activeList.title)}</h2>
                  <div class="subtle">${activeList.incomplete_count} active items${activeList.locked ? " • locked against deletion" : ""}</div>
                </div>
                <div class="toolbar">
                  <button class="icon-button subtle-button" data-action="toggle-lock" data-list-id="${activeList.id}" data-locked="${activeList.locked}" type="button">${activeList.locked ? "Unlock" : "Lock"}</button>
                  <button class="icon-button subtle-button" data-action="focus" type="button">Focus</button>
                  <button class="icon-button subtle-button" data-action="toggle-menu" data-list-id="${activeList.id}" type="button">⋯</button>
                  ${this._renderListMenu(activeList)}
                </div>
              </div>
              <form class="quick-add" data-action="submit-item" data-list-id="${activeList.id}">
                <input name="text" type="text" placeholder="Add item..." />
                <button type="submit">Add</button>
              </form>
              <div class="items">${this._renderItems(activeList, false)}</div>
            ` : `<div class="empty">Create your first list to get started.</div>`}
          </div>
        </div>
      </ha-card>
      ${activeList ? this._renderFocusOverlay(activeList) : ""}
    `;

    this._root.querySelector(".focus-shell")?.addEventListener("click", (ev) => ev.stopPropagation());
    this._root.querySelectorAll("[data-action]").forEach((node) => {
      node.addEventListener("click", (ev) => this._handleClick(ev));
    });
    this._root.querySelectorAll('form[data-action="submit-item"], form[data-action="submit-list"]').forEach((form) => {
      form.addEventListener("submit", (ev) => this._handleSubmit(ev));
    });
  }

  async _handleSubmit(ev) {
    ev.preventDefault();
    const form = ev.currentTarget;
    if (form.dataset.action === "submit-list") {
      const input = form.querySelector('input[name="title"]');
      const title = input?.value?.trim();
      if (!title) {
        return;
      }
      const created = await this._postAction("create_list", { title });
      if (created) {
        const newList = this._getLists().find((list) => list.title === title);
        if (newList) {
          this._selectedListId = newList.id;
        }
        this._creatingList = false;
        this._menuListId = null;
        this._render();
      }
      return;
    }

    const input = form.querySelector('input[name="text"]');
    const text = input?.value?.trim();
    const listId = form.dataset.listId;
    if (!text || !listId) {
      return;
    }
    const added = await this._postAction("add_item", { list_id: listId, text });
    if (added) {
      input.value = "";
    }
  }

  async _handleClick(ev) {
    const target = ev.target.closest("[data-action]");
    if (!target) {
      return;
    }
    const action = target.dataset.action;
    const listId = target.dataset.listId;
    const itemId = target.dataset.itemId;

    if (action === "select-list" && listId) {
      this._selectedListId = listId;
      this._menuListId = null;
      this._render();
      return;
    }
    if (action === "move-list-up" && listId) {
      await this._postAction("move_list", { list_id: listId, direction: "up" });
      return;
    }
    if (action === "move-list-down" && listId) {
      await this._postAction("move_list", { list_id: listId, direction: "down" });
      return;
    }
    if (action === "toggle-menu" && listId) {
      this._menuListId = this._menuListId === listId ? null : listId;
      this._render();
      return;
    }
    if (action === "toggle-create-list") {
      this._creatingList = !this._creatingList;
      this._menuListId = null;
      this._render();
      return;
    }
    if (action === "rename-list" && listId) {
      const list = this._getLists().find((entry) => entry.id === listId);
      const title = window.prompt("Rename list", list?.title || "");
      if (title) {
        await this._postAction("rename_list", { list_id: listId, title });
      }
      this._menuListId = null;
      return;
    }
    if (action === "toggle-lock" && listId) {
      const locked = target.dataset.locked === "true";
      await this._postAction("set_list_lock", { list_id: listId, locked: !locked });
      return;
    }
    if (action === "focus") {
      this._focusOpen = true;
      this._render();
      return;
    }
    if (action === "close-focus") {
      this._focusOpen = false;
      this._render();
      return;
    }
    if (action === "delete-list" && listId) {
      if (window.confirm("Delete this list?")) {
        await this._postAction("delete_list", { list_id: listId });
      }
      this._menuListId = null;
      return;
    }
    if (action === "toggle-item" && listId && itemId) {
      const checked = target.dataset.checked === "true";
      await this._postAction(checked ? "uncheck_item" : "check_item", {
        list_id: listId,
        item_id: itemId,
      });
      return;
    }
    if (action === "delete-item" && listId && itemId) {
      ev.stopPropagation();
      await this._postAction("delete_item", { list_id: listId, item_id: itemId });
      return;
    }
    if (action === "edit-item" && listId && itemId) {
      ev.stopPropagation();
      const list = this._pickList();
      const item = list?.items?.find((entry) => entry.id === itemId);
      const text = window.prompt("Edit item", item?.text || "");
      if (text) {
        await this._postAction("update_item", {
          list_id: listId,
          item_id: itemId,
          updates: { text },
        });
      }
    }
  }

  getCardSize() {
    return 8;
  }

  getGridOptions() {
    return {
      rows: 8,
      columns: 12,
      min_rows: 6,
    };
  }
}

class UltimateListsCardEditor extends HTMLElement {
  setConfig() {
    this.innerHTML = "<div style='padding:12px'>Use the built-in form editor for Ultimate Lists.</div>";
  }
}

customElements.define("ultimate-lists-card", UltimateListsCard);
customElements.define("ultimate-lists-card-editor", UltimateListsCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ultimate-lists-card",
  name: "Ultimate Lists",
  preview: true,
  description: "Two-column household lists for Home Assistant.",
  documentationURL: "https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/",
});

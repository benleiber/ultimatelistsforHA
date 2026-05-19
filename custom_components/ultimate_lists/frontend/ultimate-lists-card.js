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
        { name: "focus_mode", selector: { boolean: {} } },
        { name: "show_completed", selector: { boolean: {} } },
      ],
    };
  }

  setConfig(config) {
    this._config = {
      focus_mode: false,
      show_completed: true,
      ...config,
    };
    if (!this._root) {
      this._root = this.attachShadow({ mode: "open" });
    }
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._loadData();
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
      this._render();
    } catch (err) {
      this._error = this._formatError(err);
      this._render();
    } finally {
      this._loading = false;
    }
  }

  _pickList() {
    const lists = this._data?.lists || [];
    if (!lists.length) {
      return null;
    }
    if (!this._config?.entity) {
      return lists[0];
    }
    return lists.find((list) => list.entity_id === this._config.entity) || lists[0];
  }

  async _postAction(action, data) {
    try {
      this._data = await this._hass.callApi("POST", "ultimate_lists/action", { action, data });
      this._error = "";
      this._render();
    } catch (err) {
      this._error = this._formatError(err);
      this._render();
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
              <button class="icon-button" data-action="edit-item" data-list-id="${list.id}" data-item-id="${item.id}" type="button">Edit</button>
              <button class="icon-button danger" data-action="delete-item" data-list-id="${list.id}" data-item-id="${item.id}" type="button">Delete</button>
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
            <button class="icon-button" data-action="close-focus" type="button">Close</button>
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

    const list = this._pickList();
    const title = this._config.title || list?.title || "Ultimate Lists";

    this._root.innerHTML = `
      <style>
        :host {
          display: block;
          --ul-border: rgba(120, 132, 160, 0.22);
          --ul-bg: linear-gradient(180deg, rgba(250,251,253,0.98), rgba(242,245,249,0.98));
          --ul-panel: rgba(255,255,255,0.92);
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
        .card {
          padding: 18px;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 14px;
        }
        .header h1 {
          font-size: 1.05rem;
          line-height: 1.2;
          margin: 0 0 4px;
        }
        .subtle, .meta, .eyebrow {
          color: var(--ul-subtle);
        }
        .eyebrow {
          text-transform: uppercase;
          letter-spacing: 0.08em;
          font-size: 0.7rem;
          font-weight: 700;
        }
        .header-actions, .item-actions {
          display: flex;
          gap: 8px;
          align-items: center;
        }
        .quick-add {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 10px;
          margin-bottom: 14px;
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
        button {
          font: inherit;
        }
        .quick-add button,
        .icon-button {
          border: 0;
          border-radius: 14px;
          padding: 10px 14px;
          cursor: pointer;
        }
        .quick-add button {
          background: var(--ul-accent);
          color: white;
          font-weight: 700;
        }
        .icon-button {
          background: rgba(33, 48, 74, 0.08);
          color: var(--ul-text);
        }
        .icon-button.danger {
          color: var(--ul-danger);
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
        }
        .item-text {
          font-weight: 600;
        }
        .empty {
          padding: 18px 6px 8px;
          color: var(--ul-subtle);
        }
        .overlay {
          position: fixed;
          inset: 0;
          background: rgba(8, 14, 24, 0.58);
          display: flex;
          align-items: stretch;
          justify-content: center;
          padding: 0;
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
        <div class="card">
          <div class="header">
            <div>
              <div class="eyebrow">Ultimate Lists</div>
              <h1>${this._escape(title)}</h1>
              <div class="subtle">${list ? `${list.incomplete_count} active items` : "No lists found"}</div>
            </div>
            <div class="header-actions">
              <button class="icon-button" data-action="new-list" type="button">New List</button>
              ${list ? `<button class="icon-button" data-action="focus" type="button">Focus</button>` : ""}
              ${list ? `<button class="icon-button danger" data-action="delete-list" data-list-id="${list.id}" type="button">Delete</button>` : ""}
            </div>
          </div>
          ${this._error ? `<div class="empty">${this._escape(this._error)}</div>` : ""}
          ${this._creatingList ? `
            <form class="quick-add" data-action="submit-list">
              <input name="title" type="text" placeholder="New list name..." />
              <button type="submit">Create</button>
            </form>
          ` : ""}
          ${list ? `
            <form class="quick-add" data-action="submit-item" data-list-id="${list.id}">
              <input name="text" type="text" placeholder="Add item..." />
              <button type="submit">Add</button>
            </form>
            <div class="items">${this._renderItems(list, false)}</div>
          ` : `<div class="empty">Create your first list to get started.</div>`}
        </div>
      </ha-card>
      ${list ? this._renderFocusOverlay(list) : ""}
    `;

    this._root.querySelector(".focus-shell")?.addEventListener("click", (ev) => ev.stopPropagation());
    this._root.querySelectorAll("[data-action]").forEach((node) => {
      node.addEventListener("click", (ev) => this._handleClick(ev));
    });
    this._root.querySelectorAll('form[data-action="submit-item"]').forEach((form) => {
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
      await this._postAction("create_list", { title });
      this._creatingList = false;
      return;
    }
    const input = form.querySelector('input[name="text"]');
    const text = input?.value?.trim();
    const listId = form.dataset.listId;
    if (!text || !listId) {
      return;
    }
    await this._postAction("add_item", { list_id: listId, text });
    input.value = "";
  }

  async _handleClick(ev) {
    const target = ev.target.closest("[data-action]");
    if (!target) {
      return;
    }
    const action = target.dataset.action;
    const listId = target.dataset.listId;
    const itemId = target.dataset.itemId;

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
    if (action === "new-list") {
      this._creatingList = !this._creatingList;
      this._render();
      return;
    }
    if (action === "delete-list" && listId) {
      if (window.confirm("Delete this list?")) {
        await this._postAction("delete_list", { list_id: listId });
      }
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
    return this._config?.focus_mode ? 6 : 4;
  }

  getGridOptions() {
    return {
      rows: this._config?.focus_mode ? 6 : 4,
      columns: 6,
      min_rows: 3,
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
  description: "Compact and focus-friendly lists for Home Assistant.",
  documentationURL: "https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/",
});

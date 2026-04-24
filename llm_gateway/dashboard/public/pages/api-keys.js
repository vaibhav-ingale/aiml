import { api, formatMoney, formatDate, buildTable, formatPercent } from "../lib.js";

export function renderApiKeys() {
  return `
    <div class="page-header">
      <div>
        <h1>API Key Management</h1>
        <p>Generate keys with scoped model access and cost controls.</p>
      </div>
    </div>

    
    <div class="grid-1">
      <div class="card">
        <h3>Existing API Keys</h3>
        <div class="table-wrap" id="keysTable"></div>
        <div id="keyActionNotice" class="notice"></div>
      </div>
      <div class="card">
        <h3>Generate New API Key</h3>
        <div class="section-stack">
          <form id="createKeyForm" class="form-grid">
            <div>
              <label for="keyUser">Select user</label>
              <select id="keyUser" name="user_id"></select>
            </div>
            <div>
              <label for="keyModels">Allowed models</label>
              <select id="keyModels" name="allowed_models" multiple size="10"></select>
            </div>
            <div>
              <label for="costLimit">Cost limit ($)</label>
              <input id="costLimit" name="cost_limit" type="number" min="0" step="1" value="100" />
            </div>
            <div class="button-row">
              <button class="primary" type="submit">Generate API Key</button>
            </div>
          </form>
          <div id="keyNotice" class="notice"></div>
        </div>
      </div>

   
    </div>
  `;
}

export async function afterRenderApiKeys() {
  const userSelect = document.querySelector("#keyUser");
  const modelSelect = document.querySelector("#keyModels");
  const notice = document.querySelector("#keyNotice");
  notice.style.display = "none";
  const tableWrap = document.querySelector("#keysTable");
  const actionNotice = document.querySelector("#keyActionNotice");
  actionNotice.style.display = "none";

  const loadOptions = async () => {
    const users = await api("users");
    userSelect.innerHTML = users
      .map((user) => `<option value="${user.id}">${user.username}</option>`)
      .join("");

    const models = await api("models");
    const options = ["* (All Models)", ...models.map((model) => model.model_name)];
    modelSelect.innerHTML = options.map((model) => `<option value="${model}">${model}</option>`).join("");
    modelSelect.value = "* (All Models)";
  };

  const loadKeys = async () => {
    const keys = await api("api-keys");
    const rows = keys.map((key) => {
      const usage = key.cost_limit > 0 ? (key.current_cost / key.cost_limit) * 100 : 0;
      const statusLabel = key.is_active ? "Active" : "Inactive (Locked)";
      const copyBtn = `<button class="secondary btn-sm" data-action="copy" data-key="${key.api_key}" title="Copy API key"><i class="fa-solid fa-copy"></i></button>`;
      const actions = key.is_active
        ? `<div class="button-row">
          ${copyBtn}
          <button class="secondary" data-action="toggle" data-id="${key.id}" data-active="true">Disable</button>
          <button class="danger" data-action="delete" data-id="${key.id}">Delete</button>
        </div>`
        : `<div class="button-row">
          ${copyBtn}
          <button class="danger" data-action="delete" data-id="${key.id}">Delete</button>
        </div>`;
      return [
        key.username,
        key.api_key.slice(0, 18) + "…",
        key.allowed_models.slice(0, 3).join(", ") + (key.allowed_models.length > 3 ? "…" : ""),
        formatMoney(key.current_cost),
        key.cost_limit > 0 ? formatMoney(key.cost_limit, 2) : "Unlimited",
        key.cost_limit > 0 ? formatPercent(usage) : "N/A",
        statusLabel,
        actions,
      ];
    });

    tableWrap.innerHTML = buildTable(
      ["User", "Key", "Models", "Cost", "Limit", "Usage", "Status", "Actions"],
      rows
    );

    tableWrap.querySelectorAll("button[data-action]").forEach((button) => {
      button.addEventListener("click", async () => {
        const id = button.dataset.id;
        const action = button.dataset.action;
        actionNotice.style.display = "none";
        actionNotice.classList.remove("error");
        try {
          if (action === "copy") {
            await navigator.clipboard.writeText(button.dataset.key);
            const icon = button.querySelector("i");
            icon.className = "fa-solid fa-check";
            button.style.color = "#10b981";
            setTimeout(() => {
              icon.className = "fa-solid fa-copy";
              button.style.color = "";
            }, 1500);
            return;
          }
          if (action === "delete") {
            if (!window.confirm("Delete this API key?")) return;
            await api(`api-keys/${id}`, { method: "DELETE" });
          } else {
            const isActive = button.dataset.active === "true";
            await api(`api-keys/${id}`, {
              method: "PATCH",
              body: JSON.stringify({ is_active: !isActive }),
            });
          }
          await loadKeys();
        } catch (error) {
          actionNotice.textContent = error.message;
          actionNotice.classList.add("error");
          actionNotice.style.display = "block";
        }
      });
    });
  };

  document.querySelector("#createKeyForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    notice.classList.remove("error");
    notice.textContent = "";
    notice.style.display = "none";
    const form = event.target;
    const allowed = Array.from(form.allowed_models.selectedOptions).map((opt) => opt.value);
    try {
      const result = await api("api-keys", {
        method: "POST",
        body: JSON.stringify({
          user_id: Number(form.user_id.value),
          allowed_models: allowed.length ? allowed : ["* (All Models)"],
          cost_limit: Number(form.cost_limit.value || 0),
        }),
      });
      notice.textContent = `API key created: ${result.api_key}`;
      notice.style.display = "block";
      await loadKeys();
    } catch (error) {
      notice.textContent = error.message;
      notice.classList.add("error");
      notice.style.display = "block";
    }
  });

  try {
    await loadOptions();
    await loadKeys();
  } catch (error) {
    tableWrap.innerHTML = `<div class="empty">${error.message}</div>`;
  }
}

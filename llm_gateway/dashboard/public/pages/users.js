import { api, formatMoney, formatDate, buildTable, formatNumber } from "../lib.js";

export function renderUsers() {
  return `
    <div class="page-header">
      <div>
        <h1>User Management</h1>
        <p>Create, audit, and retire gateway users.</p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Create New User</h3>
        <form id="createUserForm" class="form-grid">
          <div>
            <label for="username">Username</label>
            <input id="username" name="username" placeholder="Enter username" required />
          </div>
          <div class="button-row">
            <button class="primary" type="submit">Create User</button>
          </div>
        </form>
        <div id="createUserNotice" class="notice"></div>
      </div>

      <div class="card">
        <h3>Existing Users</h3>
        <div class="table-wrap" id="usersTable"></div>
      </div>
    </div>

    <div class="card">
      <h3>User Details</h3>
      <div class="form-grid">
        <div>
          <label for="userSelect">Select user</label>
          <select id="userSelect"></select>
        </div>
      </div>
      <div class="section-stack">
        <div class="grid-3" id="userMetrics"></div>
        <div class="button-row" id="userActions"></div>
        <div class="table-wrap" id="userKeys"></div>
      </div>
    </div>
  `;
}

export async function afterRenderUsers() {
  const tableWrap = document.querySelector("#usersTable");
  const select = document.querySelector("#userSelect");
  const metrics = document.querySelector("#userMetrics");
  const actions = document.querySelector("#userActions");
  const keysWrap = document.querySelector("#userKeys");
  const notice = document.querySelector("#createUserNotice");
  notice.style.display = "none";

  const loadUsers = async () => {
    const users = await api("users/with-stats");
    const rows = users.map((user) => [
      user.username,
      `${user.api_keys_count} keys`,
      formatNumber(user.total_requests),
      formatMoney(user.total_cost),
      formatDate(user.created_at),
    ]);
    tableWrap.innerHTML = buildTable(
      ["User", "API Keys", "Requests", "Cost", "Created"],
      rows
    );

    select.innerHTML = users
      .map((user) => `<option value="${user.id}">${user.username}</option>`)
      .join("");

    if (users.length) {
      select.value = users[0].id;
      await loadUserDetail(users[0].id);
    } else {
      metrics.innerHTML = "";
      actions.innerHTML = "";
      keysWrap.innerHTML = "<div class=\"empty\">No users found.</div>";
    }
  };

  const loadUserDetail = async (userId) => {
    const user = await api(`users/${userId}`);
    const summary = await api(`summary?user_id=${userId}`);
    const keys = await api(`users/${userId}/api-keys`);

    metrics.innerHTML = `
      <div class="card metric">
        <div class="label">User ID</div>
        <div class="value">${user.id}</div>
      </div>
      <div class="card metric">
        <div class="label">Total Requests</div>
        <div class="value">${formatNumber(summary.total_requests)}</div>
      </div>
      <div class="card metric">
        <div class="label">Total Cost</div>
        <div class="value">${formatMoney(summary.total_cost)}</div>
      </div>
    `;

    actions.innerHTML = `
      <div class="button-row align-right">
        <button class="danger" id="deleteUser">Delete User</button>
      </div>
    `;

    document.querySelector("#deleteUser").addEventListener("click", async () => {
      if (!window.confirm(`Delete ${user.username}? This removes all keys and usage logs.`)) {
        return;
      }
      await api(`users/${userId}`, { method: "DELETE" });
      await loadUsers();
    });

    const rows = keys.map((key) => [
      key.api_key.slice(0, 18) + "…",
      key.is_active ? "Active" : "Inactive",
      key.allowed_models.join(", "),
      key.cost_limit > 0 ? formatMoney(key.cost_limit, 2) : "Unlimited",
      formatMoney(key.current_cost),
    ]);
    keysWrap.innerHTML = `
      <h3>API Keys</h3>
      ${buildTable(["Key", "Status", "Models", "Limit", "Cost"], rows)}
    `;
  };

  document.querySelector("#createUserForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = event.target.username.value.trim();
    notice.textContent = "";
    notice.classList.remove("error");
    notice.style.display = "none";
    if (!username) {
      notice.textContent = "Please enter a username.";
      notice.style.display = "block";
      return;
    }
    try {
      const result = await api("users", {
        method: "POST",
        body: JSON.stringify({ username }),
      });
      notice.textContent = `User created (ID: ${result.id}).`;
      notice.style.display = "block";
      event.target.reset();
      await loadUsers();
    } catch (error) {
      notice.textContent = error.message;
      notice.classList.add("error");
      notice.style.display = "block";
    }
  });

  select.addEventListener("change", async (event) => {
    await loadUserDetail(event.target.value);
  });

  try {
    await loadUsers();
  } catch (error) {
    tableWrap.innerHTML = `<div class="empty">${error.message}</div>`;
  }
}

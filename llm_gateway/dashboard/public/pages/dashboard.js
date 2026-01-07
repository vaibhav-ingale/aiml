import { api, formatMoney, formatNumber, formatDate, buildTable, groupBy, sumBy } from "../lib.js";

export function renderDashboard() {
  return `
    <div class="page-header">
      <div>
        <h1>Dashboard Overview</h1>
        <p>Live pulse across requests, costs, and users.</p>
      </div>
    </div>

    <div class="cards" id="dashboard-metrics">
      <div class="card metric">
        <div class="label">Total Requests</div>
        <div class="value" data-metric="total_requests">-</div>
      </div>
      <div class="card metric">
        <div class="label">Total Tokens</div>
        <div class="value" data-metric="total_tokens">-</div>
      </div>
      <div class="card metric">
        <div class="label">Total Cost</div>
        <div class="value" data-metric="total_cost">-</div>
      </div>
      <div class="card metric">
        <div class="label">Avg Response Time</div>
        <div class="value" data-metric="avg_response_time">-</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Recent Activity (Last 7 Days)</h3>
        <div class="chart-wrap"><canvas id="requestsChart"></canvas></div>
        <div class="empty" id="requestsEmpty"></div>
      </div>
      <div class="card">
        <h3>Cost Breakdown by Model</h3>
        <div class="chart-wrap"><canvas id="costChart"></canvas></div>
        <div class="empty" id="costEmpty"></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Active Users</h3>
        <small id="userCount">-</small>
        <div class="table-wrap" id="usersTable"></div>
      </div>
      <div class="card">
        <h3>API Keys Status</h3>
        <small id="keyCount">-</small>
        <div class="table-wrap" id="keysTable"></div>
      </div>
    </div>
  `;
}

export async function afterRenderDashboard() {
  const metrics = document.querySelectorAll("[data-metric]");
  metrics.forEach((el) => (el.textContent = "…"));

  try {
    const summary = await api("summary");
    document.querySelector('[data-metric="total_requests"]').textContent = formatNumber(summary.total_requests);
    document.querySelector('[data-metric="total_tokens"]').textContent = formatNumber(summary.total_tokens);
    document.querySelector('[data-metric="total_cost"]').textContent = formatMoney(summary.total_cost);
    document.querySelector('[data-metric="avg_response_time"]').textContent = `${Number(summary.avg_response_time).toFixed(2)}s`;
  } catch (error) {
    document.querySelector("#dashboard-metrics").insertAdjacentHTML(
      "beforeend",
      `<div class="notice error">${error.message}</div>`
    );
  }

  let usage7 = [];
  let usage30 = [];
  try {
    usage7 = await api("usage?days=7");
    usage30 = await api("usage?days=30");
  } catch (error) {
    document.querySelector("#requestsEmpty").textContent = error.message;
  }

  renderRequestsChart(usage7);
  renderCostChart(usage30);

  try {
    const users = await api("users");
    document.querySelector("#userCount").textContent = `${users.length} total`;
    const rows = users.slice(0, 6).map((user) => [user.username, formatDate(user.created_at)]);
    document.querySelector("#usersTable").innerHTML = buildTable(["User", "Created"], rows);
  } catch (error) {
    document.querySelector("#usersTable").innerHTML = `<div class="empty">${error.message}</div>`;
  }

  try {
    const keys = await api("api-keys");
    const active = keys.filter((key) => key.is_active);
    document.querySelector("#keyCount").textContent = `${active.length} active`;
    const rows = active.slice(0, 5).map((key) => [
      key.username,
      formatMoney(key.current_cost),
      key.cost_limit > 0 ? formatMoney(key.cost_limit, 2) : "Unlimited",
    ]);
    document.querySelector("#keysTable").innerHTML = buildTable(["User", "Cost", "Limit"], rows);
  } catch (error) {
    document.querySelector("#keysTable").innerHTML = `<div class="empty">${error.message}</div>`;
  }
}

function renderRequestsChart(logs) {
  const canvas = document.querySelector("#requestsChart");
  const empty = document.querySelector("#requestsEmpty");

  if (!logs.length) {
    empty.textContent = "No activity in the last 7 days.";
    canvas.style.display = "none";
    return;
  }

  const grouped = groupBy(logs, (log) => toLocalDateKey(log.created_at));
  const labels = Object.keys(grouped).sort();
  const data = labels.map((label) => grouped[label].length);

  empty.textContent = "";
  canvas.style.display = "block";
  new window.Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Requests",
          data,
          borderColor: "#2dd4bf",
          backgroundColor: "rgba(45, 212, 191, 0.2)",
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { ticks: { color: "#b9c1bf" } },
        y: { ticks: { color: "#b9c1bf" } },
      },
    },
  });
}

function renderCostChart(logs) {
  const canvas = document.querySelector("#costChart");
  const empty = document.querySelector("#costEmpty");

  if (!logs.length) {
    empty.textContent = "No cost data available.";
    canvas.style.display = "none";
    return;
  }

  const grouped = groupBy(logs, (log) => log.model_name);
  const entries = Object.entries(grouped)
    .map(([model, items]) => ({ model, cost: sumBy(items, "cost") }))
    .sort((a, b) => b.cost - a.cost);

  const labels = entries.map((entry) => entry.model);
  const data = entries.map((entry) => entry.cost);

  empty.textContent = "";
  canvas.style.display = "block";
  new window.Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Cost",
          data,
          backgroundColor: "rgba(247, 184, 1, 0.6)",
          borderColor: "#f7b801",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { ticks: { color: "#b9c1bf" } },
        y: { ticks: { color: "#b9c1bf" } },
      },
    },
  });
}

function toLocalDateKey(value) {
  if (!value) return "Unknown";
  const parts = String(value).split(/[- :T]/).map(Number);
  if (parts.length >= 3 && parts.every((part) => Number.isFinite(part))) {
    const [year, month, day, hour, minute, second] = parts;
    const date = new Date(year, month - 1, day, hour || 0, minute || 0, second || 0);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(
      date.getDate()
    ).padStart(2, "0")}`;
  }
  const fallback = new Date(value);
  if (Number.isNaN(fallback.getTime())) return String(value);
  return `${fallback.getFullYear()}-${String(fallback.getMonth() + 1).padStart(2, "0")}-${String(
    fallback.getDate()
  ).padStart(2, "0")}`;
}

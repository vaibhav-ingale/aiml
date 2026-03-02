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
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h3 style="margin: 0;">Recent Activity</h3>
          <div class="btn-group" id="activityTimeRange">
            <button class="btn-sm secondary active" data-days="1">Today</button>
            <button class="btn-sm secondary" data-days="7">7d</button>
            <button class="btn-sm secondary" data-days="15">15d</button>
            <button class="btn-sm secondary" data-days="30">30d</button>
          </div>
        </div>
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

  // Load initial data for charts
  let currentActivityDays = 1;
  const loadActivityChart = async (days) => {
    try {
      const usage = await api(`usage?days=${days}`);
      renderRequestsChart(usage);
    } catch (error) {
      document.querySelector("#requestsEmpty").textContent = error.message;
    }
  };

  // Load initial charts
  await loadActivityChart(currentActivityDays);

  let usage30 = [];
  try {
    usage30 = await api("usage?days=30");
  } catch (error) {
    // Error handling for cost chart
  }
  renderCostChart(usage30);

  // Setup time range selector for Recent Activity
  document.querySelectorAll("#activityTimeRange button").forEach((button) => {
    button.addEventListener("click", async () => {
      const days = Number(button.dataset.days);
      currentActivityDays = days;

      // Update active state
      document.querySelectorAll("#activityTimeRange button").forEach((btn) => {
        btn.classList.remove("active");
      });
      button.classList.add("active");

      // Reload chart
      await loadActivityChart(days);
    });
  });

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

let requestsChart = null;

function renderRequestsChart(logs) {
  const canvas = document.querySelector("#requestsChart");
  const empty = document.querySelector("#requestsEmpty");

  // Destroy existing chart if it exists
  if (requestsChart) {
    requestsChart.destroy();
    requestsChart = null;
  }

  if (!logs.length) {
    empty.textContent = "No activity in the selected time range.";
    canvas.style.display = "none";
    return;
  }

  const grouped = groupBy(logs, (log) => toLocalDateKey(log.created_at));
  const labels = Object.keys(grouped).sort();
  const data = labels.map((label) => grouped[label].length);

  empty.textContent = "";
  canvas.style.display = "block";
  requestsChart = new window.Chart(canvas, {
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

  // Generate different colors for each model
  const colors = [
    { bg: "rgba(247, 184, 1, 0.6)", border: "#f7b801" },      // Yellow
    { bg: "rgba(45, 212, 191, 0.6)", border: "#2dd4bf" },     // Teal
    { bg: "rgba(255, 107, 107, 0.6)", border: "#ff6b6b" },    // Red
    { bg: "rgba(16, 185, 129, 0.6)", border: "#10b981" },     // Green
    { bg: "rgba(139, 92, 246, 0.6)", border: "#8b5cf6" },     // Purple
    { bg: "rgba(59, 130, 246, 0.6)", border: "#3b82f6" },     // Blue
    { bg: "rgba(236, 72, 153, 0.6)", border: "#ec4899" },     // Pink
    { bg: "rgba(245, 158, 11, 0.6)", border: "#f59e0b" },     // Amber
    { bg: "rgba(20, 184, 166, 0.6)", border: "#14b8a6" },     // Cyan
    { bg: "rgba(168, 85, 247, 0.6)", border: "#a855f7" },     // Violet
  ];

  const backgroundColors = data.map((_, i) => colors[i % colors.length].bg);
  const borderColors = data.map((_, i) => colors[i % colors.length].border);

  new window.Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Cost",
          data,
          backgroundColor: backgroundColors,
          borderColor: borderColors,
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

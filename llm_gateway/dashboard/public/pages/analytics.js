import {
  api,
  formatMoney,
  formatNumber,
  buildTable,
  groupBy,
  sumBy,
  binValues,
} from "../lib.js";

let charts = {};

export function renderAnalytics() {
  return `
    <div class="page-header">
      <div>
        <h1>Analytics & Insights</h1>
        <p>Explore usage patterns, performance, and cost trends.</p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <label for="timeRange">Time range</label>
        <select id="timeRange">
          <option value="7">Last 7 Days</option>
          <option value="30" selected>Last 30 Days</option>
          <option value="90">Last 90 Days</option>
          <option value="999999">All Time</option>
        </select>
      </div>
      <div class="card">
        <label for="userFilter">Filter by user</label>
        <select id="userFilter"></select>
      </div>
    </div>

    <div class="cards" id="analyticsMetrics">
      <div class="card metric">
        <div class="label">Total Requests</div>
        <div class="value" data-analytics="requests">-</div>
      </div>
      <div class="card metric">
        <div class="label">Total Tokens</div>
        <div class="value" data-analytics="tokens">-</div>
      </div>
      <div class="card metric">
        <div class="label">Total Cost</div>
        <div class="value" data-analytics="cost">-</div>
      </div>
      <div class="card metric">
        <div class="label">Avg Response Time</div>
        <div class="value" data-analytics="latency">-</div>
      </div>
      <div class="card metric">
        <div class="label">Success Rate</div>
        <div class="value" data-analytics="success">-</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Requests Over Time</h3>
        <div class="chart-wrap"><canvas id="requestsChart"></canvas></div>
      </div>
      <div class="card">
        <h3>Requests Over a Day</h3>
        <div class="chart-wrap"><canvas id="hourlyChart"></canvas></div>
      </div>
  
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Cost Over Time</h3>
        <div class="chart-wrap"><canvas id="costChart"></canvas></div>
      </div>
      <div class="card">
        <h3>Response Time Distribution</h3>
        <div class="chart-wrap"><canvas id="latencyChart"></canvas></div>
      </div>
    </div>

    <div class="grid-2">
    <div class="card compact">
        <h3>Token Distribution</h3>
        <div class="chart-wrap"><canvas id="tokensChart"></canvas></div>
      </div>
      <div class="card compact">
        <h3>Model Usage Share</h3>
        <div class="chart-wrap"><canvas id="modelUsageChart"></canvas></div>
      </div>
    </div>

    <div class="card">
      <h3>Model Usage Statistics</h3>
      <div class="table-wrap" id="modelTable"></div>
    </div>

    <div class="card">
      <h3>Usage Heatmap (by Hour)</h3>
      <div class="heatmap" id="heatmap"></div>
    </div>
  `;
}

export async function afterRenderAnalytics() {
  const userFilter = document.querySelector("#userFilter");
  const timeRange = document.querySelector("#timeRange");

  const users = await api("users");
  userFilter.innerHTML = [
    `<option value="all">All Users</option>`,
    ...users.map((user) => `<option value="${user.id}">${user.username}</option>`),
  ].join("");

  const loadAnalytics = async () => {
    const days = Number(timeRange.value);
    const userId = userFilter.value !== "all" ? Number(userFilter.value) : null;
    const query = `usage?days=${days}${userId ? `&user_id=${userId}` : ""}`;
    const logs = await api(query);

    updateMetrics(logs);
    renderCharts(logs);
    renderModelTable(logs);
    renderHeatmap(logs);
  };

  timeRange.addEventListener("change", loadAnalytics);
  userFilter.addEventListener("change", loadAnalytics);

  await loadAnalytics();
}

function updateMetrics(logs) {
  const totalTokens = sumBy(logs, "total_tokens");
  const totalCost = sumBy(logs, "cost");
  const avgLatency = logs.length
    ? logs.reduce((acc, item) => acc + Number(item.response_time || 0), 0) / logs.length
    : 0;
  const successRate = logs.length
    ? (logs.filter((log) => log.status === "success").length / logs.length) * 100
    : 0;

  document.querySelector('[data-analytics="requests"]').textContent = formatNumber(logs.length);
  document.querySelector('[data-analytics="tokens"]').textContent = formatNumber(totalTokens);
  document.querySelector('[data-analytics="cost"]').textContent = formatMoney(totalCost);
  document.querySelector('[data-analytics="latency"]').textContent = `${avgLatency.toFixed(2)}s`;
  document.querySelector('[data-analytics="success"]').textContent = `${successRate.toFixed(1)}%`;
}

function renderCharts(logs) {
  Object.values(charts).forEach((chart) => chart.destroy());
  charts = {};

  const requestsCanvas = document.querySelector("#requestsChart");
  const tokensCanvas = document.querySelector("#tokensChart");
  const costCanvas = document.querySelector("#costChart");
  const latencyCanvas = document.querySelector("#latencyChart");
  const hourlyCanvas = document.querySelector("#hourlyChart");
  const modelUsageCanvas = document.querySelector("#modelUsageChart");

  const groupedByDate = groupBy(logs, (log) => toLocalDateKey(log.created_at));
  const dateLabels = Object.keys(groupedByDate).sort();
  const requestCounts = dateLabels.map((label) => groupedByDate[label].length);

  charts.requests = new window.Chart(requestsCanvas, {
    type: "line",
    data: {
      labels: dateLabels,
      datasets: [
        {
          label: "Requests",
          data: requestCounts,
          borderColor: "#2dd4bf",
          backgroundColor: "rgba(45, 212, 191, 0.2)",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: baseChartOptions(),
  });

  const inputTokens = sumBy(logs, "input_tokens");
  const outputTokens = sumBy(logs, "output_tokens");
  charts.tokens = new window.Chart(tokensCanvas, {
    type: "doughnut",
    data: {
      labels: ["Input", "Output"],
      datasets: [
        {
          data: [inputTokens, outputTokens],
          backgroundColor: ["#2dd4bf", "#f7b801"],
        },
      ],
    },
    options: baseChartOptions(),
  });

  const costByDate = dateLabels.map((label) => sumBy(groupedByDate[label], "cost"));
  charts.cost = new window.Chart(costCanvas, {
    type: "bar",
    data: {
      labels: dateLabels,
      datasets: [
        {
          label: "Cost",
          data: costByDate,
          backgroundColor: "rgba(247, 184, 1, 0.6)",
        },
      ],
    },
    options: baseChartOptions(),
  });

  const responseTimes = logs.map((log) => Number(log.response_time || 0));
  const bins = binValues(responseTimes, 8);
  charts.latency = new window.Chart(latencyCanvas, {
    type: "bar",
    data: {
      labels: bins.labels,
      datasets: [
        {
          label: "Responses",
          data: bins.counts,
          backgroundColor: "rgba(45, 212, 191, 0.4)",
        },
      ],
    },
    options: baseChartOptions(),
  });

  const hourlyCounts = Array.from({ length: 24 }, () => 0);
  logs.forEach((log) => {
    const hour = parseLocalHour(log.created_at);
    hourlyCounts[hour] += 1;
  });
  charts.hourly = new window.Chart(hourlyCanvas, {
    type: "bar",
    data: {
      labels: hourlyCounts.map((_, hour) => `${hour.toString().padStart(2, "0")}:00`),
      datasets: [
        {
          label: "Requests",
          data: hourlyCounts,
          backgroundColor: "rgba(45, 212, 191, 0.5)",
        },
      ],
    },
    options: baseChartOptions(),
  });

  const byModel = groupBy(logs, (log) => log.model_name);
  const modelLabels = Object.keys(byModel);
  const modelCounts = modelLabels.map((label) => byModel[label].length);
  charts.modelUsage = new window.Chart(modelUsageCanvas, {
    type: "pie",
    data: {
      labels: modelLabels,
      datasets: [
        {
          data: modelCounts,
          backgroundColor: [
            "#2dd4bf",
            "#f7b801",
            "#94a3b8",
            "#fb7185",
            "#22d3ee",
            "#f97316",
            "#38bdf8",
          ],
        },
      ],
    },
    options: baseChartOptions(),
  });
}

function parseLocalHour(value) {
  if (!value) return 0;
  const parts = String(value).split(/[- :T]/).map(Number);
  if (parts.length >= 6 && parts.every((part) => Number.isFinite(part))) {
    const [year, month, day, hour, minute, second] = parts;
    return new Date(year, month - 1, day, hour, minute || 0, second || 0).getHours();
  }
  const fallback = new Date(value);
  return Number.isNaN(fallback.getTime()) ? 0 : fallback.getHours();
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

function renderModelTable(logs) {
  const table = document.querySelector("#modelTable");
  if (!logs.length) {
    table.innerHTML = "<div class=\"empty\">No usage data for this range.</div>";
    return;
  }
  const grouped = groupBy(logs, (log) => log.model_name);
  const rows = Object.entries(grouped).map(([model, items]) => {
    const totalTokens = sumBy(items, "total_tokens");
    const totalCost = sumBy(items, "cost");
    const avgLatency = items.reduce((acc, item) => acc + Number(item.response_time || 0), 0) / items.length;
    return [
      model,
      formatNumber(items.length),
      formatNumber(totalTokens),
      formatMoney(totalCost),
      `${avgLatency.toFixed(2)}s`,
    ];
  });
  table.innerHTML = buildTable(["Model", "Requests", "Tokens", "Cost", "Avg Latency"], rows);
}

function renderHeatmap(logs) {
  const heatmap = document.querySelector("#heatmap");
  if (!logs.length) {
    heatmap.innerHTML = "<div class=\"empty\">No activity to display.</div>";
    return;
  }

  const metrics = {};
  logs.forEach((log) => {
    const date = toLocalDateKey(log.created_at);
    const hour = parseLocalHour(log.created_at);
    if (!metrics[date]) metrics[date] = {};
    if (!metrics[date][hour]) metrics[date][hour] = { count: 0, tokens: 0, cost: 0 };
    metrics[date][hour].count += 1;
    metrics[date][hour].tokens += Number(log.total_tokens || 0);
    metrics[date][hour].cost += Number(log.cost || 0);
  });

  const monthKeys = Array.from(
    new Set(Object.keys(metrics).map((dateKey) => dateKey.slice(0, 7)))
  ).sort();

  const monthBlocks = monthKeys.map((monthKey) => {
    const [yearStr, monthStr] = monthKey.split("-");
    const year = Number(yearStr);
    const monthIndex = Number(monthStr) - 1;
    const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
    const dateKeys = Array.from({ length: daysInMonth }, (_, i) => {
      const day = String(i + 1).padStart(2, "0");
      return `${monthKey}-${day}`;
    });
    const dayLabels = dateKeys.map((key) => key.slice(-2));

    const counts = Array.from({ length: 24 }, () => new Array(dateKeys.length).fill(0));
    dateKeys.forEach((dateKey, dateIndex) => {
      for (let hour = 0; hour < 24; hour += 1) {
        counts[hour][dateIndex] = metrics[dateKey]?.[hour]?.count || 0;
      }
    });

    const max = Math.max(...counts.flat());
    const cells = [];
    for (let hour = 0; hour < 24; hour += 1) {
      for (let col = 0; col < dateKeys.length; col += 1) {
        const value = counts[hour][col];
        const intensity = max ? value / max : 0;
        const color = `rgba(45, 212, 191, ${0.12 + intensity * 0.7})`;
        const detail = metrics[dateKeys[col]]?.[hour];
        const tokens = detail ? formatNumber(detail.tokens) : "0";
        const cost = detail ? formatMoney(detail.cost) : formatMoney(0);
        const label = `${dateKeys[col]} ${hour.toString().padStart(2, "0")}:00`;
        cells.push(
          `<div class="heatmap-cell" style="background: ${color}" title="${label} • ${value} req • ${tokens} tokens • ${cost}"></div>`
        );
      }
    }

    const monthLabel = new Date(year, monthIndex, 1).toLocaleString(undefined, {
      month: "long",
      year: "numeric",
    });

    return `
      <div class="heatmap-month" style="--heatmap-cols: ${dateKeys.length}">
        <div class="heatmap-title">${monthLabel}</div>
        <div class="heatmap-days">
          <span class="heatmap-corner"></span>
          ${dayLabels.map((day) => `<span>${day}</span>`).join("")}
        </div>
        <div class="heatmap-body">
          <div class="heatmap-hours">
            ${Array.from({ length: 24 }, (_, hour) => `<span>${hour.toString().padStart(2, "0")}</span>`).join("")}
          </div>
          <div class="heatmap-grid">${cells.join("")}</div>
        </div>
      </div>
    `;
  });

  heatmap.innerHTML = `
    <div class="heatmap-scroll">
      ${monthBlocks.join("")}
    </div>
  `;
}

function baseChartOptions() {
  return {
    responsive: true,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: { ticks: { color: "#b9c1bf" }, grid: { color: "rgba(255,255,255,0.04)" } },
      y: { ticks: { color: "#b9c1bf" }, grid: { color: "rgba(255,255,255,0.04)" } },
    },
  };
}

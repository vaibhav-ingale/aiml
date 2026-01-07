export async function api(path, options = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
  const response = await fetch(`/api/${path}`, { ...options, headers });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }
  if (response.status === 204) return null;
  return response.json();
}

export function formatNumber(value) {
  const num = Number(value || 0);
  return num.toLocaleString();
}

export function formatMoney(value, digits = 4) {
  const num = Number(value || 0);
  return `$${num.toFixed(digits)}`;
}

export function formatPercent(value, digits = 1) {
  const num = Number(value || 0);
  return `${num.toFixed(digits)}%`;
}

export function formatDate(value) {
  if (!value) return "-";
  const date = parseLocalDate(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString();
}

function parseLocalDate(value) {
  const parts = String(value).split(/[- :T]/).map(Number);
  if (parts.length >= 3 && parts.every((part) => Number.isFinite(part))) {
    const [year, month, day, hour, minute, second] = parts;
    return new Date(year, month - 1, day, hour || 0, minute || 0, second || 0);
  }
  return new Date(value);
}

export function buildTable(headers, rows) {
  const head = headers.map((label) => `<th>${label}</th>`).join("");
  const body = rows
    .map((cols) => `<tr>${cols.map((col) => `<td>${col}</td>`).join("")}</tr>`)
    .join("");
  return `
    <table>
      <thead><tr>${head}</tr></thead>
      <tbody>${body || `<tr><td colspan=\"${headers.length}\">No data</td></tr>`}</tbody>
    </table>
  `;
}

export function groupBy(items, keyFn) {
  return items.reduce((acc, item) => {
    const key = keyFn(item);
    acc[key] = acc[key] || [];
    acc[key].push(item);
    return acc;
  }, {});
}

export function sumBy(items, key) {
  return items.reduce((acc, item) => acc + Number(item[key] || 0), 0);
}

export function binValues(values, bins) {
  if (!values.length) return { labels: [], counts: [] };
  const min = Math.min(...values);
  const max = Math.max(...values);
  const width = (max - min) / bins || 1;
  const counts = new Array(bins).fill(0);
  values.forEach((value) => {
    const index = Math.min(bins - 1, Math.floor((value - min) / width));
    counts[index] += 1;
  });
  const labels = counts.map((_, index) => {
    const start = min + index * width;
    const end = start + width;
    return `${start.toFixed(2)}-${end.toFixed(2)}`;
  });
  return { labels, counts };
}

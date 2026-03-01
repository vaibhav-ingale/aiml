import { api, formatNumber, formatMoney, formatDate } from "../lib.js";

let currentPage = 0;
let pageSize = 50;
let totalTraces = 0;
let selectedTraces = new Set();

export function renderTraces() {
  return `
    <div class="page-header">
      <div>
        <h1>Traces</h1>
        <p>View detailed request and response traces</p>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <h2>Request Traces</h2>
        <div class="card-actions">
          <button id="deleteSelected" class="btn-danger" style="display: none;">
            <i class="fa-solid fa-trash"></i> Delete Selected (<span id="selectedCount">0</span>)
          </button>
          <button id="refreshTraces" class="btn-secondary">
            <i class="fa-solid fa-rotate"></i> Refresh
          </button>
          <button id="clearAllTraces" class="btn-danger">
            <i class="fa-solid fa-trash"></i> Clear All Traces
          </button>
        </div>
      </div>
      <div id="tracesTable"></div>
      <div class="pagination" id="tracesPagination"></div>
    </div>
    <div id="traceModal" class="modal">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h2>Trace Details</h2>
          <button class="modal-close" id="closeModal">&times;</button>
        </div>
        <div class="modal-body" id="traceDetails"></div>
      </div>
    </div>
  `;
}

export async function afterRenderTraces() {
  selectedTraces.clear();
  updateSelectionUI();
  await loadTraces();

  document.getElementById("refreshTraces")?.addEventListener("click", async () => {
    currentPage = 0;
    selectedTraces.clear();
    await loadTraces();
  });

  document.getElementById("deleteSelected")?.addEventListener("click", async () => {
    const count = selectedTraces.size;
    if (
      confirm(
        `⚠️ WARNING: This will permanently delete ${count} selected trace${count > 1 ? 's' : ''} from the database.\n\nThis action cannot be undone!\n\nAre you sure you want to continue?`
      )
    ) {
      try {
        await api("traces/delete-multiple", {
          method: "DELETE",
          body: JSON.stringify({ traceIds: Array.from(selectedTraces) }),
        });
        selectedTraces.clear();
        await loadTraces();
        alert(`✓ ${count} trace${count > 1 ? 's have' : ' has'} been deleted successfully.`);
      } catch (error) {
        alert(`Failed to delete traces: ${error.message}`);
      }
    }
  });

  document.getElementById("clearAllTraces")?.addEventListener("click", async () => {
    if (
      confirm(
        "⚠️ WARNING: This will permanently delete ALL traces from the database.\n\nThis action cannot be undone!\n\nAre you sure you want to continue?"
      )
    ) {
      try {
        await api("traces/clear", { method: "DELETE" });
        currentPage = 0;
        selectedTraces.clear();
        await loadTraces();
        alert("✓ All traces have been cleared successfully.");
      } catch (error) {
        alert(`Failed to clear traces: ${error.message}`);
      }
    }
  });

  document.getElementById("closeModal")?.addEventListener("click", closeModal);
  document.getElementById("traceModal")?.addEventListener("click", (e) => {
    if (e.target.id === "traceModal") closeModal();
  });
}

async function loadTraces() {
  try {
    const offset = currentPage * pageSize;
    const data = await api(`traces?limit=${pageSize}&offset=${offset}`);
    totalTraces = data.total;
    renderTracesTable(data.traces);
    renderPagination();
  } catch (error) {
    console.error("Failed to load traces:", error);
    document.getElementById("tracesTable").innerHTML = `
      <div class="error-message">Failed to load traces: ${error.message}</div>
    `;
  }
}

function renderTracesTable(traces) {
  const tableHtml = `
    <table>
      <thead>
        <tr>
          <th style="width: 40px;">
            <input type="checkbox" id="selectAllTraces" class="trace-checkbox-header" />
          </th>
          <th>Trace ID</th>
          <th>Timestamp</th>
          <th>Model</th>
          <th>Request Tokens</th>
          <th>Response Tokens</th>
          <th>Total Tokens</th>
          <th>Execution Time</th>
          <th>Cost</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        ${
          traces.length > 0
            ? traces
                .map(
                  (trace) => {
                    const displayId = trace.trace_id || `#${trace.id}`;
                    const lookupId = trace.trace_id || trace.id;
                    const isChecked = selectedTraces.has(lookupId);
                    return `
            <tr class="trace-row" data-trace-id="${lookupId}">
              <td onclick="event.stopPropagation()">
                <input type="checkbox" class="trace-checkbox" data-trace-id="${lookupId}" ${isChecked ? "checked" : ""} />
              </td>
              <td class="trace-id-cell" style="cursor: pointer;">
                <code class="trace-id">${displayId}</code>
              </td>
              <td class="trace-clickable" style="cursor: pointer;">${formatDate(trace.timestamp)}</td>
              <td class="trace-clickable" style="cursor: pointer;">${trace.model_name || "-"}</td>
              <td class="trace-clickable" style="cursor: pointer;">${formatNumber(trace.input_tokens)}</td>
              <td class="trace-clickable" style="cursor: pointer;">${formatNumber(trace.output_tokens)}</td>
              <td class="trace-clickable" style="cursor: pointer;">${formatNumber(trace.total_tokens)}</td>
              <td class="trace-clickable" style="cursor: pointer;">${trace.response_time ? (trace.response_time * 1000).toFixed(2) + " ms" : "-"}</td>
              <td class="trace-clickable" style="cursor: pointer;">${formatMoney(trace.cost)}</td>
              <td class="trace-clickable" style="cursor: pointer;">
                <span class="status-badge status-${trace.status || "unknown"}">
                  ${trace.status || "unknown"}
                </span>
              </td>
            </tr>
          `;
                  }
                )
                .join("")
            : '<tr><td colspan="10" style="text-align: center;">No traces found</td></tr>'
        }
      </tbody>
    </table>
  `;

  document.getElementById("tracesTable").innerHTML = tableHtml;

  // Add select all checkbox handler
  document.getElementById("selectAllTraces")?.addEventListener("change", (e) => {
    const isChecked = e.target.checked;
    document.querySelectorAll(".trace-checkbox").forEach((checkbox) => {
      checkbox.checked = isChecked;
      const traceId = checkbox.getAttribute("data-trace-id");
      if (isChecked) {
        selectedTraces.add(traceId);
      } else {
        selectedTraces.delete(traceId);
      }
    });
    updateSelectionUI();
  });

  // Add individual checkbox handlers
  document.querySelectorAll(".trace-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", (e) => {
      const traceId = e.target.getAttribute("data-trace-id");
      if (e.target.checked) {
        selectedTraces.add(traceId);
      } else {
        selectedTraces.delete(traceId);
        document.getElementById("selectAllTraces").checked = false;
      }
      updateSelectionUI();
    });
  });

  // Add click handlers to trace rows (excluding checkbox column)
  document.querySelectorAll(".trace-clickable, .trace-id-cell").forEach((cell) => {
    cell.addEventListener("click", async () => {
      const row = cell.closest(".trace-row");
      const traceId = row.getAttribute("data-trace-id");
      await showTraceDetails(traceId);
    });
  });
}

function renderPagination() {
  const totalPages = Math.ceil(totalTraces / pageSize);
  const maxVisiblePages = 5;

  let startPage = Math.max(0, currentPage - Math.floor(maxVisiblePages / 2));
  let endPage = Math.min(totalPages - 1, startPage + maxVisiblePages - 1);

  if (endPage - startPage < maxVisiblePages - 1) {
    startPage = Math.max(0, endPage - maxVisiblePages + 1);
  }

  const paginationHtml = `
    <div class="pagination-info">
      Showing ${currentPage * pageSize + 1} - ${Math.min((currentPage + 1) * pageSize, totalTraces)} of ${totalTraces} traces
    </div>
    <div class="pagination-controls">
      <button
        class="btn-secondary"
        ${currentPage === 0 ? "disabled" : ""}
        id="firstPage"
      >
        <i class="fa-solid fa-angles-left"></i>
      </button>
      <button
        class="btn-secondary"
        ${currentPage === 0 ? "disabled" : ""}
        id="prevPage"
      >
        <i class="fa-solid fa-angle-left"></i>
      </button>
      ${Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i)
        .map(
          (page) => `
        <button
          class="btn-secondary ${page === currentPage ? "active" : ""}"
          data-page="${page}"
        >
          ${page + 1}
        </button>
      `
        )
        .join("")}
      <button
        class="btn-secondary"
        ${currentPage >= totalPages - 1 ? "disabled" : ""}
        id="nextPage"
      >
        <i class="fa-solid fa-angle-right"></i>
      </button>
      <button
        class="btn-secondary"
        ${currentPage >= totalPages - 1 ? "disabled" : ""}
        id="lastPage"
      >
        <i class="fa-solid fa-angles-right"></i>
      </button>
    </div>
  `;

  document.getElementById("tracesPagination").innerHTML = paginationHtml;

  document.getElementById("firstPage")?.addEventListener("click", async () => {
    currentPage = 0;
    await loadTraces();
  });

  document.getElementById("prevPage")?.addEventListener("click", async () => {
    if (currentPage > 0) {
      currentPage--;
      await loadTraces();
    }
  });

  document.getElementById("nextPage")?.addEventListener("click", async () => {
    if (currentPage < totalPages - 1) {
      currentPage++;
      await loadTraces();
    }
  });

  document.getElementById("lastPage")?.addEventListener("click", async () => {
    currentPage = totalPages - 1;
    await loadTraces();
  });

  document.querySelectorAll("[data-page]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      currentPage = Number(btn.getAttribute("data-page"));
      await loadTraces();
    });
  });
}

async function showTraceDetails(traceId) {
  try {
    const trace = await api(`traces/${traceId}`);

    const displayId = trace.trace_id || `#${trace.id}`;
    const detailsHtml = `
      <div class="trace-details">
        <div class="trace-section">
          <h3>Overview</h3>
          <div class="trace-grid">
            <div class="trace-field">
              <label>Trace ID:</label>
              <code>${displayId}</code>
            </div>
            <div class="trace-field">
              <label>Session ID:</label>
              <code>${trace.session_id || "-"}</code>
            </div>
            <div class="trace-field">
              <label>Timestamp:</label>
              <span>${formatDate(trace.timestamp)}</span>
            </div>
            <div class="trace-field">
              <label>Model:</label>
              <span>${trace.model_name || "-"}</span>
            </div>
            <div class="trace-field">
              <label>Execution Time:</label>
              <span>${trace.response_time ? (trace.response_time * 1000).toFixed(2) + " ms" : "-"}</span>
            </div>
            <div class="trace-field">
              <label>Status:</label>
              <span class="status-badge status-${trace.status || "unknown"}">${trace.status || "unknown"}</span>
            </div>
            <div class="trace-field">
              <label>Request Tokens:</label>
              <span>${formatNumber(trace.input_tokens)}</span>
            </div>
            <div class="trace-field">
              <label>Response Tokens:</label>
              <span>${formatNumber(trace.output_tokens)}</span>
            </div>
            <div class="trace-field">
              <label>Total Tokens:</label>
              <span>${formatNumber(trace.total_tokens)}</span>
            </div>
            <div class="trace-field">
              <label>Cost:</label>
              <span>${formatMoney(trace.cost)}</span>
            </div>
            ${trace.temperature ? `
            <div class="trace-field">
              <label>Temperature:</label>
              <span>${trace.temperature}</span>
            </div>
            ` : ''}
            ${trace.stream_setting ? `
            <div class="trace-field">
              <label>Stream:</label>
              <span>${trace.stream_setting}</span>
            </div>
            ` : ''}
          </div>
        </div>

        ${trace.error_message ? `
        <div class="trace-section">
          <h3>Error</h3>
          <div class="trace-code error-message">
            ${escapeHtml(trace.error_message)}
          </div>
        </div>
        ` : ''}

        ${trace.request_payload ? `
        <div class="trace-section">
          <h3>Request Payload</h3>
          <pre class="trace-code"><code>${escapeHtml(JSON.stringify(trace.request_payload, null, 2))}</code></pre>
        </div>
        ` : ''}

        ${trace.system_message ? `
        <div class="trace-section">
          <h3>System Message</h3>
          <div class="trace-code">
            ${escapeHtml(trace.system_message)}
          </div>
        </div>
        ` : ''}

        ${trace.user_message ? `
        <div class="trace-section">
          <h3>User Message</h3>
          <div class="trace-code">
            ${escapeHtml(trace.user_message)}
          </div>
        </div>
        ` : ''}

        ${trace.assistant_message ? `
        <div class="trace-section">
          <h3>Assistant Message</h3>
          <div class="trace-code">
            ${escapeHtml(trace.assistant_message)}
          </div>
        </div>
        ` : ''}

        ${trace.assistant_tool_calls ? `
        <div class="trace-section">
          <h3>Tool Calls</h3>
          <pre class="trace-code"><code>${escapeHtml(JSON.stringify(trace.assistant_tool_calls, null, 2))}</code></pre>
        </div>
        ` : ''}

        ${trace.tool_responses ? `
        <div class="trace-section">
          <h3>Tool Responses</h3>
          <pre class="trace-code"><code>${escapeHtml(JSON.stringify(trace.tool_responses, null, 2))}</code></pre>
        </div>
        ` : ''}

        ${trace.response_payload ? `
        <div class="trace-section">
          <h3>Response Payload</h3>
          <pre class="trace-code"><code>${escapeHtml(JSON.stringify(trace.response_payload, null, 2))}</code></pre>
        </div>
        ` : ''}
      </div>
    `;

    document.getElementById("traceDetails").innerHTML = detailsHtml;
    document.getElementById("traceModal").style.display = "flex";
  } catch (error) {
    console.error("Failed to load trace details:", error);
    alert(`Failed to load trace details: ${error.message}`);
  }
}

function closeModal() {
  document.getElementById("traceModal").style.display = "none";
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function updateSelectionUI() {
  const count = selectedTraces.size;
  const deleteButton = document.getElementById("deleteSelected");
  const countSpan = document.getElementById("selectedCount");

  if (deleteButton && countSpan) {
    countSpan.textContent = count;
    deleteButton.style.display = count > 0 ? "inline-flex" : "none";
  }
}

import { api, formatNumber, formatMoney, formatDate, showNotification, showConfirm } from "../lib.js";

console.log('🔧 Traces.js loaded - Tool column support enabled v2');

let currentPage = 0;
let pageSize = 50;
let totalTraces = 0;
let selectedTraces = new Set();
let currentSessionFilter = null;
let availableSessions = [];

// Column visibility configuration
const DEFAULT_COLUMNS = {
  checkbox: true,
  trace_id: true,
  session_id: true,
  timestamp: true,
  model: true,
  tool_name: true,
  user_message: false,
  assistant_message: false,
  input_tokens: true,
  output_tokens: true,
  total_tokens: true,
  execution_time: true,
  cost: true,
  status: true
};

let visibleColumns = { ...DEFAULT_COLUMNS };

// Load saved column preferences from localStorage
try {
  const saved = localStorage.getItem('traces_columns');
  if (saved) {
    const savedColumns = JSON.parse(saved);
    // Merge saved with defaults, ensuring new columns get their default value
    visibleColumns = { ...DEFAULT_COLUMNS, ...savedColumns };
    // Save merged version to ensure new columns are persisted
    localStorage.setItem('traces_columns', JSON.stringify(visibleColumns));
  }
} catch (e) {
  console.error('Failed to load column preferences:', e);
}

function saveColumnPreferences() {
  try {
    localStorage.setItem('traces_columns', JSON.stringify(visibleColumns));
  } catch (e) {
    console.error('Failed to save column preferences:', e);
  }
}

// Make filterBySession available globally
window.filterBySession = function(sessionId) {
  currentSessionFilter = sessionId;
  currentPage = 0;
  loadTraces();

  // Show filter badge with full session ID
  const filterBadge = document.getElementById("sessionFilterBadge");
  const filterText = document.getElementById("sessionFilterText");
  const showAllBtn = document.getElementById("showAllTraces");

  if (filterBadge && filterText) {
    filterText.textContent = sessionId;
    filterBadge.style.display = "flex";
  }

  if (showAllBtn) {
    showAllBtn.style.display = "inline-flex";
  }
};

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
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
          <h2>Request Traces</h2>
          <div style="display: flex; align-items: center; gap: 8px;">
            <label for="sessionFilter" style="font-size: 13px; color: var(--muted); white-space: nowrap;">
              <i class="fa-solid fa-filter"></i> Session:
            </label>
            <select id="sessionFilter" style="min-width: 200px; max-width: 300px; padding: 6px 10px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; color: var(--text); font-size: 13px; cursor: pointer;">
              <option value="">All Sessions</option>
            </select>
          </div>
        </div>
        <div class="card-actions">
          <button id="columnSettings" class="btn-secondary">
            <i class="fa-solid fa-columns"></i> Columns
          </button>
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

    <!-- Column Settings Modal -->
    <div id="columnModal" class="modal" style="display: none;">
      <div class="modal-content" style="max-width: 650px;">
        <div class="modal-header">
          <h2><i class="fa-solid fa-columns"></i> Customize Columns</h2>
          <button id="closeColumnModal" class="modal-close">&times;</button>
        </div>
        <div class="modal-body" style="max-height: 600px; overflow-y: auto;">
          <p style="color: #8b949e; margin-bottom: 20px; font-size: 14px;">
            <i class="fa-solid fa-circle-info" style="color: #58a6ff;"></i>
            Select which columns to display in the traces table. Click any column to toggle visibility.
          </p>
          <div id="columnCheckboxes"></div>
        </div>
      </div>
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
  currentSessionFilter = null;
  updateSelectionUI();
  await loadSessions();
  await loadTraces();

  document.getElementById("refreshTraces")?.addEventListener("click", async () => {
    currentPage = 0;
    selectedTraces.clear();
    await loadSessions();
    await loadTraces();
  });

  // Session filter change handler
  document.getElementById("sessionFilter")?.addEventListener("change", async (e) => {
    const selectedSession = e.target.value;
    currentSessionFilter = selectedSession || null;
    currentPage = 0;
    selectedTraces.clear();
    await loadTraces();
  });

  document.getElementById("deleteSelected")?.addEventListener("click", async () => {
    const count = selectedTraces.size;
    showConfirm(
      'Delete Selected Traces',
      `This will permanently delete ${count} selected trace${count > 1 ? 's' : ''} from the database.\n\nThis action cannot be undone!\n\nAre you sure you want to continue?`,
      async () => {
        try {
          await api("traces/delete-multiple", {
            method: "DELETE",
            body: JSON.stringify({ traceIds: Array.from(selectedTraces) }),
          });
          selectedTraces.clear();
          await loadTraces();
          updateSelectionUI();
          showNotification(`${count} trace${count > 1 ? 's have' : ' has'} been deleted successfully`, 'success');
        } catch (error) {
          showNotification(`Failed to delete traces: ${error.message}`, 'error');
        }
      }
    );
  });

  document.getElementById("clearAllTraces")?.addEventListener("click", async () => {
    showConfirm(
      'Clear All Traces',
      'This will permanently delete ALL traces from the database.\n\nThis action cannot be undone!\n\nAre you sure you want to continue?',
      async () => {
        try {
          await api("traces/clear", { method: "DELETE" });
          currentPage = 0;
          selectedTraces.clear();
          await loadTraces();
          showNotification('All traces have been cleared successfully', 'success');
        } catch (error) {
          showNotification(`Failed to clear traces: ${error.message}`, 'error');
        }
      }
    );
  });

  document.getElementById("closeModal")?.addEventListener("click", closeModal);
  document.getElementById("traceModal")?.addEventListener("click", (e) => {
    if (e.target.id === "traceModal") closeModal();
  });

  // Column settings modal
  document.getElementById("columnSettings")?.addEventListener("click", openColumnSettings);
  document.getElementById("closeColumnModal")?.addEventListener("click", closeColumnSettings);
  document.getElementById("columnModal")?.addEventListener("click", (e) => {
    if (e.target.id === "columnModal") closeColumnSettings();
  });

  // ESC key to close modals
  document.addEventListener("keydown", handleEscKey);
}

function handleEscKey(e) {
  if (e.key === "Escape") {
    // Check which modal is open and close it
    const traceModal = document.getElementById("traceModal");
    const columnModal = document.getElementById("columnModal");

    if (traceModal && traceModal.style.display === "flex") {
      closeModal();
    } else if (columnModal && columnModal.style.display === "flex") {
      closeColumnSettings();
    }
  }
}

function openColumnSettings() {
  const columnGroups = {
    'Basic Information': [
      { key: 'checkbox', label: 'Checkbox', icon: 'fa-square-check', disabled: true },
      { key: 'trace_id', label: 'Trace ID', icon: 'fa-fingerprint' },
      { key: 'session_id', label: 'Session ID', icon: 'fa-layer-group' },
      { key: 'timestamp', label: 'Timestamp', icon: 'fa-clock' },
      { key: 'model', label: 'Model', icon: 'fa-microchip' },
      { key: 'tool_name', label: 'Tool Name', icon: 'fa-wrench' },
      { key: 'status', label: 'Status', icon: 'fa-circle-check' }
    ],
    'Messages': [
      { key: 'user_message', label: 'Request Text', icon: 'fa-comment-dots' },
      { key: 'assistant_message', label: 'Response Text', icon: 'fa-comment' }
    ],
    'Metrics': [
      { key: 'input_tokens', label: 'Request Tokens', icon: 'fa-arrow-right' },
      { key: 'output_tokens', label: 'Response Tokens', icon: 'fa-arrow-left' },
      { key: 'total_tokens', label: 'Total Tokens', icon: 'fa-hashtag' },
      { key: 'execution_time', label: 'Execution Time', icon: 'fa-stopwatch' },
      { key: 'cost', label: 'Cost', icon: 'fa-dollar-sign' }
    ]
  };

  const checkboxesHtml = Object.entries(columnGroups).map(([groupName, columns]) => `
    <div class="column-group">
      <div class="column-group-title">${groupName}</div>
      <div class="column-group-items">
        ${columns.map(col => {
          const isChecked = visibleColumns[col.key];
          const isDisabled = col.disabled || false;
          return `
            <label class="column-toggle ${isDisabled ? 'disabled' : ''} ${isChecked ? 'checked' : ''}">
              <input
                type="checkbox"
                data-column="${col.key}"
                ${isChecked ? 'checked' : ''}
                ${isDisabled ? 'disabled' : ''}
              />
              <div class="column-toggle-content">
                <i class="fa-solid ${col.icon}"></i>
                <span class="column-label">${col.label}</span>
                <i class="fa-solid fa-check column-check"></i>
              </div>
            </label>
          `;
        }).join('')}
      </div>
    </div>
  `).join('');

  document.getElementById('columnCheckboxes').innerHTML = checkboxesHtml;
  document.getElementById('columnModal').style.display = 'flex';

  // Add change listeners
  document.querySelectorAll('#columnCheckboxes input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      const column = e.target.dataset.column;
      visibleColumns[column] = e.target.checked;
      saveColumnPreferences();

      // Update visual state
      const label = e.target.closest('.column-toggle');
      if (e.target.checked) {
        label.classList.add('checked');
      } else {
        label.classList.remove('checked');
      }

      loadTraces(); // Reload table with new columns
    });
  });
}

function closeColumnSettings() {
  document.getElementById('columnModal').style.display = 'none';
}

async function loadSessions() {
  try {
    const sessions = await api('traces/sessions');
    availableSessions = sessions;

    const sessionFilter = document.getElementById('sessionFilter');
    if (sessionFilter) {
      // Save current selection
      const currentSelection = sessionFilter.value;

      // Clear existing options except the first "All Sessions"
      sessionFilter.innerHTML = '<option value="">All Sessions</option>';

      // Add session options
      sessions.forEach(session => {
        const option = document.createElement('option');
        option.value = session.session_id;
        option.textContent = `${session.session_id} (${session.trace_count} trace${session.trace_count > 1 ? 's' : ''})`;
        sessionFilter.appendChild(option);
      });

      // Restore selection if it still exists
      if (currentSelection && sessions.some(s => s.session_id === currentSelection)) {
        sessionFilter.value = currentSelection;
      }
    }
  } catch (error) {
    console.error("Failed to load sessions:", error);
  }
}

async function loadTraces() {
  try {
    const offset = currentPage * pageSize;
    let url = `traces?limit=${pageSize}&offset=${offset}`;
    if (currentSessionFilter) {
      url += `&session_id=${encodeURIComponent(currentSessionFilter)}`;
    }
    const data = await api(url);
    totalTraces = data.total;
    console.log('Loaded traces:', data.traces.length);
    console.log('First trace tool_name:', data.traces[0]?.tool_name);
    console.log('Visible columns:', visibleColumns);
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
  // Define column information
  const columns = [
    { key: 'checkbox', label: '', width: '40px', resizable: false },
    { key: 'trace_id', label: 'Trace ID', width: '200px', resizable: true },
    { key: 'session_id', label: 'Session ID', width: '180px', resizable: true },
    { key: 'timestamp', label: 'Timestamp', width: '180px', resizable: true },
    { key: 'model', label: 'Model', width: '200px', resizable: true },
    { key: 'tool_name', label: 'Tool Name', width: '150px', resizable: true },
    { key: 'user_message', label: 'Request Text', width: '300px', resizable: true },
    { key: 'assistant_message', label: 'Response Text', width: '300px', resizable: true },
    { key: 'input_tokens', label: 'Request Tokens', width: '120px', resizable: true },
    { key: 'output_tokens', label: 'Response Tokens', width: '120px', resizable: true },
    { key: 'total_tokens', label: 'Total Tokens', width: '100px', resizable: true },
    { key: 'execution_time', label: 'Execution Time', width: '120px', resizable: true },
    { key: 'cost', label: 'Cost', width: '100px', resizable: true },
    { key: 'status', label: 'Status', width: '100px', resizable: true }
  ];

  const visibleCols = columns.filter(col => visibleColumns[col.key]);
  const colCount = visibleCols.length;

  const tableHtml = `
    <table class="resizable-table">
      <thead>
        <tr>
          ${visibleCols.map(col => `
            <th style="width: ${col.width}; position: relative;" data-column="${col.key}">
              ${col.key === 'checkbox'
                ? '<input type="checkbox" id="selectAllTraces" class="trace-checkbox-header" />'
                : col.label
              }
              ${col.resizable ? '<div class="column-resizer"></div>' : ''}
            </th>
          `).join('')}
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
                    const sessionDisplay = trace.session_id
                      ? `<code class="trace-id" style="font-size: 10px; cursor: pointer;" onclick="filterBySession('${trace.session_id}')">${trace.session_id}</code>`
                      : "-";

                    const truncateText = (text, maxLen = 100) => {
                      if (!text) return "-";
                      return text.length > maxLen ? text.substring(0, maxLen) + "..." : text;
                    };

                    return `
            <tr class="trace-row" data-trace-id="${lookupId}" data-session-id="${trace.session_id || ''}">
              ${visibleColumns.checkbox ? `
              <td onclick="event.stopPropagation()">
                <input type="checkbox" class="trace-checkbox" data-trace-id="${lookupId}" ${isChecked ? "checked" : ""} />
              </td>
              ` : ''}
              ${visibleColumns.trace_id ? `
              <td class="trace-id-cell" style="cursor: pointer;">
                <code class="trace-id">${displayId}</code>
              </td>
              ` : ''}
              ${visibleColumns.session_id ? `
              <td class="trace-clickable" style="cursor: pointer;">
                ${sessionDisplay}
              </td>
              ` : ''}
              ${visibleColumns.timestamp ? `
              <td class="trace-clickable" style="cursor: pointer;">${formatDate(trace.timestamp)}</td>
              ` : ''}
              ${visibleColumns.model ? `
              <td class="trace-clickable" style="cursor: pointer;">${trace.model_name || "-"}</td>
              ` : ''}
              ${visibleColumns.tool_name ? `
              <td class="trace-clickable" style="cursor: pointer;">
                ${trace.tool_name ? `<span class="tool-badge"><i class="fa-solid fa-wrench"></i> ${trace.tool_name}</span>` : "-"}
              </td>
              ` : ''}
              ${visibleColumns.user_message ? `
              <td class="trace-clickable" style="cursor: pointer; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${trace.user_message || ''}">${truncateText(trace.user_message, 100)}</td>
              ` : ''}
              ${visibleColumns.assistant_message ? `
              <td class="trace-clickable" style="cursor: pointer; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${trace.assistant_message || ''}">${truncateText(trace.assistant_message, 100)}</td>
              ` : ''}
              ${visibleColumns.input_tokens ? `
              <td class="trace-clickable" style="cursor: pointer;">${formatNumber(trace.input_tokens)}</td>
              ` : ''}
              ${visibleColumns.output_tokens ? `
              <td class="trace-clickable" style="cursor: pointer;">${formatNumber(trace.output_tokens)}</td>
              ` : ''}
              ${visibleColumns.total_tokens ? `
              <td class="trace-clickable" style="cursor: pointer;">${formatNumber(trace.total_tokens)}</td>
              ` : ''}
              ${visibleColumns.execution_time ? `
              <td class="trace-clickable" style="cursor: pointer;">${trace.response_time ? (trace.response_time * 1000).toFixed(2) + " ms" : "-"}</td>
              ` : ''}
              ${visibleColumns.cost ? `
              <td class="trace-clickable" style="cursor: pointer;">${formatMoney(trace.cost)}</td>
              ` : ''}
              ${visibleColumns.status ? `
              <td class="trace-clickable" style="cursor: pointer;">
                <span class="status-badge status-${trace.status || "unknown"}">
                  ${trace.status || "unknown"}
                </span>
              </td>
              ` : ''}
            </tr>
          `;
                  }
                )
                .join("")
            : `<tr><td colspan="${colCount}" style="text-align: center;">No traces found</td></tr>`
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

  // Add column resize handlers
  initColumnResizers();
}

function initColumnResizers() {
  const resizers = document.querySelectorAll('.column-resizer');
  let currentResizer = null;
  let currentTh = null;
  let startX = 0;
  let startWidth = 0;

  resizers.forEach(resizer => {
    resizer.addEventListener('mousedown', (e) => {
      currentResizer = resizer;
      currentTh = resizer.parentElement;
      startX = e.pageX;
      startWidth = currentTh.offsetWidth;

      e.preventDefault();
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });
  });

  document.addEventListener('mousemove', (e) => {
    if (currentResizer) {
      const diff = e.pageX - startX;
      const newWidth = Math.max(50, startWidth + diff);
      currentTh.style.width = newWidth + 'px';
    }
  });

  document.addEventListener('mouseup', () => {
    if (currentResizer) {
      currentResizer = null;
      currentTh = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
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
            ${trace.provider_name ? `
            <div class="trace-field">
              <label>Provider:</label>
              <span class="status-badge" style="background: var(--accent-soft); color: var(--accent);">
                <i class="fa-solid fa-server"></i> ${trace.provider_name}
              </span>
            </div>
            ` : ''}
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
            ${trace.tool_name ? `
            <div class="trace-field">
              <label>Tool Name:</label>
              <span class="tool-badge"><i class="fa-solid fa-wrench"></i> ${trace.tool_name}</span>
            </div>
            ` : ''}
            ${trace.tool_call_type ? `
            <div class="trace-field">
              <label>Tool Call Type:</label>
              <span>${trace.tool_call_type}</span>
            </div>
            ` : ''}
          </div>
        </div>

        ${trace.error_message ? `
        <div class="trace-section collapsible-section">
          <h3 class="collapsible-header" onclick="toggleSection(this)">
            <i class="fa-solid fa-chevron-right"></i>
            Error
          </h3>
          <div class="collapsible-content" style="display: none;">
            <div class="trace-code error-message">${escapeHtml(trace.error_message)}</div>
          </div>
        </div>
        ` : ''}

        ${trace.system_message ? `
        <div class="trace-section collapsible-section">
          <h3 class="collapsible-header" onclick="toggleSection(this)">
            <i class="fa-solid fa-chevron-right"></i>
            System Message
          </h3>
          <div class="collapsible-content" style="display: none;">
            <div class="trace-code">${escapeHtml(trace.system_message.trim())}</div>
          </div>
        </div>
        ` : ''}

        ${trace.user_message ? `
        <div class="trace-section collapsible-section">
          <h3 class="collapsible-header" onclick="toggleSection(this)">
            <i class="fa-solid fa-chevron-right"></i>
            User Message
          </h3>
          <div class="collapsible-content" style="display: none;">
            <div class="trace-code">${escapeHtml(trace.user_message.trim())}</div>
          </div>
        </div>
        ` : ''}

        ${trace.assistant_message ? `
        <div class="trace-section collapsible-section">
          <h3 class="collapsible-header" onclick="toggleSection(this)">
            <i class="fa-solid fa-chevron-right"></i>
            Assistant Message
          </h3>
          <div class="collapsible-content" style="display: none;">
            <div class="trace-code">${escapeHtml(trace.assistant_message.trim())}</div>
          </div>
        </div>
        ` : ''}

        ${trace.request_payload ? `
        <div class="trace-section collapsible-section">
          <h3 class="collapsible-header" onclick="toggleSection(this)">
            <i class="fa-solid fa-chevron-right"></i>
            Request Payload
          </h3>
          <div class="collapsible-content" style="display: none;">
            <pre class="trace-code"><code>${escapeHtml(JSON.stringify(trace.request_payload, null, 2))}</code></pre>
          </div>
        </div>
        ` : ''}

        ${trace.assistant_tool_calls ? `
        <div class="trace-section collapsible-section">
          <h3 class="collapsible-header" onclick="toggleSection(this)">
            <i class="fa-solid fa-chevron-right"></i>
            Tool Calls
          </h3>
          <div class="collapsible-content" style="display: none;">
            ${renderToolCalls(trace.assistant_tool_calls)}
          </div>
        </div>
        ` : ''}

        ${trace.tool_responses ? `
        <div class="trace-section collapsible-section">
          <h3 class="collapsible-header" onclick="toggleSection(this)">
            <i class="fa-solid fa-chevron-right"></i>
            Tool Responses
          </h3>
          <div class="collapsible-content" style="display: none;">
            <pre class="trace-code"><code>${escapeHtml(JSON.stringify(trace.tool_responses, null, 2))}</code></pre>
          </div>
        </div>
        ` : ''}

        ${trace.response_payload ? `
        <div class="trace-section collapsible-section">
          <h3 class="collapsible-header" onclick="toggleSection(this)">
            <i class="fa-solid fa-chevron-right"></i>
            Response Payload
          </h3>
          <div class="collapsible-content" style="display: none;">
            <pre class="trace-code"><code>${escapeHtml(JSON.stringify(trace.response_payload, null, 2))}</code></pre>
          </div>
        </div>
        ` : ''}
      </div>
    `;

    document.getElementById("traceDetails").innerHTML = detailsHtml;
    document.getElementById("traceModal").style.display = "flex";
  } catch (error) {
    console.error("Failed to load trace details:", error);
    showNotification(`Failed to load trace details: ${error.message}`, 'error');
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

function renderToolCalls(toolCalls) {
  try {
    const calls = Array.isArray(toolCalls) ? toolCalls : [toolCalls];

    return calls.map((call, index) => {
      const toolName = call.function?.name || call.name || 'Unknown Tool';
      const toolArgs = call.function?.arguments || call.arguments || call.input || '{}';

      // Parse arguments if it's a string
      let parsedArgs;
      try {
        parsedArgs = typeof toolArgs === 'string' ? JSON.parse(toolArgs) : toolArgs;
      } catch {
        parsedArgs = toolArgs;
      }

      return `
        <div style="margin-bottom: ${index < calls.length - 1 ? '20px' : '0'}; padding-bottom: ${index < calls.length - 1 ? '20px' : '0'}; border-bottom: ${index < calls.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none'};">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span class="tool-badge"><i class="fa-solid fa-wrench"></i> ${escapeHtml(toolName)}</span>
            ${call.id ? `<code style="font-size: 10px; color: var(--muted);">ID: ${escapeHtml(call.id)}</code>` : ''}
          </div>
          <div>
            <div style="font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">Parameters:</div>
            <pre class="trace-code"><code>${escapeHtml(JSON.stringify(parsedArgs, null, 2))}</code></pre>
          </div>
        </div>
      `;
    }).join('');
  } catch (error) {
    // Fallback to raw JSON display
    return `<pre class="trace-code"><code>${escapeHtml(JSON.stringify(toolCalls, null, 2))}</code></pre>`;
  }
}

// Make toggleSection available globally for collapsible sections
window.toggleSection = function(headerElement) {
  const section = headerElement.closest('.collapsible-section');
  const content = section.querySelector('.collapsible-content');
  const icon = headerElement.querySelector('i');

  if (content.style.display === 'none') {
    content.style.display = 'block';
    icon.classList.remove('fa-chevron-right');
    icon.classList.add('fa-chevron-down');
  } else {
    content.style.display = 'none';
    icon.classList.remove('fa-chevron-down');
    icon.classList.add('fa-chevron-right');
  }
};

function updateSelectionUI() {
  const count = selectedTraces.size;
  const deleteButton = document.getElementById("deleteSelected");
  const countSpan = document.getElementById("selectedCount");

  if (deleteButton && countSpan) {
    countSpan.textContent = count;
    deleteButton.style.display = count > 0 ? "inline-flex" : "none";
  }
}

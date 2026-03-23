import { api, showNotification, buildTable } from "../lib.js";

export function renderCustomEndpoints() {
  return `
    <div class="page-header">
      <div>
        <h1>Custom Endpoints</h1>
        <p>Create custom API endpoints with configurable models and fallback options.</p>
      </div>
      <button class="primary" id="addEndpointBtn">
        <i class="fa-solid fa-plus"></i> Add Endpoint
      </button>
    </div>

    <div class="card">
      <h3>Configured Endpoints</h3>
      <div class="table-wrap" id="endpointsTable"></div>
    </div>

    <!-- Add/Edit Endpoint Modal -->
    <div id="endpointModal" class="modal" style="display: none;">
      <div class="modal-content" style="max-width: 700px;">
        <div class="modal-header">
          <h3 id="modalTitle">Add Custom Endpoint</h3>
          <button class="close-modal" id="closeModal">&times;</button>
        </div>
        <form id="endpointForm" class="form-grid">
          <input type="hidden" id="endpointId" />
          <div>
            <label for="endpointName">Endpoint Name</label>
            <input
              id="endpointName"
              name="endpoint_name"
              type="text"
              placeholder="e.g., My Custom API"
              required
            />
          </div>
          <div>
            <label for="endpointPath">Endpoint Path</label>
            <input
              id="endpointPath"
              name="endpoint_path"
              type="text"
              placeholder="e.g., /custom/my-api"
              required
            />
            <small style="color: var(--muted); font-size: 0.875rem;">
              Must start with /. This is the path you'll use to access this endpoint.
            </small>
          </div>
          <div>
            <label for="endpointApiKey">API Key <span style="color: var(--danger);">*</span></label>
            <select id="endpointApiKey" name="api_key" required>
              <option value="">Select API key...</option>
            </select>
            <small style="color: var(--muted); font-size: 0.875rem;">
              Select an existing LLM Gateway API key. This key will be used for authentication when calling this endpoint.
            </small>
          </div>
          <div>
            <label for="primaryModel">Primary Model</label>
            <select id="primaryModel" name="primary_model" required>
              <option value="">Select primary model...</option>
            </select>
            <small style="color: var(--muted); font-size: 0.875rem;">
              The main model that will handle requests to this endpoint.
            </small>
          </div>
          <div>
            <label for="fallbackModel">Fallback Model (Optional)</label>
            <select id="fallbackModel" name="fallback_model">
              <option value="">No fallback</option>
            </select>
            <small style="color: var(--muted); font-size: 0.875rem;">
              Model to use if primary model fails or is unavailable.
            </small>
          </div>
          <div class="button-row">
            <button class="primary" type="submit">
              <i class="fa-solid fa-save"></i> Save Endpoint
            </button>
            <button class="secondary" type="button" id="cancelBtn">
              Cancel
            </button>
          </div>
        </form>
        <div id="modalNotice" class="notice" style="display: none;"></div>
      </div>
    </div>

    <!-- Endpoint Details Modal -->
    <div id="detailsModal" class="modal" style="display: none;">
      <div class="modal-content" style="max-width: 800px;">
        <div class="modal-header">
          <h3 id="detailsTitle">Endpoint Details</h3>
          <button class="close-modal" id="closeDetailsModal">&times;</button>
        </div>
        <div id="detailsContent"></div>
      </div>
    </div>
  `;
}

export async function afterRenderCustomEndpoints() {
  const endpointsTable = document.querySelector("#endpointsTable");
  const addEndpointBtn = document.querySelector("#addEndpointBtn");
  const endpointModal = document.querySelector("#endpointModal");
  const detailsModal = document.querySelector("#detailsModal");
  const endpointForm = document.querySelector("#endpointForm");
  const closeModal = document.querySelector("#closeModal");
  const closeDetailsModal = document.querySelector("#closeDetailsModal");
  const cancelBtn = document.querySelector("#cancelBtn");
  const modalNotice = document.querySelector("#modalNotice");
  const modalTitle = document.querySelector("#modalTitle");
  const primaryModelSelect = document.querySelector("#primaryModel");
  const fallbackModelSelect = document.querySelector("#fallbackModel");
  const apiKeySelect = document.querySelector("#endpointApiKey");

  let editingEndpointId = null;
  let availableModels = [];
  let availableApiKeys = [];
  let selectedApiKeyAllowedModels = [];

  // Load available models
  const loadModels = async () => {
    try {
      const models = await api("models");
      availableModels = models.filter((m) => m.is_active);
      updateModelDropdowns();
    } catch (error) {
      showNotification(`Failed to load models: ${error.message}`, "error");
    }
  };

  // Update model dropdowns based on selected API key
  const updateModelDropdowns = () => {
    // Populate model dropdowns
    primaryModelSelect.innerHTML = '<option value="">Select primary model...</option>';
    fallbackModelSelect.innerHTML = '<option value="">No fallback</option>';

    // Filter models based on selected API key's allowed models
    const filteredModels = availableModels.filter((model) => {
      // If no API key selected or API key allows all models, show all
      if (selectedApiKeyAllowedModels.length === 0 ||
          selectedApiKeyAllowedModels.includes("*") ||
          selectedApiKeyAllowedModels.includes("* (All Models)")) {
        return true;
      }
      // Otherwise, only show models allowed by the API key
      return selectedApiKeyAllowedModels.includes(model.model_name);
    });

    if (filteredModels.length === 0 && selectedApiKeyAllowedModels.length > 0) {
      primaryModelSelect.innerHTML = '<option value="">No models available for this API key</option>';
      fallbackModelSelect.innerHTML = '<option value="">No models available</option>';
      return;
    }

    filteredModels.forEach((model) => {
      const option = document.createElement("option");
      option.value = model.model_name;
      option.textContent = `${model.model_name} (${model.provider_name || "unknown"})`;
      primaryModelSelect.appendChild(option.cloneNode(true));
      fallbackModelSelect.appendChild(option.cloneNode(true));
    });
  };

  // Load available API keys
  const loadApiKeys = async () => {
    try {
      const apiKeys = await api("api-keys");
      // Include both active and inactive keys, but mark them
      availableApiKeys = apiKeys;

      // Populate API key dropdown
      apiKeySelect.innerHTML = '<option value="">Select API key...</option>';

      availableApiKeys.forEach((key) => {
        const option = document.createElement("option");
        option.value = key.api_key;
        option.dataset.allowedModels = JSON.stringify(key.allowed_models);
        option.dataset.isActive = key.is_active;

        // Calculate quota usage percentage
        const quotaPercent = key.cost_limit > 0
          ? Math.round((key.current_cost / key.cost_limit) * 100)
          : 0;

        // Show masked key with username, status, and quota
        const maskedKey = key.api_key.substring(0, 10) + '...' + key.api_key.slice(-4);
        const status = key.is_active ? '✓' : '✗';
        const quotaInfo = key.cost_limit > 0 ? ` [${quotaPercent}%]` : ' [∞]';

        option.textContent = `${status} ${maskedKey} (${key.username})${quotaInfo}`;

        // Disable option if key is inactive or quota exceeded
        if (!key.is_active || (key.cost_limit > 0 && key.current_cost >= key.cost_limit)) {
          option.disabled = true;
          option.textContent += ' - Unavailable';
        }

        apiKeySelect.appendChild(option);
      });
    } catch (error) {
      showNotification(`Failed to load API keys: ${error.message}`, "error");
    }
  };

  // Load endpoints
  const loadEndpoints = async () => {
    try {
      const endpoints = await api("custom-endpoints");

      if (endpoints.length === 0) {
        endpointsTable.innerHTML = `<div class="empty">No custom endpoints configured. Click "Add Endpoint" to get started.</div>`;
        return;
      }

      const rows = endpoints.map((endpoint) => {
        const statusIcon = endpoint.is_active
          ? '<i class="fa-solid fa-circle-check" style="color: var(--accent);"></i>'
          : '<i class="fa-solid fa-circle-xmark" style="color: var(--muted);"></i>';

        return [
          endpoint.endpoint_name,
          `<code style="background: var(--code-bg); padding: 2px 6px; border-radius: 4px;">${endpoint.endpoint_path}</code>`,
          endpoint.primary_model,
          endpoint.fallback_model || '<span style="color: var(--muted);">None</span>',
          statusIcon,
          `<div class="button-row">
            <button class="secondary btn-sm" data-action="view" data-id="${endpoint.id}">
              <i class="fa-solid fa-eye"></i> View
            </button>
            <button class="secondary btn-sm" data-action="edit" data-id="${endpoint.id}">
              <i class="fa-solid fa-edit"></i> Edit
            </button>
            <button class="danger btn-sm" data-action="delete" data-id="${endpoint.id}">
              <i class="fa-solid fa-trash"></i> Delete
            </button>
          </div>`,
        ];
      });

      endpointsTable.innerHTML = buildTable(
        ["Name", "Path", "Primary Model", "Fallback Model", "Active", "Actions"],
        rows
      );

      // Attach event listeners to action buttons
      endpointsTable.querySelectorAll("button[data-action]").forEach((button) => {
        button.addEventListener("click", async (e) => {
          e.preventDefault();
          const action = button.dataset.action;
          const id = Number(button.dataset.id);

          if (action === "view") {
            await viewEndpointDetails(id);
          } else if (action === "edit") {
            await editEndpoint(id);
          } else if (action === "delete") {
            await deleteEndpoint(id);
          }
        });
      });
    } catch (error) {
      endpointsTable.innerHTML = `<div class="empty error">${error.message}</div>`;
    }
  };

  // View endpoint details
  const viewEndpointDetails = async (endpointId) => {
    try {
      const endpoint = await api(`custom-endpoints/${endpointId}`);

      // Create the curl command with API key
      const curlCommand = `curl ${window.location.protocol}//${window.location.hostname}:8008${endpoint.endpoint_path}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${endpoint.api_key}" \\
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}]
  }'`;

      document.querySelector("#detailsTitle").textContent = `${endpoint.endpoint_name} - Details`;
      document.querySelector("#detailsContent").innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <strong>Endpoint Path:</strong>
            <div style="margin-top: 0.5rem;">
              <code style="background: var(--code-bg); padding: 8px 12px; border-radius: 4px; display: inline-block;">
                ${window.location.protocol}//${window.location.hostname}:8008${endpoint.endpoint_path}
              </code>
            </div>
          </div>
          <div>
            <strong>API Key:</strong> ${endpoint.api_key_masked}
          </div>
          <div>
            <strong>Primary Model:</strong> ${endpoint.primary_model}
          </div>
          <div>
            <strong>Fallback Model:</strong> ${endpoint.fallback_model || '<span style="color: var(--muted);">None</span>'}
          </div>
          <div>
            <strong>Active:</strong> ${endpoint.is_active ? "Yes" : "No"}
          </div>
          <div>
            <strong>Created:</strong> ${endpoint.created_at}
          </div>
          <div>
            <strong>Last Updated:</strong> ${endpoint.updated_at}
          </div>
          <div style="margin-top: 1rem; padding: 1rem; background: var(--code-bg); border-radius: 8px; position: relative;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
              <strong>Usage Example:</strong>
              <button
                id="copyCurlBtn"
                class="secondary btn-sm"
                style="padding: 4px 12px;"
                title="Copy curl command">
                <i class="fa-solid fa-copy"></i> Copy
              </button>
            </div>
            <pre style="margin: 0; overflow-x: auto;"><code id="curlCommand">${curlCommand}</code></pre>
          </div>
        </div>
      `;

      detailsModal.style.display = "flex";

      // Add copy button event listener
      const copyCurlBtn = document.querySelector("#copyCurlBtn");
      if (copyCurlBtn) {
        copyCurlBtn.addEventListener("click", async () => {
          try {
            await navigator.clipboard.writeText(curlCommand);
            showNotification("Curl command copied to clipboard", "success");
            copyCurlBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
            setTimeout(() => {
              copyCurlBtn.innerHTML = '<i class="fa-solid fa-copy"></i> Copy';
            }, 2000);
          } catch (error) {
            // Fallback for older browsers
            const curlCodeElement = document.querySelector("#curlCommand");
            const range = document.createRange();
            range.selectNode(curlCodeElement);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            document.execCommand("copy");
            window.getSelection().removeAllRanges();
            showNotification("Curl command copied to clipboard", "success");
            copyCurlBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
            setTimeout(() => {
              copyCurlBtn.innerHTML = '<i class="fa-solid fa-copy"></i> Copy';
            }, 2000);
          }
        });
      }
    } catch (error) {
      showNotification(`Failed to load endpoint details: ${error.message}`, "error");
    }
  };

  // Edit endpoint
  const editEndpoint = async (endpointId) => {
    try {
      const endpoint = await api(`custom-endpoints/${endpointId}`);

      editingEndpointId = endpointId;
      modalTitle.textContent = "Edit Custom Endpoint";
      document.querySelector("#endpointId").value = endpointId;
      document.querySelector("#endpointName").value = endpoint.endpoint_name;
      document.querySelector("#endpointPath").value = endpoint.endpoint_path;

      // Try to select the current API key if it exists in the dropdown
      const currentKey = endpoint.api_key;
      if (currentKey && availableApiKeys.find(k => k.api_key === currentKey)) {
        apiKeySelect.value = currentKey;

        // Update allowed models for this API key
        const selectedOption = apiKeySelect.options[apiKeySelect.selectedIndex];
        if (selectedOption && selectedOption.dataset.allowedModels) {
          selectedApiKeyAllowedModels = JSON.parse(selectedOption.dataset.allowedModels);
          updateModelDropdowns();
        }
      } else {
        apiKeySelect.value = "";
        selectedApiKeyAllowedModels = [];
        updateModelDropdowns();
      }

      // Set model values after updating dropdowns
      document.querySelector("#primaryModel").value = endpoint.primary_model;
      document.querySelector("#fallbackModel").value = endpoint.fallback_model || "";

      endpointModal.style.display = "flex";
    } catch (error) {
      showNotification(`Failed to load endpoint: ${error.message}`, "error");
    }
  };

  // Delete endpoint
  const deleteEndpoint = async (endpointId) => {
    if (!confirm("Are you sure you want to delete this custom endpoint?")) {
      return;
    }

    try {
      await api(`custom-endpoints/${endpointId}`, { method: "DELETE" });
      showNotification("Endpoint deleted successfully", "success");
      await loadEndpoints();
    } catch (error) {
      showNotification(`Failed to delete endpoint: ${error.message}`, "error");
    }
  };

  // Add endpoint button
  addEndpointBtn.addEventListener("click", () => {
    editingEndpointId = null;
    modalTitle.textContent = "Add Custom Endpoint";
    endpointForm.reset();
    document.querySelector("#endpointId").value = "";
    selectedApiKeyAllowedModels = [];
    updateModelDropdowns();
    endpointModal.style.display = "flex";
  });

  // Close modal buttons
  closeModal.addEventListener("click", () => {
    endpointModal.style.display = "none";
    modalNotice.style.display = "none";
  });

  closeDetailsModal.addEventListener("click", () => {
    detailsModal.style.display = "none";
  });

  cancelBtn.addEventListener("click", () => {
    endpointModal.style.display = "none";
    modalNotice.style.display = "none";
  });

  // Close modal on outside click
  window.addEventListener("click", (e) => {
    if (e.target === endpointModal) {
      endpointModal.style.display = "none";
      modalNotice.style.display = "none";
    }
    if (e.target === detailsModal) {
      detailsModal.style.display = "none";
    }
  });

  // Form submission
  endpointForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    modalNotice.style.display = "none";
    modalNotice.classList.remove("error");

    const formData = {
      endpoint_name: document.querySelector("#endpointName").value.trim(),
      endpoint_path: document.querySelector("#endpointPath").value.trim(),
      api_key: apiKeySelect.value.trim(),
      primary_model: document.querySelector("#primaryModel").value,
      fallback_model: document.querySelector("#fallbackModel").value || null,
    };

    // Validate endpoint path format
    if (!formData.endpoint_path.startsWith("/")) {
      modalNotice.textContent = "Endpoint path must start with /";
      modalNotice.classList.add("error");
      modalNotice.style.display = "block";
      return;
    }

    // Validate API key for new endpoints
    if (!editingEndpointId && !formData.api_key) {
      modalNotice.textContent = "API key is required. Please enter an API key or click Generate.";
      modalNotice.classList.add("error");
      modalNotice.style.display = "block";
      return;
    }

    try {
      if (editingEndpointId) {
        // Update existing endpoint
        const updateData = { ...formData };
        // Only update API key if it was changed
        if (!formData.api_key) {
          delete updateData.api_key;
        }

        await api(`custom-endpoints/${editingEndpointId}`, {
          method: "PATCH",
          body: JSON.stringify(updateData),
        });
        showNotification("Endpoint updated successfully", "success");
      } else {
        // Create new endpoint
        await api("custom-endpoints", {
          method: "POST",
          body: JSON.stringify(formData),
        });
        showNotification("Endpoint created successfully", "success");
      }

      endpointModal.style.display = "none";
      endpointForm.reset();
      await loadEndpoints();
    } catch (error) {
      modalNotice.textContent = error.message;
      modalNotice.classList.add("error");
      modalNotice.style.display = "block";
    }
  });

  // API key selection change handler
  apiKeySelect.addEventListener("change", () => {
    const selectedOption = apiKeySelect.options[apiKeySelect.selectedIndex];
    if (selectedOption && selectedOption.dataset.allowedModels) {
      selectedApiKeyAllowedModels = JSON.parse(selectedOption.dataset.allowedModels);
    } else {
      selectedApiKeyAllowedModels = [];
    }
    updateModelDropdowns();
  });

  // Initial load
  await loadModels();
  await loadApiKeys();
  await loadEndpoints();
}

import { api, showNotification, buildTable } from "../lib.js";

export function renderLlmProvider() {
  return `
    <div class="page-header">
      <div>
        <h1>LLM Provider Management</h1>
        <p>Configure and manage multiple LLM providers (LMStudio, Ollama, llama.cpp, etc.).</p>
      </div>
      <button class="primary" id="addProviderBtn">
        <i class="fa-solid fa-plus"></i> Add Provider
      </button>
    </div>

    <div class="card">
      <h3>Configured Providers</h3>
      <div class="table-wrap" id="providersTable"></div>
    </div>

    <!-- Add/Edit Provider Modal -->
    <div id="providerModal" class="modal" style="display: none;">
      <div class="modal-content" style="max-width: 600px;">
        <div class="modal-header">
          <h3 id="modalTitle">Add Provider</h3>
          <button class="close-modal" id="closeModal">&times;</button>
        </div>
        <form id="providerForm" class="form-grid">
          <input type="hidden" id="providerId" />
          <div>
            <label for="providerName">Provider Name</label>
            <input
              id="providerName"
              name="provider_name"
              type="text"
              placeholder="e.g., LMStudio, Ollama"
              required
            />
          </div>
          <div>
            <label for="baseUrl">Base URL</label>
            <input
              id="baseUrl"
              name="base_url"
              type="text"
              placeholder="e.g., http://10.0.0.100:1234"
              required
            />
            <small style="color: var(--muted); font-size: 0.875rem;">
              Include protocol and port (e.g., http://localhost:11434)
            </small>
          </div>
          <div>
            <label for="apiKey">API Key (Optional)</label>
            <input
              id="apiKey"
              name="api_key"
              type="password"
              placeholder="Leave empty for local servers"
            />
            <small style="color: var(--muted); font-size: 0.875rem;">
              Required for cloud providers, optional for local servers
            </small>
          </div>
          <div class="button-row">
            <button class="primary" type="submit">
              <i class="fa-solid fa-save"></i> Save Provider
            </button>
            <button class="secondary" type="button" id="cancelBtn">
              Cancel
            </button>
          </div>
        </form>
        <div id="modalNotice" class="notice" style="display: none;"></div>
      </div>
    </div>

    <!-- Provider Details Modal -->
    <div id="detailsModal" class="modal" style="display: none;">
      <div class="modal-content" style="max-width: 800px;">
        <div class="modal-header">
          <h3 id="detailsTitle">Provider Details</h3>
          <button class="close-modal" id="closeDetailsModal">&times;</button>
        </div>
        <div id="detailsContent"></div>
      </div>
    </div>
  `;
}

export async function afterRenderLlmProvider() {
  const providersTable = document.querySelector("#providersTable");
  const addProviderBtn = document.querySelector("#addProviderBtn");
  const providerModal = document.querySelector("#providerModal");
  const detailsModal = document.querySelector("#detailsModal");
  const providerForm = document.querySelector("#providerForm");
  const closeModal = document.querySelector("#closeModal");
  const closeDetailsModal = document.querySelector("#closeDetailsModal");
  const cancelBtn = document.querySelector("#cancelBtn");
  const modalNotice = document.querySelector("#modalNotice");
  const modalTitle = document.querySelector("#modalTitle");

  let editingProviderId = null;

  // Load providers
  const loadProviders = async () => {
    try {
      const providers = await api("providers");

      if (providers.length === 0) {
        providersTable.innerHTML = `<div class="empty">No providers configured. Click "Add Provider" to get started.</div>`;
        return;
      }

      const rows = providers.map((provider) => {
        const statusIcon = getStatusIcon(provider.health_status);

        return [
          provider.provider_name,
          provider.base_url,
          `<span class="status-badge" data-status="${provider.health_status}">${statusIcon} ${provider.health_status || "unknown"}</span>`,
          `<div class="button-row">
            <button class="secondary btn-sm" data-action="check-health" data-id="${provider.id}">
              <i class="fa-solid fa-heartbeat"></i> Check
            </button>
            <button class="secondary btn-sm" data-action="refresh-models" data-id="${provider.id}">
              <i class="fa-solid fa-sync"></i> Refresh
            </button>
            <button class="secondary btn-sm" data-action="view" data-id="${provider.id}">
              <i class="fa-solid fa-eye"></i> View
            </button>
            <button class="secondary btn-sm" data-action="edit" data-id="${provider.id}">
              <i class="fa-solid fa-edit"></i> Edit
            </button>
            <button class="danger btn-sm" data-action="delete" data-id="${provider.id}">
              <i class="fa-solid fa-trash"></i> Delete
            </button>
          </div>`,
        ];
      });

      providersTable.innerHTML = buildTable(
        ["Provider", "Base URL", "Status", "Actions"],
        rows
      );

      // Attach event listeners to action buttons
      providersTable.querySelectorAll("button[data-action]").forEach((button) => {
        button.addEventListener("click", async (e) => {
          e.preventDefault();
          const action = button.dataset.action;
          const id = Number(button.dataset.id);

          if (action === "check-health") {
            await checkProviderHealth(id);
          } else if (action === "refresh-models") {
            await refreshModels(id);
          } else if (action === "view") {
            await viewProviderDetails(id);
          } else if (action === "edit") {
            await editProvider(id);
          } else if (action === "delete") {
            await deleteProvider(id);
          }
        });
      });
    } catch (error) {
      providersTable.innerHTML = `<div class="empty error">${error.message}</div>`;
    }
  };

  // Get status icon
  const getStatusIcon = (status) => {
    if (status === "online") {
      return '<i class="fa-solid fa-circle" style="color: #10b981;"></i>';
    } else if (status === "offline") {
      return '<i class="fa-solid fa-circle" style="color: var(--danger);"></i>';
    } else {
      return '<i class="fa-solid fa-circle" style="color: var(--muted);"></i>';
    }
  };

  // Check provider health
  const checkProviderHealth = async (providerId) => {
    try {
      showNotification("Checking provider health...", "info");
      const result = await api(`providers/${providerId}/health`);

      if (result.status === "online") {
        showNotification(`${result.provider_name} is online`, "success");
      } else {
        showNotification(`${result.provider_name} is offline`, "error");
      }

      await loadProviders();
    } catch (error) {
      showNotification(`Health check failed: ${error.message}`, "error");
    }
  };

  // Refresh models
  const refreshModels = async (providerId) => {
    try {
      showNotification("Fetching models from provider...", "info");
      const result = await api(`providers/${providerId}/refresh-models`, {
        method: "POST",
      });

      showNotification(
        `Refreshed ${result.models_count} models for ${result.provider_name} (${result.added_count} new)`,
        "success"
      );
    } catch (error) {
      showNotification(`Failed to refresh models: ${error.message}`, "error");
    }
  };

  // View provider details
  const viewProviderDetails = async (providerId) => {
    try {
      const provider = await api(`providers/${providerId}`);
      const models = await api(`providers/${providerId}/models`);

      const modelsList = models.models
        .map(
          (model) => `
        <div class="model-item">
          <i class="fa-solid fa-cube" style="color: var(--accent); margin-right: 8px;"></i>
          <span>${model.id}</span>
        </div>
      `
        )
        .join("");

      document.querySelector("#detailsTitle").textContent = `${provider.provider_name} - Details`;
      document.querySelector("#detailsContent").innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <strong>Base URL:</strong> ${provider.base_url}
          </div>
          <div>
            <strong>Status:</strong> <span class="status-badge" data-status="${provider.health_status}">
              ${getStatusIcon(provider.health_status)} ${provider.health_status || "unknown"}
            </span>
          </div>
          <div>
            <strong>Last Health Check:</strong> ${provider.last_health_check || "Never"}
          </div>
          <div>
            <strong>Available Models (${models.models.length}):</strong>
            <div class="models-list" style="margin-top: 0.5rem; max-height: 300px; overflow-y: auto;">
              ${modelsList || '<div class="empty">No models available</div>'}
            </div>
          </div>
        </div>
      `;

      detailsModal.style.display = "flex";
    } catch (error) {
      showNotification(`Failed to load provider details: ${error.message}`, "error");
    }
  };

  // Edit provider
  const editProvider = async (providerId) => {
    try {
      const provider = await api(`providers/${providerId}`);

      editingProviderId = providerId;
      modalTitle.textContent = "Edit Provider";
      document.querySelector("#providerId").value = providerId;
      document.querySelector("#providerName").value = provider.provider_name;
      document.querySelector("#baseUrl").value = provider.base_url;
      document.querySelector("#apiKey").value = ""; // Don't pre-fill for security

      providerModal.style.display = "flex";
    } catch (error) {
      showNotification(`Failed to load provider: ${error.message}`, "error");
    }
  };

  // Delete provider
  const deleteProvider = async (providerId) => {
    if (!confirm("Are you sure you want to delete this provider? Associated models will be deactivated.")) {
      return;
    }

    try {
      await api(`providers/${providerId}`, { method: "DELETE" });
      showNotification("Provider deleted successfully", "success");
      await loadProviders();
    } catch (error) {
      showNotification(`Failed to delete provider: ${error.message}`, "error");
    }
  };

  // Add provider button
  addProviderBtn.addEventListener("click", () => {
    editingProviderId = null;
    modalTitle.textContent = "Add Provider";
    providerForm.reset();
    document.querySelector("#providerId").value = "";
    providerModal.style.display = "flex";
  });

  // Close modal buttons
  closeModal.addEventListener("click", () => {
    providerModal.style.display = "none";
    modalNotice.style.display = "none";
  });

  closeDetailsModal.addEventListener("click", () => {
    detailsModal.style.display = "none";
  });

  cancelBtn.addEventListener("click", () => {
    providerModal.style.display = "none";
    modalNotice.style.display = "none";
  });

  // Close modal on outside click
  window.addEventListener("click", (e) => {
    if (e.target === providerModal) {
      providerModal.style.display = "none";
      modalNotice.style.display = "none";
    }
    if (e.target === detailsModal) {
      detailsModal.style.display = "none";
    }
  });

  // Form submission
  providerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    modalNotice.style.display = "none";

    const formData = {
      provider_name: document.querySelector("#providerName").value.trim(),
      base_url: document.querySelector("#baseUrl").value.trim(),
      api_key: document.querySelector("#apiKey").value.trim() || null,
    };

    // Remove trailing slash from base URL
    if (formData.base_url.endsWith("/")) {
      formData.base_url = formData.base_url.slice(0, -1);
    }

    try {
      if (editingProviderId) {
        // Update existing provider
        await api(`providers/${editingProviderId}`, {
          method: "PATCH",
          body: JSON.stringify(formData),
        });
        showNotification("Provider updated successfully", "success");
      } else {
        // Create new provider
        await api("providers", {
          method: "POST",
          body: JSON.stringify(formData),
        });
        showNotification("Provider created successfully", "success");
      }

      providerModal.style.display = "none";
      providerForm.reset();
      await loadProviders();
    } catch (error) {
      modalNotice.textContent = error.message;
      modalNotice.classList.add("error");
      modalNotice.style.display = "block";
    }
  });

  // Initial load
  await loadProviders();
}

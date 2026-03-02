import { api, formatMoney, buildTable } from "../lib.js";

export function renderModels() {
  return `
    <div class="page-header">
      <div>
        <h1>Model Cost Configuration</h1>
        <p>Set pricing, manage model access, and estimate cost.</p>
      </div>
    </div>



    <div class="card">
      <h3>Cost Calculator</h3>
      <form id="calcForm" class="form-grid">
        <div>
          <label for="calcModel">Model</label>
          <select id="calcModel" name="model"></select>
        </div>
        <div>
          <label for="inputTokens">Input tokens</label>
          <input id="inputTokens" name="input_tokens" type="number" min="0" value="1000" />
        </div>
        <div>
          <label for="outputTokens">Output tokens</label>
          <input id="outputTokens" name="output_tokens" type="number" min="0" value="500" />
        </div>
      </form>
      <div class="section-stack">
        <div id="calcResult" class="notice"></div>
      </div>
    </div>

    <div class="card">
      <h3>Configured Models</h3>
      <div class="table-wrap" id="modelsTable"></div>
    </div>
  `;
}

export async function afterRenderModels() {
  const tableWrap = document.querySelector("#modelsTable");
  const modelSelect = document.querySelector("#calcModel");
  const result = document.querySelector("#calcResult");

  let allModels = [];

  const loadModels = async () => {
    const models = await api("models");
    allModels = models;

    // Build table with edit/save functionality
    const rows = models.map((model) => [
      model.model_name,
      model.provider_name || "-",
      `<span class="price-display" data-model="${model.model_name}" data-field="input">${formatMoney(model.input_cost_per_1k, 6)}</span>
       <input type="number" step="0.000001" min="0" value="${model.input_cost_per_1k}"
         class="price-input" data-model="${model.model_name}" data-field="input"
         style="display: none; width: 100px; padding: 4px 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; color: var(--text);" />`,
      `<span class="price-display" data-model="${model.model_name}" data-field="output">${formatMoney(model.output_cost_per_1k, 6)}</span>
       <input type="number" step="0.000001" min="0" value="${model.output_cost_per_1k}"
         class="price-input" data-model="${model.model_name}" data-field="output"
         style="display: none; width: 100px; padding: 4px 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; color: var(--text);" />`,
      `<div class="button-row">
        <button class="secondary btn-sm" data-action="edit" data-model="${model.model_name}">
          <i class="fa-solid fa-edit"></i> Edit
        </button>
        <button class="primary btn-sm" data-action="save" data-model="${model.model_name}" style="display: none;">
          <i class="fa-solid fa-save"></i> Save
        </button>
        <button class="danger btn-sm" data-id="${model.id}">
          <i class="fa-solid fa-trash"></i> Delete
        </button>
      </div>`,
    ]);

    tableWrap.innerHTML = buildTable(["Model", "Provider", "Input ($/1K)", "Output ($/1K)", "Actions"], rows);

    // Delete button handler
    tableWrap.querySelectorAll("button[data-id]").forEach((button) => {
      button.addEventListener("click", async () => {
        if (!window.confirm("Delete this model?")) return;
        await api(`models/${button.dataset.id}`, { method: "DELETE" });
        await loadModels();
      });
    });

    // Edit button handler
    tableWrap.querySelectorAll("button[data-action='edit']").forEach((button) => {
      button.addEventListener("click", () => {
        const modelName = button.dataset.model;
        const row = button.closest("tr");

        // Hide displays, show inputs
        row.querySelectorAll(".price-display").forEach(el => el.style.display = "none");
        row.querySelectorAll(".price-input").forEach(el => el.style.display = "inline-block");

        // Hide edit button, show save button
        button.style.display = "none";
        row.querySelector("button[data-action='save']").style.display = "inline-flex";
      });
    });

    // Save button handler for inline editing
    tableWrap.querySelectorAll("button[data-action='save']").forEach((button) => {
      button.addEventListener("click", async () => {
        const modelName = button.dataset.model;
        const row = button.closest("tr");
        const inputCostField = row.querySelector("input[data-field='input']");
        const outputCostField = row.querySelector("input[data-field='output']");

        const inputCost = parseFloat(inputCostField.value);
        const outputCost = parseFloat(outputCostField.value);

        // Get the model's existing provider_name from allModels
        const model = allModels.find(m => m.model_name === modelName);
        const providerName = model ? model.provider_name : null;

        try {
          await api("models", {
            method: "POST",
            body: JSON.stringify({
              model_name: modelName,
              input_cost_per_1k: inputCost,
              output_cost_per_1k: outputCost,
            }),
          });

          // Show success feedback
          button.innerHTML = '<i class="fa-solid fa-check"></i> Saved';
          button.classList.remove('primary');
          button.classList.add('success');

          setTimeout(async () => {
            await loadModels();
          }, 1000);

        } catch (error) {
          alert(`Failed to save: ${error.message}`);
          // Revert to edit mode on error
          row.querySelectorAll(".price-display").forEach(el => el.style.display = "inline");
          row.querySelectorAll(".price-input").forEach(el => el.style.display = "none");
          button.style.display = "none";
          row.querySelector("button[data-action='edit']").style.display = "inline-flex";
        }
      });
    });

    // Populate calculator dropdown
    modelSelect.innerHTML = models
      .map((model) => `<option value="${model.model_name}">${model.model_name}</option>`)
      .join("");

    calculate(models);
  };

  const calculate = async (models) => {
    if (!models.length) {
      result.textContent = "Add a model to calculate costs.";
      return;
    }
    const form = document.querySelector("#calcForm");
    const modelName = form.model.value;
    const inputTokens = Number(form.input_tokens.value || 0);
    const outputTokens = Number(form.output_tokens.value || 0);
    const model = models.find((item) => item.model_name === modelName);
    if (!model) return;
    const inputCost = (inputTokens / 1000) * model.input_cost_per_1k;
    const outputCost = (outputTokens / 1000) * model.output_cost_per_1k;
    const total = inputCost + outputCost;
    result.textContent = `Input: ${inputTokens} x $${model.input_cost_per_1k.toFixed(6)} = ${formatMoney(
      inputCost,
      6
    )} | Output: ${outputTokens} x $${model.output_cost_per_1k.toFixed(6)} = ${formatMoney(
      outputCost,
      6
    )} | Total: ${formatMoney(total, 6)}`;
  };

  document.querySelector("#calcForm").addEventListener("input", async () => {
    const models = await api("models");
    calculate(models);
  });

  try {
    await loadModels();
  } catch (error) {
    tableWrap.innerHTML = `<div class="empty">${error.message}</div>`;
  }
}

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
 <div class="grid-2">
      <div class="card">
        <h3>Configured Models</h3>
        <div class="table-wrap" id="modelsTable"></div>
      </div>
      <div class="card">
        <h3>Add Model Pricing</h3>
        <form id="modelForm" class="form-grid">
          <div>
            <label for="modelName">Model name</label>
            <input id="modelName" name="model_name" placeholder="e.g. llama2" required />
          </div>
          <div>
            <label for="inputCost">Input cost ($/1K)</label>
            <input id="inputCost" name="input_cost_per_1k" type="number" min="0" step="0.0001" value="0.001" />
          </div>
          <div>
            <label for="outputCost">Output cost ($/1K)</label>
            <input id="outputCost" name="output_cost_per_1k" type="number" min="0" step="0.0001" value="0.002" />
          </div>
          <div class="button-row">
            <button class="primary" type="submit">Add / Update Model</button>
          </div>
        </form>
        <div id="modelNotice" class="notice"></div>
      </div>


    </div>
  `;
}

export async function afterRenderModels() {
  const tableWrap = document.querySelector("#modelsTable");
  const modelSelect = document.querySelector("#calcModel");
  const notice = document.querySelector("#modelNotice");
  const result = document.querySelector("#calcResult");
  notice.style.display = "none";

  const loadModels = async () => {
    const models = await api("models");
    const rows = models.map((model) => [
      model.model_name,
      formatMoney(model.input_cost_per_1k, 6),
      formatMoney(model.output_cost_per_1k, 6),
      `<button class="danger" data-id="${model.id}">Delete</button>`,
    ]);

    tableWrap.innerHTML = buildTable(["Model", "Input", "Output", ""], rows);
    tableWrap.querySelectorAll("button[data-id]").forEach((button) => {
      button.addEventListener("click", async () => {
        if (!window.confirm("Delete this model?")) return;
        await api(`models/${button.dataset.id}`, { method: "DELETE" });
        await loadModels();
      });
    });

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

  document.querySelector("#modelForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    notice.classList.remove("error");
    notice.style.display = "none";
    const form = event.target;
    try {
      await api("models", {
        method: "POST",
        body: JSON.stringify({
          model_name: form.model_name.value.trim(),
          input_cost_per_1k: Number(form.input_cost_per_1k.value || 0),
          output_cost_per_1k: Number(form.output_cost_per_1k.value || 0),
        }),
      });
      notice.textContent = "Model saved.";
      notice.style.display = "block";
      form.reset();
      await loadModels();
    } catch (error) {
      notice.textContent = error.message;
      notice.classList.add("error");
      notice.style.display = "block";
    }
  });

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

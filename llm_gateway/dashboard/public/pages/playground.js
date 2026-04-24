import { api } from "../lib.js";

export function renderPlayground() {
  return `
    <div class="page-header">
      <div>
        <div class="page-title">Playground</div>
        <div class="page-subtitle">Chat with your LLM gateway using any API key</div>
      </div>
    </div>

    <div class="playground-layout">
      <div class="playground-config card">
        <div class="playground-config-title">Configuration</div>

        <div class="form-field">
          <label class="form-label">API Key</label>
          <select id="pg-api-key" class="form-control">
            <option value="">Loading...</option>
          </select>
        </div>

        <div class="form-field">
          <label class="form-label">Model</label>
          <select id="pg-model" class="form-control">
            <option value="">Select API key first</option>
          </select>
        </div>

        <div class="form-field">
          <label class="form-label">System Prompt</label>
          <textarea id="pg-system" class="form-control" rows="4" placeholder="You are a helpful assistant."></textarea>
        </div>

        <div class="form-field">
          <label class="form-label">Temperature: <span id="pg-temp-val">0.7</span></label>
          <input type="range" id="pg-temperature" min="0" max="2" step="0.1" value="0.7" class="form-range" />
        </div>

        <div class="form-field">
          <label class="form-label">Max Tokens</label>
          <input type="number" id="pg-max-tokens" class="form-control" value="1024" min="1" max="32000" />
        </div>

        <button id="pg-clear" class="btn-secondary" style="width:100%;margin-top:8px;">
          <i class="fa-solid fa-trash"></i> Clear Chat
        </button>
      </div>

      <div class="playground-chat">
        <div class="chat-messages" id="pg-messages">
          <div class="chat-empty">
            <i class="fa-solid fa-comments" style="font-size:2rem;opacity:0.3;"></i>
            <div style="margin-top:8px;opacity:0.5;">Select an API key and model to start chatting</div>
          </div>
        </div>

        <div class="chat-input-area">
          <textarea
            id="pg-input"
            class="chat-input"
            placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
            rows="1"
          ></textarea>
          <button id="pg-send" class="primary chat-send-btn" disabled>
            <i class="fa-solid fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </div>
  `;
}

export async function afterRenderPlayground() {
  const apiKeySelect = document.getElementById("pg-api-key");
  const modelSelect = document.getElementById("pg-model");
  const systemInput = document.getElementById("pg-system");
  const tempSlider = document.getElementById("pg-temperature");
  const tempVal = document.getElementById("pg-temp-val");
  const maxTokensInput = document.getElementById("pg-max-tokens");
  const messagesEl = document.getElementById("pg-messages");
  const inputEl = document.getElementById("pg-input");
  const sendBtn = document.getElementById("pg-send");
  const clearBtn = document.getElementById("pg-clear");

  let messages = [];
  let selectedApiKey = null;
  let isStreaming = false;
  const sessionId = `playground_${Date.now()}`;

  function maskKey(key) {
    return key.length > 8 ? "****" + key.slice(-6) : "****";
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br>");
  }

  function renderMarkdown(text) {
    if (!window.marked) return escapeHtml(text);
    const renderer = new marked.Renderer();
    if (window.hljs) {
      renderer.code = (token) => {
        const code = token.text ?? token ?? "";
        const lang = token.lang || "";
        const language = lang && hljs.getLanguage(lang) ? lang : "plaintext";
        const highlighted = hljs.highlight(String(code), { language }).value;
        return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`;
      };
    }
    return marked.parse(text, { renderer, breaks: true });
  }

  function updateSendBtn() {
    sendBtn.disabled = !selectedApiKey || !modelSelect.value || isStreaming;
  }

  function renderMessages() {
    if (messages.length === 0) {
      messagesEl.innerHTML = `
        <div class="chat-empty">
          <i class="fa-solid fa-comments" style="font-size:2rem;opacity:0.3;"></i>
          <div style="margin-top:8px;opacity:0.5;">Select an API key and model to start chatting</div>
        </div>`;
      return;
    }
    messagesEl.innerHTML = messages
      .map(
        (m) => `
        <div class="chat-msg chat-msg--${m.role}">
          <div class="chat-msg-role">${m.role === "user" ? "You" : "Assistant"}</div>
          <div class="chat-msg-content">${m.role === "assistant" ? renderMarkdown(m.content) : escapeHtml(m.content)}</div>
        </div>`
      )
      .join("");
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  // Load API keys
  try {
    const keys = await api("api-keys");
    const activeKeys = keys.filter((k) => k.is_active);
    apiKeySelect.innerHTML = activeKeys.length
      ? `<option value="">— Select API Key —</option>` +
        activeKeys
          .map(
            (k) =>
              `<option value="${k.api_key}" data-models='${JSON.stringify(k.allowed_models)}'>${k.username} — ${maskKey(k.api_key)}</option>`
          )
          .join("")
      : `<option value="">No active API keys</option>`;
  } catch {
    apiKeySelect.innerHTML = `<option value="">Failed to load keys</option>`;
  }

  apiKeySelect.addEventListener("change", async () => {
    const opt = apiKeySelect.selectedOptions[0];
    selectedApiKey = opt.value || null;

    if (!selectedApiKey) {
      modelSelect.innerHTML = `<option value="">Select API key first</option>`;
      updateSendBtn();
      return;
    }

    let allowedModels = [];
    try {
      allowedModels = JSON.parse(opt.dataset.models || "[]");
    } catch {}

    const isAllModels = allowedModels.length === 1 && allowedModels[0] === "* (All Models)";

    if (isAllModels) {
      try {
        const models = await api("models");
        modelSelect.innerHTML =
          `<option value="">— Select Model —</option>` +
          models.map((m) => `<option value="${m.model_name}">${m.model_name}</option>`).join("");
      } catch {
        modelSelect.innerHTML = `<option value="">Failed to load models</option>`;
      }
    } else {
      modelSelect.innerHTML =
        `<option value="">— Select Model —</option>` +
        allowedModels
          .filter((m) => m !== "* (All Models)")
          .map((m) => `<option value="${m}">${m}</option>`)
          .join("");
    }
    updateSendBtn();
  });

  modelSelect.addEventListener("change", updateSendBtn);

  tempSlider.addEventListener("input", () => {
    tempVal.textContent = tempSlider.value;
  });

  clearBtn.addEventListener("click", () => {
    messages = [];
    renderMessages();
  });

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) sendBtn.click();
    }
  });

  sendBtn.addEventListener("click", sendMessage);

  async function sendMessage() {
    const content = inputEl.value.trim();
    if (!content || isStreaming) return;

    messages.push({ role: "user", content });
    inputEl.value = "";
    isStreaming = true;
    updateSendBtn();

    const assistantMsg = { role: "assistant", content: "" };
    messages.push(assistantMsg);
    renderMessages();

    const bubbles = messagesEl.querySelectorAll(".chat-msg--assistant");
    const lastBubble = bubbles[bubbles.length - 1]?.querySelector(".chat-msg-content");

    try {
      const payload = {
        model: modelSelect.value,
        messages: [
          ...(systemInput.value.trim()
            ? [{ role: "system", content: systemInput.value.trim() }]
            : []),
          ...messages.slice(0, -1),
        ],
        temperature: parseFloat(tempSlider.value),
        max_tokens: parseInt(maxTokensInput.value, 10),
        stream: true,
      };

      const response = await fetch("/api/playground/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${selectedApiKey}`,
          "X-Session-ID": sessionId,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const err = await response.text();
        assistantMsg.content = `Error: ${err}`;
        renderMessages();
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6).trim();
          if (data === "[DONE]") break;
          try {
            const parsed = JSON.parse(data);
            const delta = parsed.choices?.[0]?.delta?.content || "";
            assistantMsg.content += delta;
            if (lastBubble) {
              lastBubble.innerHTML = renderMarkdown(assistantMsg.content) + '<span class="pg-cursor">▋</span>';
              messagesEl.scrollTop = messagesEl.scrollHeight;
            }
          } catch {}
        }
      }

      if (lastBubble) lastBubble.innerHTML = renderMarkdown(assistantMsg.content);
    } catch (err) {
      assistantMsg.content = `Error: ${err.message}`;
      if (lastBubble) lastBubble.innerHTML = escapeHtml(assistantMsg.content);
    } finally {
      isStreaming = false;
      updateSendBtn();
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }
  }
}

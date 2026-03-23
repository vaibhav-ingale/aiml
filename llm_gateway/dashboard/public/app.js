import { renderDashboard, afterRenderDashboard } from "./pages/dashboard.js";
import { renderUsers, afterRenderUsers } from "./pages/users.js";
import { renderApiKeys, afterRenderApiKeys } from "./pages/api-keys.js";
import { renderModels, afterRenderModels } from "./pages/models.js";
import { renderAnalytics, afterRenderAnalytics } from "./pages/analytics.js";
import { renderTraces, afterRenderTraces } from "./pages/traces.js";
import { renderLlmProvider, afterRenderLlmProvider } from "./pages/llm-provider.js";
import { renderCustomEndpoints, afterRenderCustomEndpoints } from "./pages/custom-endpoints.js";

const routes = {
  dashboard: {
    render: renderDashboard,
    afterRender: afterRenderDashboard,
  },
  users: {
    render: renderUsers,
    afterRender: afterRenderUsers,
  },
  "api-keys": {
    render: renderApiKeys,
    afterRender: afterRenderApiKeys,
  },
  models: {
    render: renderModels,
    afterRender: afterRenderModels,
  },
  analytics: {
    render: renderAnalytics,
    afterRender: afterRenderAnalytics,
  },
  traces: {
    render: renderTraces,
    afterRender: afterRenderTraces,
  },
  "llm-provider": {
    render: renderLlmProvider,
    afterRender: afterRenderLlmProvider,
  },
  "custom-endpoints": {
    render: renderCustomEndpoints,
    afterRender: afterRenderCustomEndpoints,
  },
};

const appRoot = document.querySelector(".app");
const pageRoot = document.querySelector("#page");
const links = document.querySelectorAll("[data-route]");
const sidebarToggle = document.querySelector("#sidebarToggle");
const sidebarStorageKey = "ollama.sidebar.collapsed";

function setActive(route) {
  links.forEach((link) => {
    const target = link.getAttribute("data-route");
    link.classList.toggle("active", target === route);
  });
}

async function navigate() {
  const route = window.location.hash.replace("#", "") || "dashboard";
  const entry = routes[route] || routes.dashboard;
  setActive(route);
  pageRoot.innerHTML = entry.render();
  await entry.afterRender();
}

function setSidebarState(collapsed) {
  appRoot.classList.toggle("is-collapsed", collapsed);
  sidebarToggle.setAttribute("aria-pressed", String(collapsed));
  localStorage.setItem(sidebarStorageKey, collapsed ? "1" : "0");
}

function initSidebarToggle() {
  if (!sidebarToggle || !appRoot) return;
  const stored = localStorage.getItem(sidebarStorageKey);
  const collapsed = stored === "1";
  setSidebarState(collapsed);
  sidebarToggle.addEventListener("click", () => {
    setSidebarState(!appRoot.classList.contains("is-collapsed"));
  });
}

links.forEach((link) => {
  link.addEventListener("click", () => {
    const route = link.getAttribute("data-route");
    window.location.hash = route;
  });
});

window.addEventListener("hashchange", navigate);
window.addEventListener("DOMContentLoaded", () => {
  initSidebarToggle();
  navigate();
});

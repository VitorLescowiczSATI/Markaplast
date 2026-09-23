import { demoApi } from "./demoApi";
import { IS_DEMO } from "./mode";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "gimak.accessToken";

let accessToken = window.localStorage.getItem(TOKEN_KEY) || "";

function setAccessToken(token) {
  accessToken = token || "";
  if (accessToken) window.localStorage.setItem(TOKEN_KEY, accessToken);
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}, authenticated = true) {
  const response = await fetch(`${API_URL}/api/gimak${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(authenticated && accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const raw = await response.text();
    let message = raw;
    try {
      message = JSON.parse(raw)?.detail || raw;
    } catch {
      // Mantém o texto original quando a resposta não é JSON.
    }
    if (response.status === 401 && authenticated) {
      setAccessToken("");
      window.dispatchEvent(new Event("gimak:auth-expired"));
    }
    throw new Error(message || `Erro HTTP ${response.status}`);
  }
  return response.status === 204 ? null : response.json();
}

const json = (method, payload) => ({ method, body: JSON.stringify(payload) });

const realApi = {
  hasToken: () => Boolean(accessToken),
  setAccessToken,
  login: (username, senha) => request("/auth/login", json("POST", { username, senha }), false),
  me: () => request("/auth/me"),
  getIndicators: (inicio, fim, options = {}) => request(`/indicadores?${new URLSearchParams({ inicio, fim })}`, options),
  getTVPanel: (options = {}) => request("/painel-tv", options),
  listUsers: () => request("/usuarios"),
  createUser: (payload) => request("/usuarios", json("POST", payload)),
  updateUser: (id, payload) => request(`/usuarios/${id}`, json("PATCH", payload)),
  resetPassword: (id, senha) => request(`/usuarios/${id}/senha`, json("POST", { senha })),
  listProjects: (situacao = "todos") => request(`/projetos?situacao=${situacao}`),
  createProject: (payload) => request("/projetos", json("POST", payload)),
  updateProject: (id, payload) => request(`/projetos/${id}`, json("PATCH", payload)),
  listTasks: () => request("/tarefas"),
  createTask: (payload) => request("/tarefas", json("POST", payload)),
  updateTask: (id, payload) => request(`/tarefas/${id}`, json("PATCH", payload)),
  updateTaskStatus: (id, status, motivo = "") =>
    request(`/tarefas/${id}/status`, json("PATCH", { status, motivo })),
  deleteTask: (id) => request(`/tarefas/${id}`, { method: "DELETE" }),
  listServices: (situacao = "todos") => request(`/atendimentos?situacao=${situacao}`),
  createService: (payload) => request("/atendimentos", json("POST", payload)),
  updateService: (id, payload) => request(`/atendimentos/${id}`, json("PATCH", payload)),
  finishService: (id, relatorio) => request(`/atendimentos/${id}/concluir`, json("POST", { relatorio })),
  reopenService: (id) => request(`/atendimentos/${id}/reabrir`, json("POST", {})),
  leaveForService: (id) => request(`/atendimentos/${id}/sair`, json("POST", {})),
  deleteService: (id) => request(`/atendimentos/${id}`, { method: "DELETE" }),
  listIssues: (situacao = "todas") => request(`/pendencias?situacao=${situacao}`),
  createIssue: (serviceId, descricao) => request(`/atendimentos/${serviceId}/pendencias`, json("POST", { descricao })),
  updateIssue: (id, payload) => request(`/pendencias/${id}`, json("PATCH", payload)),
  resolveIssue: (id, resolucao) => request(`/pendencias/${id}/resolver`, json("POST", { resolucao })),
  reopenIssue: (id) => request(`/pendencias/${id}/reabrir`, json("POST", {})),
  deleteIssue: (id) => request(`/pendencias/${id}`, { method: "DELETE" }),
};

// Em /demo a interface é a mesma, mas nenhuma chamada sai do navegador.
export const api = IS_DEMO ? demoApi : realApi;

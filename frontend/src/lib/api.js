const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "giras.accessToken";

let accessToken = window.localStorage.getItem(TOKEN_KEY) || "";

function setAccessToken(token) {
  accessToken = token || "";
  if (accessToken) window.localStorage.setItem(TOKEN_KEY, accessToken);
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}, authenticated = true) {
  const response = await fetch(`${API_URL}${path}`, {
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
      // Resposta não JSON: usa o texto original.
    }
    if (response.status === 401 && authenticated) {
      setAccessToken("");
      window.dispatchEvent(new Event("giras:auth-expired"));
    }
    throw new Error(message || `Erro HTTP ${response.status}`);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  getAccessToken: () => accessToken,
  setAccessToken,
  login: (username, senha) => request("/api/auth/login", { method: "POST", body: JSON.stringify({ username, senha }) }, false),
  me: () => request("/api/auth/me"),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  listUsuarios: () => request("/api/auth/usuarios"),
  createUsuario: (payload) => request("/api/auth/usuarios", { method: "POST", body: JSON.stringify(payload) }),
  updateUsuario: (id, payload) => request(`/api/auth/usuarios/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  resetUsuarioSenha: (id, senha) => request(`/api/auth/usuarios/${id}/senha`, { method: "POST", body: JSON.stringify({ senha }) }),
  health: () => request("/health"),
  listPedidos: () => request("/api/pedidos"),
  createPedido: (payload) => request("/api/pedidos", { method: "POST", body: JSON.stringify(payload) }),
  updatePedido: (id, payload) => request(`/api/pedidos/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  updateStatus: (id, status) => request(`/api/pedidos/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
  updateFinanceiro: (id, statusFinanceiro) =>
    request(`/api/pedidos/${id}/financeiro`, { method: "PATCH", body: JSON.stringify({ statusFinanceiro }) }),
  deletePedido: (id) => request(`/api/pedidos/${id}`, { method: "DELETE" }),
  listCargas: () => request("/api/cargas"),
  createCarga: (payload) => request("/api/cargas", { method: "POST", body: JSON.stringify(payload) }),
  listClientes: () => request("/api/clientes"),
  createCliente: (payload) => request("/api/clientes", { method: "POST", body: JSON.stringify(payload) }),
  updateCliente: (id, payload) => request(`/api/clientes/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteCliente: (id) => request(`/api/clientes/${id}`, { method: "DELETE" }),
  lookupCep: (cep) => request(`/api/integracoes/cep/${encodeURIComponent(cep)}`),
  listProdutos: () => request("/api/produtos"),
  createProduto: (payload) => request("/api/produtos", { method: "POST", body: JSON.stringify(payload) }),
  updateProduto: (id, payload) => request(`/api/produtos/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  createMovimentoEstoque: (id, payload) => request(`/api/produtos/${id}/movimentos`, { method: "POST", body: JSON.stringify(payload) }),
  listPrecos: (clienteId) => request(`/api/precos?clienteId=${encodeURIComponent(clienteId)}`),
  lookupPreco: (clienteId, produtoId) =>
    request(`/api/precos/lookup?clienteId=${encodeURIComponent(clienteId)}&produtoId=${encodeURIComponent(produtoId)}`),
  upsertPreco: (payload) => request("/api/precos", { method: "POST", body: JSON.stringify(payload) }),
  deletePreco: (id) => request(`/api/precos/${id}`, { method: "DELETE" }),
  listMetas: () => request("/api/metas"),
  upsertMeta: (payload) => request("/api/metas", { method: "POST", body: JSON.stringify(payload) }),
  deleteMeta: (id) => request(`/api/metas/${id}`, { method: "DELETE" }),
  getDashboard: () => request("/api/dashboard"),
  listNotas: () => request("/api/fiscal/notas"),
  prepararNfe: (pedidoId) => request(`/api/fiscal/pedidos/${pedidoId}/preparar-nfe`, { method: "POST" }),
  marcarNfeEmitida: (notaId) => request(`/api/fiscal/notas/${notaId}/marcar-emitida`, { method: "POST" }),
  enviarNfeHomologacao: (notaId) => request(`/api/fiscal/notas/${notaId}/enviar-homologacao`, { method: "POST" }),
  excluirNota: (notaId) => request(`/api/fiscal/notas/${notaId}`, { method: "DELETE" }),
  excluirNotaDoPedido: (pedidoId) => request(`/api/pedidos/${pedidoId}/nota`, { method: "DELETE" }),
};

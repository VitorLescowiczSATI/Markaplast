const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Erro HTTP ${response.status}`);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  health: () => request("/health"),
  listPedidos: () => request("/api/pedidos?perfil=Gestor"),
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
  lookupCep: (cep) => request(`/api/integracoes/cep/${encodeURIComponent(cep)}`),
  listProdutos: () => request("/api/produtos"),
  createProduto: (payload) => request("/api/produtos", { method: "POST", body: JSON.stringify(payload) }),
  updateProduto: (id, payload) => request(`/api/produtos/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  createMovimentoEstoque: (id, payload) => request(`/api/produtos/${id}/movimentos`, { method: "POST", body: JSON.stringify(payload) }),
  getDashboard: () => request("/api/dashboard"),
  listNotas: () => request("/api/fiscal/notas"),
  prepararNfe: (pedidoId) => request(`/api/fiscal/pedidos/${pedidoId}/preparar-nfe`, { method: "POST" }),
  marcarNfeEmitida: (notaId) => request(`/api/fiscal/notas/${notaId}/marcar-emitida`, { method: "POST" }),
  enviarNfeHomologacao: (notaId) => request(`/api/fiscal/notas/${notaId}/enviar-homologacao`, { method: "POST" }),
  historicoRecente: () => request("/api/historico/pedidos"),
};

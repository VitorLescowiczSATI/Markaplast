export function valorTotalPedido(pedido) {
  return (Number(pedido.valor || 0) + Number(pedido.valorTampa || 0)) * Number(pedido.quantidade || 0);
}

export function currency(value) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number(value || 0));
}

export function statusColor(status) {
  if (status === "Cancelado") {
    return "bg-red-50 text-red-800 border-red-200";
  }
  if (["Finalizado", "Enviado", "Nota emitida"].includes(status)) {
    return "bg-green-50 text-green-800 border-green-200";
  }
  if (["Aguardando pagamento", "Novo pedido"].includes(status)) {
    return "bg-amber-50 text-amber-800 border-amber-200";
  }
  if (["Vai produzir", "Em produção", "Pronto para faturar", "Separado para entrega"].includes(status)) {
    return "bg-sky-50 text-sky-800 border-sky-200";
  }
  if (status === "Pago") {
    return "bg-teal-50 text-teal-800 border-teal-200";
  }
  return "bg-slate-100 text-slate-700 border-slate-200";
}

export function financeiroColor(statusFinanceiro) {
  return statusFinanceiro === "Pago"
    ? "bg-green-50 text-green-800 border-green-200"
    : "bg-amber-50 text-amber-800 border-amber-200";
}

export function podeVerPedidoPorPerfil(perfil, status) {
  if (perfil === "Gestor" || perfil === "Comercial") return true;
  if (perfil === "Financeiro") return status === "Nota emitida";
  if (perfil === "PCP/Logística") return ["Novo pedido", "Pago", "Vai produzir", "Em produção", "Pronto para faturar"].includes(status);
  if (perfil === "Faturamento") return ["Pronto para faturar", "Nota emitida"].includes(status);
  if (perfil === "Logística") return ["Nota emitida", "Separado para entrega", "Enviado", "Finalizado"].includes(status);
  return false;
}

export function calcularResumo(pedidos) {
  const pedidosAtivos = pedidos.filter((p) => p.status !== "Cancelado");
  return {
    novos: pedidosAtivos.filter((p) => p.status === "Novo pedido").length,
    aguardando: pedidosAtivos.filter((p) => p.status === "Aguardando pagamento").length,
    vaiProduzir: pedidosAtivos.filter((p) => p.status === "Vai produzir").length,
    producao: pedidosAtivos.filter((p) => p.status === "Em produção").length,
    faturar: pedidosAtivos.filter((p) => p.status === "Pronto para faturar").length,
    notasEmitidas: pedidosAtivos.filter((p) => p.status === "Nota emitida").length,
    financeiroPago: pedidosAtivos.filter((p) => p.status === "Nota emitida" && p.statusFinanceiro === "Pago").length,
    financeiroPendente: pedidosAtivos.filter((p) => p.status === "Nota emitida" && p.statusFinanceiro !== "Pago").length,
    cancelados: pedidos.filter((p) => p.status === "Cancelado").length,
    total: pedidosAtivos.reduce((acc, p) => acc + valorTotalPedido(p), 0),
  };
}

export function filtrarPedidos(pedidos, busca, statusFiltro, vendedorFiltro, perfil, financeiroFiltro = "Todos") {
  return pedidos.filter((p) => {
    const textoBusca = `${p.id} ${p.cliente} ${p.cnpj} ${p.cep} ${p.logradouro} ${p.numero} ${p.bairro} ${p.cidade} ${p.uf} ${p.produto} ${p.tampa} ${p.cor} ${p.status} ${p.pagamento} ${p.statusFinanceiro} ${p.transporte} ${p.tipoFrete} ${p.detalheFOB} ${p.faturamento} ${p.tipoEntrega} ${p.pcpPrevisaoProducao} ${p.pcpPrevisaoPronto} ${p.pcpQuantidadeProduzida} ${p.pcpObservacoes}`.toLowerCase();
    const matchBusca = textoBusca.includes(String(busca || "").toLowerCase());
    const matchStatus = statusFiltro === "Todos" || p.status === statusFiltro;
    const matchVendedor = vendedorFiltro === "Todos" || p.vendedor === vendedorFiltro;
    const matchPerfil = podeVerPedidoPorPerfil(perfil, p.status);
    const matchFinanceiro = financeiroFiltro === "Todos" || p.statusFinanceiro === financeiroFiltro;
    return matchBusca && matchStatus && matchVendedor && matchPerfil && matchFinanceiro;
  });
}

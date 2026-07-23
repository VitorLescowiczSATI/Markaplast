export function valorTotalPedido(pedido) {
  return (Number(pedido.valor || 0) + Number(pedido.valorTampa || 0)) * Number(pedido.quantidade || 0);
}

// Travas do pedido: campos obrigatórios para o pedido chegar completo no PCP.
export const PEDIDO_CAMPOS_OBRIGATORIOS = [
  ["cliente", "Cliente"],
  ["produto", "Produto"],
  ["cor", "Cor"],
  ["tampa", "Tampa"],
  ["quantidade", "Quantidade"],
  ["vendedor", "Vendedor"],
];

export function camposFaltandoPedido(form) {
  return PEDIDO_CAMPOS_OBRIGATORIOS.filter(([campo]) => {
    if (campo === "quantidade") return !(Number(form?.quantidade) > 0);
    return !String(form?.[campo] || "").trim();
  }).map(([, label]) => label);
}

// Pedido é considerado "faturado/realizado" a partir da emissão da nota.
export const STATUS_FATURADO = ["Nota emitida", "Separado para entrega", "Enviado", "Finalizado"];

function infoData(dataStr) {
  const [ano, mes, dia] = String(dataStr || "").split("-").map(Number);
  const mesIdx = (mes || 1) - 1;
  return { ano: ano || 0, mes: mesIdx, dia: dia || 0, trimestre: Math.floor(mesIdx / 3) };
}

// Soma o faturado por período (diária/mensal/trimestral) da empresa e por vendedor.
export function realizadoMetas(pedidos = [], hoje = new Date()) {
  const H = { ano: hoje.getFullYear(), mes: hoje.getMonth(), dia: hoje.getDate(), trimestre: Math.floor(hoje.getMonth() / 3) };
  const empresa = { diaria: 0, mensal: 0, trimestral: 0 };
  const porVendedor = {};

  pedidos.forEach((pedido) => {
    if (!STATUS_FATURADO.includes(pedido.status)) return;
    // Fatura pela data de emissão da nota; cai na data do pedido só para faturados legados (sem dataEmissao).
    const D = infoData(pedido.dataEmissao || pedido.data);
    if (D.ano !== H.ano) return;
    const total = valorTotalPedido(pedido);
    const vendedor = pedido.vendedor || "Não informado";
    if (!porVendedor[vendedor]) porVendedor[vendedor] = { diaria: 0, mensal: 0, trimestral: 0 };

    const noTrimestre = D.trimestre === H.trimestre;
    const noMes = D.mes === H.mes;
    const noDia = noMes && D.dia === H.dia;
    if (noTrimestre) {
      empresa.trimestral += total;
      porVendedor[vendedor].trimestral += total;
    }
    if (noMes) {
      empresa.mensal += total;
      porVendedor[vendedor].mensal += total;
    }
    if (noDia) {
      empresa.diaria += total;
      porVendedor[vendedor].diaria += total;
    }
  });

  return { empresa, porVendedor };
}

export function percentualMeta(realizado, meta) {
  const alvo = Number(meta || 0);
  if (alvo <= 0) return 0;
  return Math.round((Number(realizado || 0) / alvo) * 100);
}

// Normaliza um valor legado (texto livre) contra a lista fixa de opções (cor/tampa),
// ignorando caixa e um prefixo "Tampa ". Retorna a string canônica ou "" se não casar.
export function normalizarOpcao(valor, opcoes = []) {
  const v = String(valor || "").trim().toLowerCase();
  if (!v) return "";
  const direto = opcoes.find((opcao) => opcao.toLowerCase() === v);
  if (direto) return direto;
  const semPrefixo = v.replace(/^tampa\s+/, "");
  return opcoes.find((opcao) => opcao.toLowerCase() === semPrefixo) || "";
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
  if (["Nota emitida", "Finalizado", "Enviado"].includes(status)) {
    return "bg-green-50 text-green-800 border-green-200";
  }
  if (["Aguardando pagamento", "Novo pedido"].includes(status)) {
    return "bg-amber-50 text-amber-800 border-amber-200";
  }
  if (["A produzir", "Em produção", "Prontos", "Vai produzir", "Pronto para faturar"].includes(status)) {
    return "bg-sky-50 text-sky-800 border-sky-200";
  }
  if (["Pago", "Pronto para retirada", "Pronto para o envio", "Separado para entrega"].includes(status)) {
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
  if (perfil === "Comercial") return true;
  if (perfil === "Financeiro") return status === "Nota emitida";
  if (perfil === "PCP") return ["Novo pedido", "Pago", "A produzir", "Em produção", "Prontos"].includes(status);
  if (perfil === "Faturamento") return ["Pronto para retirada", "Pronto para o envio", "Nota emitida"].includes(status);
  if (perfil === "Logística") return ["Prontos", "Pronto para retirada", "Pronto para o envio"].includes(status);
  return false;
}

export function calcularResumo(pedidos) {
  const pedidosAtivos = pedidos.filter((p) => p.status !== "Cancelado");
  return {
    novos: pedidosAtivos.filter((p) => p.status === "Novo pedido").length,
    aguardando: pedidosAtivos.filter((p) => p.status === "Aguardando pagamento").length,
    vaiProduzir: pedidosAtivos.filter((p) => ["A produzir", "Vai produzir"].includes(p.status)).length,
    producao: pedidosAtivos.filter((p) => p.status === "Em produção").length,
    faturar: pedidosAtivos.filter((p) => ["Pronto para retirada", "Pronto para o envio", "Pronto para faturar"].includes(p.status)).length,
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

export const setores = ["Inteligência", "Comercial", "Clientes", "Estoque", "PCP", "Logística", "Faturamento", "Financeiro", "Fiscal"];

export const statusList = [
  "Novo pedido",
  "Aguardando pagamento",
  "Pago",
  "A produzir",
  "Em produção",
  "Prontos",
  "Pronto para retirada",
  "Pronto para o envio",
  "Nota emitida",
  "Cancelado",
];

export const financeiroStatusList = ["Aguardando pagamento", "Pago"];

export const vendedores = ["Arthur", "Ingrid", "Nelso", "Tadeu", "Martini", "Marcos", "Silvana"];

export const produtos = [
  "1L sem alça",
  "1L redondo",
  "1L oval",
  "1L agro",
  "1L dosador",
  "2L redondo",
  "2L quadrado",
  "3L",
  "5L M2",
  "5L M4",
  "5L M6",
  "5L M8",
  "20L",
  "25L",
  "Pote de soda 300g",
  "Pote de soda 500g",
  "Pote de soda 1kg",
  "Pote normal 500g",
];

export const tiposFaturamento = ["NF Gimak", "NF Markaplast", "ROM Gpack"];
export const tiposEntrega = ["Retirada na empresa", "Entrega CIF"];
export const tiposFrete = ["CIF", "FOB"];

// Listas-base para as travas do pedido (cor/tampa). Ajustar com a lista real do cliente.
export const cores = ["Natural", "Branco", "Preto", "Azul", "Vermelho", "Verde", "Amarelo", "Cinza"];
export const tampas = ["Lacre", "Rosca", "Dosadora", "Flip top", "Batoque", "Sem tampa"];
export const alcaOpcoes = ["nao", "sim"];

export const emptyForm = {
  cliente: "",
  cnpj: "",
  cep: "",
  logradouro: "",
  numero: "",
  bairro: "",
  cidade: "",
  uf: "",
  produto: "",
  tampa: "",
  cor: "",
  quantidade: "",
  valor: "",
  valorTampa: "",
  pagamento: "",
  vendedor: "",
  transporte: "",
  tipoFrete: "",
  detalheFOB: "",
  faturamento: "",
  tipoEntrega: "",
  observacoes: "",
};

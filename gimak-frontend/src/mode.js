// Qual "sistema" esta aba está rodando, decidido uma vez pelo caminho da URL.
// O Render reescreve qualquer rota para o index.html, então não precisa de config.
const caminho = window.location.pathname.replace(/\/+$/, "").toLowerCase();

export const IS_APRESENTACAO = caminho === "/apresentacao";
export const IS_DEMO = caminho === "/demo";

// Na demonstração quem vê é o cliente em potencial: o produto é o PCP na mão e a
// fábrica é fictícia. Fora dela, o sistema continua sendo o da Gimak.
export const MARCA = IS_DEMO
  ? { produto: "PCP na mão", empresa: "Metalúrgica Modelo" }
  : { produto: "Gimak PCP", empresa: "Gimak" };

// WhatsApp que recebe quem clica em "quero na minha fábrica" na demonstração.
// Só dígitos, com DDI e DDD (ex.: 5547999999999). Vazio esconde o botão.
export const CONTATO_WHATSAPP = "";

// Qual "sistema" esta aba está rodando, decidido uma vez pelo caminho da URL.
// O Render reescreve qualquer rota para o index.html, então não precisa de config.
const caminho = window.location.pathname.replace(/\/+$/, "").toLowerCase();

export const IS_APRESENTACAO = caminho === "/apresentacao";
export const IS_DEMO = caminho === "/demo";

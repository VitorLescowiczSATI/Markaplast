import React from "react";
import { createRoot } from "react-dom/client";

import App from "./App.jsx";
import { Apresentacao } from "./Apresentacao.jsx";
import "./styles.css";

// A apresentação é pública e fica fora do app: quem abre /apresentacao não passa pelo login.
// O Render reescreve qualquer rota para o index.html, então basta olhar o caminho aqui.
const caminho = window.location.pathname.replace(/\/+$/, "").toLowerCase();
const ehApresentacao = caminho === "/apresentacao";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {ehApresentacao ? <Apresentacao /> : <App />}
  </React.StrictMode>,
);

import React from "react";
import { createRoot } from "react-dom/client";

import App from "./App.jsx";
import { Apresentacao } from "./Apresentacao.jsx";
import { DemoBanner } from "./DemoBanner.jsx";
import { IS_APRESENTACAO, IS_DEMO } from "./mode";
import "./styles.css";

// A apresentação é pública e fica fora do app: quem abre /apresentacao não passa pelo login.
// Em /demo o app é o mesmo, só que falando com dados fictícios em memória (demoApi.js).
createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {IS_APRESENTACAO ? <Apresentacao /> : <>{IS_DEMO && <DemoBanner />}<App /></>}
  </React.StrictMode>,
);

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { Printer, X } from "lucide-react";

import { MARCA } from "./mode";
import "./validation-sheet.css";

/** Folha de "Equipamento validado" que sai ao concluir o projeto. Vai direto para a impressão. */
export function ValidationSheet({ project, onClose }) {
  // O App re-renderiza a cada segundo (relógio); o efeito roda só ao abrir para não reimprimir.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  useEffect(() => {
    document.body.classList.add("printing-sheet");
    // Espera o layout montar antes de abrir a janela de impressão.
    const timer = setTimeout(() => window.print(), 350);
    const close = (event) => event.key === "Escape" && onCloseRef.current();
    window.addEventListener("keydown", close);
    return () => { clearTimeout(timer); window.removeEventListener("keydown", close); document.body.classList.remove("printing-sheet"); };
  }, []);

  const concluido = project.concluidoEm ? new Date(project.concluidoEm) : new Date();
  return createPortal(
    <div className="validation-overlay">
      <div className="validation-toolbar">
        <button className="primary" onClick={() => window.print()}><Printer size={16} /> Imprimir</button>
        <button className="secondary" onClick={onClose}><X size={16} /> Fechar</button>
      </div>
      <article className="validation-sheet">
        <header><span>{MARCA.empresa}</span><small>Projeto {String(project.id).padStart(4, "0")}</small></header>
        <div className="validation-stamp">EQUIPAMENTO VALIDADO</div>
        <dl>
          <div><dt>Cliente</dt><dd>{project.cliente}</dd></div>
          <div><dt>Equipamento</dt><dd>{project.equipamento}</dd></div>
          {project.cidade && <div><dt>Cidade</dt><dd>{project.cidade}</dd></div>}
          <div><dt>Data da validação</dt><dd>{concluido.toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })}</dd></div>
        </dl>
        <footer>
          <span>Responsável pela validação</span>
          <span>Cliente</span>
        </footer>
      </article>
    </div>,
    document.body,
  );
}

import { useState } from "react";
import { FlaskConical, RotateCcw } from "lucide-react";

import { demoControls } from "./demoApi";
import "./demo.css";

// Selo fixo do modo demonstração. Fica flutuando no canto para caber até no modo TV,
// que ocupa a tela inteira. Trocar de perfil recarrega a página porque o App guarda
// o usuário logado em estado próprio.
export function DemoBanner() {
  const [users] = useState(() => demoControls.users());
  const [atual] = useState(() => demoControls.currentUsername());

  function trocar(username) {
    demoControls.switchUser(username);
    const perfil = users.find((item) => item.username === username)?.perfil;
    // Sair do perfil TV sem limpar o #tv deixaria o próximo perfil preso na tela da TV.
    window.location.hash = perfil === "TV" ? "tv" : "";
    window.location.reload();
  }

  function recomecar() {
    if (!window.confirm("Apagar o que você fez na demonstração e voltar aos dados iniciais?")) return;
    demoControls.reset();
    window.location.reload();
  }

  return (
    <aside className="demo-pill" aria-label="Modo demonstração">
      <span className="demo-pill-label"><FlaskConical size={16} /> Demonstração<small>dados fictícios, nada vai para a fábrica</small></span>
      <label className="demo-pill-profile">
        Ver como
        <select value={atual} onChange={(event) => trocar(event.target.value)}>
          {users.map((item) => <option key={item.username} value={item.username}>{item.nome} ({item.perfil})</option>)}
        </select>
      </label>
      <button type="button" onClick={recomecar} title="Voltar aos dados iniciais"><RotateCcw size={15} /> Recomeçar</button>
    </aside>
  );
}

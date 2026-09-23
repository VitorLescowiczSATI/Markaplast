import { useEffect, useState } from "react";
import { CheckCircle2, Circle, FlaskConical, MessageCircle, RotateCcw, X } from "lucide-react";

import { demoControls } from "./demoApi";
import { CONTATO_WHATSAPP, linkWhatsApp } from "./mode";
import "./demo.css";

const GUIA_KEY = "gimak.demo.guia";
const OPERADOR = "marcos";

const PASSOS = [
  {
    id: "iniciar",
    titulo: "Inicie uma tarefa",
    texto: "No quadro, abra uma tarefa em A fazer e clique em Iniciar. O cronômetro começa sozinho.",
  },
  {
    id: "operador",
    titulo: "Veja como o operador",
    texto: "Quem está na bancada só enxerga o quadro e os botões de situação.",
    acao: "Ver como operador",
  },
  {
    id: "tv",
    titulo: "Abra a TV da fábrica",
    texto: "O painel que fica na televisão do chão de fábrica e se atualiza sozinho.",
    acao: "Abrir a TV",
  },
];

function lerGuia() {
  try {
    const salvo = JSON.parse(window.localStorage.getItem(GUIA_KEY) || "null");
    if (salvo && Array.isArray(salvo.feitos)) return salvo;
  } catch {
    // Sem armazenamento o roteiro só não lembra o progresso.
  }
  return { feitos: [], aberto: true };
}

function gravarGuia(guia) {
  try {
    window.localStorage.setItem(GUIA_KEY, JSON.stringify(guia));
  } catch {
    // Idem.
  }
}

function BotaoContato({ grande = false }) {
  if (!CONTATO_WHATSAPP) return null;
  return (
    <a className={`demo-contato ${grande ? "demo-contato-grande" : ""}`} href={linkWhatsApp("a demonstração")} target="_blank" rel="noopener noreferrer">
      <MessageCircle size={grande ? 18 : 15} /> Quero na minha fábrica
    </a>
  );
}

// Selo fixo do modo demonstração, com o roteiro de três passos para quem abre o link
// sozinho. Fica flutuando no canto para caber até no modo TV, que ocupa a tela inteira.
// Trocar de perfil recarrega a página porque o App guarda o usuário em estado próprio.
export function DemoBanner() {
  const [users] = useState(() => demoControls.users());
  const [atual] = useState(() => demoControls.currentUsername());
  const [guia, setGuia] = useState(lerGuia);
  const [naTv, setNaTv] = useState(() => window.location.hash === "#tv");

  const perfilAtual = users.find((item) => item.username === atual)?.perfil;
  const feitos = new Set(guia.feitos);
  const concluido = PASSOS.every((passo) => feitos.has(passo.id));
  const passoAtual = PASSOS.find((passo) => !feitos.has(passo.id))?.id;

  function atualizar(proximo) {
    setGuia(proximo);
    gravarGuia(proximo);
  }

  function marcar(id, extra = {}) {
    const atualGuia = lerGuia();
    if (atualGuia.feitos.includes(id)) return atualizar({ ...atualGuia, ...extra });
    atualizar({ ...atualGuia, ...extra, feitos: [...atualGuia.feitos, id] });
  }

  useEffect(() => {
    const iniciou = () => marcar("iniciar");
    const hash = () => setNaTv(window.location.hash === "#tv");
    window.addEventListener("gimak:demo-iniciou", iniciou);
    window.addEventListener("hashchange", hash);
    return () => {
      window.removeEventListener("gimak:demo-iniciou", iniciou);
      window.removeEventListener("hashchange", hash);
    };
  }, []);

  function trocar(username) {
    demoControls.switchUser(username);
    const perfil = users.find((item) => item.username === username)?.perfil;
    // Sair do perfil TV sem limpar o #tv deixaria o próximo perfil preso na tela da TV.
    window.location.hash = perfil === "TV" ? "tv" : "";
    window.location.reload();
  }

  function agir(id) {
    if (id === "operador") {
      marcar("operador");
      trocar(OPERADOR);
    } else if (id === "tv") {
      marcar("tv", { aberto: false });
      window.location.hash = "tv";
    }
  }

  function recomecar() {
    if (!window.confirm("Apagar o que você fez na demonstração e voltar aos dados iniciais?")) return;
    demoControls.reset();
    gravarGuia({ feitos: [], aberto: true });
    window.location.reload();
  }

  // A TV ocupa a tela exata. O roteiro some ali e volta pelo botão do selo.
  const mostrarGuia = guia.aberto && !naTv && perfilAtual !== "TV";

  return (
    <div className="demo-dock">
      {mostrarGuia && (
        <section className="demo-guia" aria-label="Roteiro da demonstração">
          <header>
            <div>
              <strong>{concluido ? "Pronto, esse é o dia a dia" : "Conheça em 3 passos"}</strong>
              <small>{concluido ? "Pode continuar mexendo à vontade." : `Passo ${feitos.size + 1} de ${PASSOS.length}. Tudo aqui é fictício.`}</small>
            </div>
            <button type="button" className="demo-fechar" onClick={() => atualizar({ ...guia, aberto: false })} title="Fechar roteiro"><X size={16} /></button>
          </header>
          <ol>
            {PASSOS.map((passo) => {
              const feito = feitos.has(passo.id);
              return (
                <li key={passo.id} className={feito ? "feito" : passo.id === passoAtual ? "atual" : ""}>
                  {feito ? <CheckCircle2 size={19} /> : <Circle size={19} />}
                  <div>
                    <b>{passo.titulo}</b>
                    <p>{passo.texto}</p>
                    {passo.acao && !feito && <button type="button" onClick={() => agir(passo.id)}>{passo.acao}</button>}
                  </div>
                </li>
              );
            })}
          </ol>
          {concluido && <BotaoContato grande />}
        </section>
      )}
      <aside className="demo-pill" aria-label="Modo demonstração">
        <span className="demo-pill-label"><FlaskConical size={16} /> Demonstração<small>dados fictícios</small></span>
        <label className="demo-pill-profile">
          Ver como
          <select value={atual} onChange={(event) => trocar(event.target.value)}>
            {users.map((item) => <option key={item.username} value={item.username}>{item.nome} ({item.perfil})</option>)}
          </select>
        </label>
        {!mostrarGuia && (
          <button type="button" onClick={() => { setNaTv(false); atualizar({ ...guia, aberto: true }); if (window.location.hash === "#tv" && perfilAtual !== "TV") window.location.hash = ""; }}>
            Roteiro {feitos.size}/{PASSOS.length}
          </button>
        )}
        <button type="button" onClick={recomecar} title="Voltar aos dados iniciais"><RotateCcw size={15} /> Recomeçar</button>
        <BotaoContato />
      </aside>
    </div>
  );
}

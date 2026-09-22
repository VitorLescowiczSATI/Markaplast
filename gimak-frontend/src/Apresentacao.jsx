import { useEffect } from "react";
import {
  BarChart3,
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Clock3,
  Factory,
  Monitor,
  PauseCircle,
  PlayCircle,
  ServerCog,
  ShieldCheck,
  Timer,
  Wrench,
} from "lucide-react";

import "./apresentacao.css";

const DORES = [
  "O que cada um está fazendo agora, sem levantar e perguntar.",
  "Por que uma atividade parou. O motivo não ficava registrado em lugar nenhum.",
  "Onde a montagem realmente consome as horas. O tempo por etapa não era medido.",
  "Se alguém ficou sem tarefa no dia, antes do dia começar.",
  "O que ficou faltando numa assistência. A ficha era de papel e a pendência se perdia.",
];

const TELAS = [
  {
    icon: Factory,
    nome: "Painel da fábrica",
    texto:
      "O quadro do dia em quatro colunas: a fazer, em execução, não realizado e concluído. Filtra por colaborador e por hoje ou pela semana inteira.",
    destaque: "O card de quem está executando mostra o cronômetro correndo.",
  },
  {
    icon: CalendarDays,
    nome: "Calendário",
    texto:
      "Em modo mês, a grade inteira colorida pela situação. Em semana por pessoa, uma linha por quem executa e uma coluna por dia.",
    destaque: "O dia vazio fica hachurado, e é assim que o PCP enxerga quem ficou sem tarefa.",
  },
  {
    icon: BriefcaseBusiness,
    nome: "Projetos",
    texto:
      "Cada equipamento vendido é um projeto, com cliente e nome do equipamento. Mostra o que está pendente, o que foi realizado e o tempo gasto em cada etapa.",
    destaque: "Projeto encerrado sai do andamento e volta pelo filtro de concluídos. Dá para reabrir.",
  },
  {
    icon: Wrench,
    nome: "Assistências e instalações",
    texto:
      "O PCP agenda com tipo, cliente, endereço, técnico, data de ida, hora de sair e hora prevista de volta. O técnico clica em Estou saindo para o atendimento e a hora real fica registrada.",
    destaque: "Na volta ele escreve o relatório do que foi feito e conclui.",
  },
  {
    icon: ClipboardList,
    nome: "Pendências",
    texto:
      "O técnico foi, resolveu, mas faltou um componente. Isso morria no relatório. Agora vira um item aberto, com contador na aba.",
    destaque: "O administrador acompanha, escreve como foi resolvido e fecha.",
  },
  {
    icon: Monitor,
    nome: "Modo TV",
    texto:
      "Painel somente leitura para a televisão do chão de fábrica: o que está em execução com cronômetro, as pausas, o plano do dia, os projetos e o gráfico dos últimos sete dias.",
    destaque: "Atualiza sozinho a cada trinta segundos e mantém a tela acesa.",
  },
  {
    icon: BarChart3,
    nome: "Indicadores",
    texto:
      "Entregas, taxa de conclusão, entregas no prazo, pendências vencidas, motivos de pausa, ranking por responsável e uso dos apontamentos, com período selecionável.",
    destaque: "O critério de cálculo fica escrito na própria tela, para o número não virar discussão.",
  },
];

const PERMISSOES = [
  ["Ver quadro, projetos e assistências", true, true, true, false],
  ["Apontar tarefa e concluir assistência", true, true, true, false],
  ["Criar tarefa, projeto e assistência", true, true, false, false],
  ["Concluir e reabrir projeto", true, true, false, false],
  ["Registrar e resolver pendência", true, true, true, false],
  ["Excluir tarefa, assistência e pendência", true, false, false, false],
  ["Indicadores e gestão de usuários", true, false, false, false],
];

const ROADMAP = [
  {
    nome: "Anexo de arquivo na tarefa",
    texto: "Por exemplo a lista de corte de material. Depende de armazenamento de arquivo, que o plano atual não tem.",
  },
  {
    nome: "Aplicativo no celular",
    texto: "As telas já funcionam no navegador do celular. Falta a notificação e o campo de foto na assistência.",
  },
  {
    nome: "Mais de um responsável na tarefa",
    texto: "Parado por decisão, até definir o que acontece quando um sai e o outro continua.",
  },
  {
    nome: "Ranking visível para a fábrica",
    texto: "O ranking já existe, mas hoje só o administrador enxerga.",
  },
];

function Sim() {
  return <span className="lp-sim"><CheckCircle2 size={16} /> sim</span>;
}

function Nao() {
  return <span className="lp-nao">não</span>;
}

export function Apresentacao() {
  useEffect(() => {
    document.title = "Gimak PCP — como o sistema funciona";
    const alvos = document.querySelectorAll("[data-reveal]");
    if (!("IntersectionObserver" in window)) {
      alvos.forEach((item) => item.classList.add("is-visible"));
      return undefined;
    }
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      }),
      { rootMargin: "0px 0px -80px 0px", threshold: 0.08 },
    );
    alvos.forEach((item) => observer.observe(item));
    return () => observer.disconnect();
  }, []);

  return (
    <div className="lp">
      <header className="lp-nav">
        <a className="lp-brand" href="#topo">
          <span className="brand-mark"><Factory size={22} /></span>
          <div><strong>Gimak PCP</strong><small>Planejamento e controle da produção</small></div>
        </a>
        <nav className="lp-links">
          <a href="#dor">A dor</a>
          <a href="#principio">O princípio</a>
          <a href="#telas">As telas</a>
          <a href="#acesso">Acesso</a>
          <a href="#infra">Infraestrutura</a>
        </nav>
        <a className="lp-cta" href="/">Entrar no sistema</a>
      </header>

      <main id="topo">
        <section className="lp-hero">
          <div className="lp-hero-text">
            <p className="lp-eyebrow">Gimak</p>
            <h1>PCP na mão de quem executa</h1>
            <p className="lp-lead">
              O andamento da fábrica em um lugar só, do apontamento na bancada ao indicador da diretoria,
              sem burocratizar o trabalho de quem faz.
            </p>
            <div className="lp-hero-actions">
              <a className="lp-cta lp-cta-lg" href="/">Entrar no sistema</a>
              <a className="lp-ghost" href="#telas">Ver as telas</a>
            </div>
          </div>
          <figure className="lp-mock" aria-label="Exemplo do quadro do dia">
            <div className="lp-mock-bar"><span /><span /><span /></div>
            <div className="lp-mock-board">
              <div className="lp-mock-col">
                <header><Clock3 size={15} /> A fazer <i>6</i></header>
                <div className="lp-mock-card">
                  <span className="lp-op">OS 1047</span>
                  <b>Usinagem dos flanges</b>
                  <em>Envasadora GK 500</em>
                </div>
                <div className="lp-mock-card">
                  <span className="lp-op">OS 1051</span>
                  <b>Pintura da base</b>
                </div>
              </div>
              <div className="lp-mock-col">
                <header><PlayCircle size={15} /> Em execução <i>3</i></header>
                <div className="lp-mock-card">
                  <span className="lp-op">OS 1042</span>
                  <b>Montagem do carrossel</b>
                  <em>Envasadora GK 500</em>
                  <span className="lp-timer">● Contando <strong>01:42:18</strong></span>
                </div>
              </div>
              <div className="lp-mock-col">
                <header><PauseCircle size={15} /> Não realizado <i>1</i></header>
                <div className="lp-mock-card lp-mock-card-red">
                  <span className="lp-op">OS 1044</span>
                  <b>Solda do quadro</b>
                  <span className="lp-motivo">Motivo: faltou material de solda</span>
                </div>
              </div>
              <div className="lp-mock-col">
                <header><CheckCircle2 size={15} /> Concluído <i>9</i></header>
                <div className="lp-mock-card lp-mock-card-done">
                  <span className="lp-op">OS 1031</span>
                  <b>Corte das chapas</b>
                  <span className="lp-timer lp-timer-off">Tempo registrado <strong>03:10:05</strong></span>
                </div>
              </div>
            </div>
            <figcaption>Exemplo do quadro do dia, com dados de demonstração.</figcaption>
          </figure>
        </section>

        <section className="lp-section lp-section-light" id="dor" data-reveal>
          <p className="lp-eyebrow lp-eyebrow-dark">Antes</p>
          <h2>O que ninguém conseguia responder</h2>
          <p className="lp-sub">
            O andamento da fábrica vivia na cabeça das pessoas e no WhatsApp. Se a diretoria perguntasse
            por que atrasou, a resposta dependia de alguém lembrar.
          </p>
          <ul className="lp-dores">
            {DORES.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>

        <section className="lp-principio" id="principio" data-reveal>
          <p className="lp-eyebrow lp-eyebrow-navy">O princípio de projeto</p>
          <h2>Abrir a atividade, clicar em Iniciar e, no fim, clicar em Concluir.</h2>
          <p className="lp-sub lp-sub-navy">
            Quem está na fábrica não é usuário de computador e não vai preencher formulário. Pausar e marcar
            como não realizada pedem uma justificativa em uma frase, porque é exatamente essa informação que
            faltava antes. Nada além disso.
          </p>
          <div className="lp-passos">
            <div><PlayCircle size={26} /><b>Iniciar</b><span>Um clique ao pegar a atividade</span></div>
            <div><PauseCircle size={26} /><b>Pausar</b><span>Uma frase dizendo o motivo</span></div>
            <div><CheckCircle2 size={26} /><b>Concluir</b><span>Um clique ao terminar</span></div>
          </div>
          <p className="lp-derivado">
            Quem fez, a hora, o cronômetro, o histórico e os indicadores o sistema deriva sozinho desses cliques.
            O operador nunca digita hora, nunca escolhe data e nunca preenche relatório de produção.
          </p>
        </section>

        <section className="lp-section" id="telas" data-reveal>
          <p className="lp-eyebrow lp-eyebrow-dark">As telas</p>
          <h2>Sete telas, cada uma com um trabalho</h2>
          <div className="lp-telas">
            {TELAS.map(({ icon: Icon, nome, texto, destaque }) => (
              <article className="lp-tela" key={nome}>
                <span className="lp-tela-icon"><Icon size={22} /></span>
                <h3>{nome}</h3>
                <p>{texto}</p>
                <p className="lp-tela-destaque">{destaque}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section lp-section-light" id="acesso" data-reveal>
          <p className="lp-eyebrow lp-eyebrow-dark">Acesso</p>
          <h2>Perfis e permissões</h2>
          <p className="lp-sub">
            O perfil TV é uma conta cega, feita para ficar logada na televisão. Sessão de trinta dias e
            nenhum acesso a tarefa, projeto ou usuário.
          </p>
          <div className="lp-tabela-wrap">
            <table className="lp-tabela">
              <thead>
                <tr><th>O que faz</th><th>Admin</th><th>PCP</th><th>Fábrica</th><th>TV</th></tr>
              </thead>
              <tbody>
                {PERMISSOES.map(([label, ...perfis]) => (
                  <tr key={label}>
                    <td>{label}</td>
                    {perfis.map((pode, indice) => <td key={indice}>{pode ? <Sim /> : <Nao />}</td>)}
                  </tr>
                ))}
                <tr>
                  <td>Modo TV</td>
                  <td><Sim /></td><td><Sim /></td><td><Sim /></td>
                  <td><span className="lp-so-isso">só isso</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="lp-section" id="pordentro" data-reveal>
          <p className="lp-eyebrow lp-eyebrow-dark">Por dentro</p>
          <h2>Todo clique vira registro</h2>
          <div className="lp-duplo">
            <article>
              <span className="lp-tela-icon"><ShieldCheck size={22} /></span>
              <h3>O apontamento</h3>
              <p>
                Toda mudança de situação grava a situação anterior, a nova, quem fez, quando e a justificativa
                quando existe. É daí que sai o histórico da atividade e é daí que saem os indicadores.
              </p>
            </article>
            <article>
              <span className="lp-tela-icon"><Timer size={22} /></span>
              <h3>O cronômetro</h3>
              <p>
                Acumula em segundos. Iniciar marca o começo, pausar soma o intervalo ao acumulado, retomar
                recomeça a contagem. O operador nunca vê nem digita esse número, só o resultado.
              </p>
            </article>
          </div>
          <p className="lp-nota">
            Clicar em Iniciar ou Concluir duas vezes não tem efeito, de propósito, para não mexer no tempo nem
            na data de conclusão. Já Não realizada pode ser reenviada, porque aí o objetivo é corrigir a justificativa.
          </p>
        </section>

        <section className="lp-section lp-section-light" id="infra" data-reveal>
          <p className="lp-eyebrow lp-eyebrow-dark">Infraestrutura</p>
          <h2>Roda no que já estava contratado</h2>
          <div className="lp-infra">
            <div>
              <header><ServerCog size={18} /> API</header>
              <p className="lp-infra-mk">Markaplast <code>/api/...</code></p>
              <p className="lp-infra-gk">Gimak <code>/api/gimak/...</code></p>
            </div>
            <div>
              <header><ServerCog size={18} /> PostgreSQL</header>
              <p className="lp-infra-mk">Markaplast <code>banco giras</code></p>
              <p className="lp-infra-gk">Gimak <code>banco gimak_pcp</code></p>
            </div>
            <div>
              <header><ServerCog size={18} /> Sites</header>
              <p className="lp-infra-mk">Markaplast <code>giras-web</code></p>
              <p className="lp-infra-gk">Gimak <code>gimak-pcp-web</code></p>
            </div>
          </div>
          <div className="lp-zero">
            <strong>Custo adicional de infraestrutura: zero</strong>
            <p>
              Reaproveita a API e o banco já contratados, e o site estático é gratuito. Banco lógico separado,
              autenticação com segredo próprio, e nada em comum com a Markaplast além da infraestrutura.
            </p>
          </div>
        </section>

        <section className="lp-section" id="proximo" data-reveal>
          <p className="lp-eyebrow lp-eyebrow-dark">Próximos passos</p>
          <h2>O que ainda não existe</h2>
          <div className="lp-roadmap">
            {ROADMAP.map((item) => (
              <article key={item.nome}>
                <h3>{item.nome}</h3>
                <p>{item.texto}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-fim" data-reveal>
          <h2>O que a fábrica está fazendo agora cabe em uma tela.</h2>
          <p>
            Sem formulário para quem executa, sem planilha para quem planeja e sem depender de alguém lembrar
            para quem cobra.
          </p>
          <a className="lp-cta lp-cta-lg" href="/">Entrar no sistema</a>
        </section>
      </main>

      <footer className="lp-rodape">
        <span><Factory size={17} /> Gimak PCP</span>
        <span>gimak-pcp-web.onrender.com</span>
      </footer>
    </div>
  );
}

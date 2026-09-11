import { useCallback, useEffect, useRef, useState } from "react";
import { Activity, ArrowLeft, BarChart3, CheckCircle2, Clock3, Expand, Factory, PauseCircle, RefreshCw, TriangleAlert, Users } from "lucide-react";
import { api } from "./api";
import "./production-views.css";

const ZONE = "America/Sao_Paulo";
const dateKey = (value = new Date()) => new Intl.DateTimeFormat("en-CA", { timeZone: ZONE, year: "numeric", month: "2-digit", day: "2-digit" }).format(value);
const dateLabel = (value) => value ? new Date(value.length === 10 ? `${value}T12:00:00-03:00` : value).toLocaleDateString("pt-BR", { timeZone: ZONE, day: "2-digit", month: "2-digit" }) : "—";
const clockLabel = (value) => value ? new Date(value).toLocaleTimeString("pt-BR", { timeZone: ZONE, hour: "2-digit", minute: "2-digit" }) : "—";
const percent = (value) => value == null ? "—" : `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
const duration = (seconds) => {
  const n = Math.max(0, Math.floor(seconds || 0));
  return [Math.floor(n / 3600), Math.floor(n % 3600 / 60), n % 60].map(v => String(v).padStart(2, "0")).join(":");
};
const STATUS = { todo: "A fazer", doing: "Em execução", paused: "Pausada", blocked: "Não realizada", done: "Concluída" };

function useLiveData(fetcher) {
  const [state, setState] = useState({ data: null, receivedAt: null, error: "", loading: true });
  const [retry, setRetry] = useState(0);
  const refresh = useCallback(() => setRetry(n => n + 1), []);
  useEffect(() => {
    let alive = true;
    let timer;
    const controller = new AbortController();
    const load = async () => {
      try {
        const data = await fetcher(controller.signal);
        if (alive) setState({ data, receivedAt: Date.now(), error: "", loading: false });
      } catch (error) {
        if (alive && error.name !== "AbortError") setState(old => ({ ...old, error: error.message || "Falha de conexão", loading: false }));
      } finally {
        if (alive) timer = setTimeout(load, 30000);
      }
    };
    setState({ data: null, receivedAt: null, error: "", loading: true });
    load();
    return () => { alive = false; clearTimeout(timer); controller.abort(); };
  }, [fetcher, retry]);
  return { ...state, refresh };
}

function Connection({ live }) {
  return <div className={`pv-connection ${live.error ? "is-stale" : ""}`} role="status">
    <span className="pv-live-dot" />
    {live.error ? `Sem atualização${live.receivedAt ? ` desde ${clockLabel(live.receivedAt)}` : ""}. Verifique a conexão.` : live.receivedAt ? `Atualizado às ${clockLabel(live.receivedAt)} · a cada 30 s` : "Conectando…"}
    <button onClick={live.refresh} aria-label="Atualizar indicadores"><RefreshCw size={15} /></button>
  </div>;
}

function Metric({ label, value, detail, tone = "", icon: Icon = Activity }) {
  return <article className={`pv-metric ${tone}`}><span><Icon size={19} />{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</article>;
}

function DailyChart({ series = [], compact = false }) {
  const max = Math.max(1, ...series.flatMap(item => [item.planejadas, item.concluidas]));
  return <div className={`pv-daily ${compact ? "compact" : ""}`}>
    <div className="pv-chart-legend"><span><i /> Planejadas</span><span><i /> Concluídas</span></div>
    <div className="pv-bars" role="img" aria-label="Tarefas planejadas e concluídas por dia">
      {series.map(item => <div className="pv-bar-day" key={item.data} title={`${dateLabel(item.data)}: ${item.planejadas} planejadas, ${item.concluidas} concluídas`}>
        <div className="pv-bar-pair"><div><b>{item.planejadas}</b><i style={{ height: `${item.planejadas / max * 100}%` }} /></div><div><b>{item.concluidas}</b><i style={{ height: `${item.concluidas / max * 100}%` }} /></div></div>
        <small>{dateLabel(item.data)}</small>
      </div>)}
    </div>
  </div>;
}

function Progress({ value }) {
  return <span className="pv-progress" role="progressbar" aria-label="Progresso de conclusão" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value ?? 0}><i style={{ width: `${value ?? 0}%` }} /></span>;
}

function initialPeriod(kind) {
  const today = dateKey();
  const start = new Date(`${today}T12:00:00-03:00`);
  if (kind === "week") start.setUTCDate(start.getUTCDate() - ((start.getUTCDay() + 6) % 7));
  if (kind === "month") start.setUTCDate(1);
  return { inicio: dateKey(start), fim: today };
}

export function AdminIndicators() {
  const [preset, setPreset] = useState("week");
  const [period, setPeriod] = useState(() => initialPeriod("week"));
  const [draft, setDraft] = useState(period);
  const [validation, setValidation] = useState("");
  const [sort, setSort] = useState("concluidas");
  const fetcher = useCallback(signal => api.getIndicators(period.inicio, period.fim, { signal }), [period]);
  const live = useLiveData(fetcher);
  const data = live.data;
  function selectPreset(key) {
    setPreset(key); setValidation("");
    if (key !== "custom") { const next = initialPeriod(key); setPeriod(next); setDraft(next); }
  }
  function applyPeriod(event) {
    event.preventDefault();
    const days = (new Date(draft.fim) - new Date(draft.inicio)) / 86400000;
    if (!draft.inicio || !draft.fim || days < 0 || days >= 366) { setValidation("Escolha um intervalo válido de até 366 dias."); return; }
    setValidation(""); setPeriod({ ...draft });
  }
  const ranked = [...(data?.ranking || [])].sort((a, b) => (b[sort] ?? -1) - (a[sort] ?? -1) || a.nome.localeCompare(b.nome));
  const summary = data?.resumo;
  return <main className="page pv-admin">
    <section className="pv-admin-title"><div><p className="eyebrow">GESTÃO DA PRODUÇÃO</p><h1>Indicadores da fábrica</h1><p>Entregas, prazos e participação nos apontamentos.</p></div><span className="pv-private"><Users size={16} /> Exclusivo do administrador</span></section>
    <section className="pv-toolbar"><div className="segmented">{[["today", "Hoje"], ["week", "Esta semana"], ["month", "Este mês"], ["custom", "Personalizado"]].map(([key, label]) => <button key={key} className={preset === key ? "active" : ""} onClick={() => selectPreset(key)}>{label}</button>)}</div><Connection live={live} /></section>
    {preset === "custom" && <form className="pv-date-form" onSubmit={applyPeriod}><label>De<input type="date" required value={draft.inicio} onChange={e => setDraft({ ...draft, inicio: e.target.value })} /></label><label>Até<input type="date" required value={draft.fim} onChange={e => setDraft({ ...draft, fim: e.target.value })} /></label><button className="primary">Aplicar período</button>{validation && <span role="alert">{validation}</span>}</form>}
    {!data && <div className="pv-empty" role="status">{live.error ? "Não foi possível carregar os indicadores. Tente atualizar." : "Calculando indicadores…"}</div>}
    {data && <>
      <p className="pv-scope">Tarefas planejadas entre {dateLabel(data.periodo.inicio)} e {dateLabel(data.periodo.fim)} · prazos no horário de Brasília.</p>
      <section className="pv-metrics">
        <Metric label="Planejadas" value={summary.planejadas} detail="Tarefas do período selecionado" icon={BarChart3} />
        <Metric label="Concluídas" value={summary.concluidas} detail={`${percent(summary.taxaConclusao)} das ${summary.planejadas} planejadas`} tone="green" icon={CheckCircle2} />
        <Metric label="Entregas no prazo" value={percent(summary.taxaNoPrazo)} detail={`${summary.concluidasNoPrazo} de ${summary.concluidasComPrazoConhecido} conclusões com data conhecida`} tone="blue" icon={Clock3} />
        <Metric label="Atrasos em aberto" value={summary.atrasadasEmAberto} detail={`${summary.atrasadasNoPeriodo} do período · inclui pendências anteriores`} tone="red" icon={TriangleAlert} />
      </section>
      <section className="pv-middle-grid"><article className="pv-panel"><header><h2>Planejamento e entregas</h2><span>{dateLabel(period.inicio)} — {dateLabel(period.fim)}</span></header><DailyChart series={data.serieDiaria} /><p className="pv-note">Conclusões pela data de entrega final; podem vir de tarefas planejadas em outros dias.</p></article>
        <article className="pv-panel"><header><h2>Situação do período</h2></header><div className="pv-state-list">{[["aFazer", "A fazer", "todo"], ["emExecucao", "Em execução", "doing"], ["pausadas", "Pausadas", "paused"], ["naoRealizadas", "Não realizadas", "blocked"], ["concluidas", "Concluídas", "done"]].map(([key, label, tone]) => <div key={key}><span><i className={tone} />{label}</span><b>{summary[key]}</b></div>)}</div><div className="pv-time-total"><small>Tempo acumulado nas tarefas do período</small><b>{duration(summary.tempoRegistradoSegundos)}</b><p>Pode incluir execução fora do período. Não representa jornada de trabalho.</p></div></article></section>
      <section className="pv-panel"><header><div><h2>Ranking por responsável</h2><p>Tarefas atribuídas no período. Quantidades não medem dificuldade ou qualidade.</p></div><label className="pv-sort">Ordenar<select value={sort} onChange={e => setSort(e.target.value)}><option value="concluidas">Mais concluídas</option><option value="taxaNoPrazo">Maior % no prazo</option><option value="atrasadas">Mais atrasadas</option></select></label></header>
        <div className="pv-table-wrap"><table><thead><tr><th>#</th><th>Responsável</th><th>Planejadas</th><th>Concluídas</th><th>Conclusão</th><th>No prazo</th><th>Atrasadas</th><th>Não realizadas</th><th>Tempo acumulado</th></tr></thead><tbody>{ranked.map((row, index) => <tr key={`${row.usuarioId}-${row.nome}`}><td><span className={`pv-rank ${index === 0 ? "first" : ""}`}>{index + 1}</span></td><td><b>{row.nome}</b>{row.vinculo !== "unico" && <small className="pv-match-warning">{row.vinculo === "ambiguo" ? "Nome com mais de um usuário" : "Sem usuário correspondente"}</small>}</td><td>{row.planejadas}</td><td><b>{row.concluidas}</b></td><td>{percent(row.taxaConclusao)}</td><td>{percent(row.taxaNoPrazo)}<small>{row.noPrazo}/{row.concluidasComPrazoConhecido} conclusões</small></td><td className={row.atrasadas ? "pv-alert-text" : ""}>{row.atrasadas}</td><td>{row.naoRealizadas}</td><td className="pv-mono">{duration(row.tempoRegistradoSegundos)}</td></tr>)}</tbody></table>{!ranked.length && <p className="pv-empty">Nenhuma tarefa planejada neste período.</p>}</div>
      </section>
      <section className="pv-panel"><header><div><h2>Uso dos apontamentos</h2><p>Quem registrou mudanças de situação, independentemente do responsável pela tarefa.</p></div></header><div className="pv-table-wrap"><table><thead><tr><th>Usuário</th><th>Apontamentos</th><th>Tarefas movimentadas</th><th>Dias com registro</th><th>Tarefas próprias apontadas</th><th>Último registro no período</th></tr></thead><tbody>{data.adesao.map(row => <tr key={row.usuarioId}><td><b>{row.nome}</b><small>{row.perfil}{!row.ativo ? " · inativo" : ""}</small></td><td>{row.apontamentos}</td><td>{row.tarefasMovimentadas}</td><td>{row.diasAtivos}</td><td><b>{percent(row.taxaApontamentoProprio)}</b><small>{row.tarefasPropriasApontadas} de {row.tarefasAtribuidas} atribuídas</small></td><td>{row.ultimoApontamento ? `${dateLabel(row.ultimoApontamento)} às ${clockLabel(row.ultimoApontamento)}` : "Sem registro no período"}</td></tr>)}</tbody></table>{!data.adesao.length && <p className="pv-empty">Nenhum usuário para analisar.</p>}</div><p className="pv-note">Não mede presença nem logins. Para identificar cada colaborador, use acessos individuais. Percentuais sem tarefas atribuídas aparecem como “—”.</p></section>
      <section className="pv-middle-grid"><article className="pv-panel"><header><div><h2>Pendências vencidas</h2><p>Todo o histórico · ordenadas pelo prazo mais antigo</p></div><span className="pv-count">{data.atrasadas.length}</span></header><div className="pv-pending-list">{data.atrasadas.map(task => <div key={task.id}><span><b>{task.titulo}</b><small>{task.responsavel} · {task.projeto || "Sem projeto"}</small></span><span><b className="pv-alert-text">{dateLabel(task.prazo)} {clockLabel(task.prazo)}</b><small>{STATUS[task.status]}</small></span></div>)}{!data.atrasadas.length && <p className="pv-empty">Nenhuma tarefa em aberto fora do prazo.</p>}</div></article>
        <article className="pv-panel"><header><h2>Motivos das pausas atuais</h2></header><div className="pv-reasons">{data.motivosPausa.map(row => <div key={row.motivo}><span>{row.motivo}</span><b>{row.quantidade}</b></div>)}{!data.motivosPausa.length && <p className="pv-empty">Nenhuma tarefa pausada.</p>}</div></article></section>
      <details className="pv-definitions"><summary>Como os indicadores são calculados</summary>{Object.entries(data.criterios).map(([key, description]) => <p key={key}>{description}</p>)}</details>
    </>}
  </main>;
}

function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mql = window.matchMedia(query);
    const update = () => setMatches(mql.matches);
    update();
    mql.addEventListener("change", update);
    // Alguns navegadores de TV não disparam o evento da media query ao girar ou redimensionar.
    window.addEventListener("resize", update);
    return () => { mql.removeEventListener("change", update); window.removeEventListener("resize", update); };
  }, [query]);
  return matches;
}

function rotation(items, page, count) {
  const pages = Math.max(1, Math.ceil(items.length / count));
  const index = page % pages;
  // Com mais itens que espaços, a última página volta ao início em vez de deixar a TV vazia.
  const visible = items.length > count
    ? Array.from({ length: count }, (_, slot) => items[(index * count + slot) % items.length])
    : items.slice(0, count);
  return { items: visible, label: `${index + 1}/${pages}` };
}

export function FactoryTV({ user, onExit }) {
  const fetcher = useCallback(signal => api.getTVPanel({ signal }), []);
  const live = useLiveData(fetcher);
  const [now, setNow] = useState(Date.now());
  const [page, setPage] = useState(0);
  const [screenMessage, setScreenMessage] = useState("");
  // Em telas baixas cabem dois cards legíveis; quatro sairiam cortados.
  const tallScreen = useMediaQuery("(min-height: 900px)");
  // Sem o gráfico de 7 dias (escondido por CSS na mesma faixa) sobra espaço para mais projetos.
  const chartHidden = useMediaQuery("(min-width: 1101px) and (max-height: 767px)");
  const wakeLock = useRef(null);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    const pages = setInterval(() => setPage(n => n + 1), 15000);
    return () => { clearInterval(timer); clearInterval(pages); };
  }, []);
  useEffect(() => {
    let active = true;
    async function keepAwake() {
      if (!navigator.wakeLock || document.visibilityState !== "visible" || wakeLock.current) return;
      try { const lock = await navigator.wakeLock.request("screen"); if (!active) { await lock.release(); return; } wakeLock.current = lock; lock.addEventListener("release", () => { wakeLock.current = null; }); } catch { /* TVs may manage standby in their own settings. */ }
    }
    keepAwake(); document.addEventListener("visibilitychange", keepAwake);
    return () => { active = false; document.removeEventListener("visibilitychange", keepAwake); wakeLock.current?.release(); wakeLock.current = null; };
  }, []);
  async function fullscreen() {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen(); else setScreenMessage("Use o modo de tela cheia do navegador da TV."); }
    catch { setScreenMessage("Use o modo de tela cheia do navegador da TV."); }
  }
  function exit() { if (document.fullscreenElement) document.exitFullscreen().catch(() => {}); onExit(); }
  const data = live.data;
  const serverNow = data ? new Date(data.geradoEm).getTime() + Math.max(0, now - live.receivedAt) : now;
  const current = rotation(data?.emExecucao || [], page, tallScreen ? 4 : 2);
  const paused = rotation(data?.pausadas || [], page, 2);
  const projects = rotation((data?.projetos || []).filter(p => p.total > 0), page, tallScreen || chartHidden ? 3 : 2);
  const recent = rotation(data?.ultimosEventos || [], page, 3);
  return <main className="pv-tv">
    <header className="pv-tv-header"><div className="pv-tv-brand"><span><Factory size={32} /></span><div><strong>GIMAK</strong><small>PRODUÇÃO EM TEMPO REAL</small></div></div><div className="pv-tv-clock"><strong>{clockLabel(serverNow)}</strong><span>{new Date(serverNow).toLocaleDateString("pt-BR", { timeZone: ZONE, weekday: "long", day: "2-digit", month: "long" })}</span></div><div className="pv-tv-tools"><button onClick={fullscreen}><Expand size={18} /> Tela cheia</button><button onClick={exit}><ArrowLeft size={18} /> {user.perfil === "TV" ? "Sair" : "Voltar"}</button></div></header>
    <div className="pv-tv-status"><Connection live={live} /><span>Somente leitura · cards alternam a cada 15 s</span>{screenMessage && <span role="status">{screenMessage}</span>}</div>
    {!data && <div className="pv-tv-empty">{live.error ? "Aguardando conexão com a fábrica…" : "Carregando painel da fábrica…"}</div>}
    {data && <>
      <section className="pv-metrics">
        <Metric label="Em execução agora" value={data.resumo.emExecucao} detail="Todas as atividades iniciadas" tone="green" icon={Activity} />
        <Metric label="Concluídas hoje" value={data.resumo.concluidasHoje} detail="Entregas registradas hoje" tone="blue" icon={CheckCircle2} />
        <Metric label="Pausadas agora" value={data.resumo.pausadas} detail="Aguardando retomada" tone="amber" icon={PauseCircle} />
        <Metric label="Pendências vencidas" value={data.resumo.atrasadasEmAberto} detail="Inclui prazos de dias anteriores" tone="red" icon={TriangleAlert} />
      </section>
      <div className="pv-tv-grid"><section className="pv-tv-production"><header><h1><span className="pv-live-dot" /> No chão de fábrica</h1><span>{current.label}</span></header><div className="pv-tv-task-grid">{current.items.map(task => <article className="pv-tv-task" key={task.id}><div><span className="pv-tv-op">{task.ordem}</span>{task.prioridade === "Urgente" && <b className="pv-tv-urgent">URGENTE</b>}</div><h2>{task.titulo}</h2><p>{task.projeto || "Sem projeto vinculado"}</p><footer><span>{task.responsavel}</span><strong>{duration(task.tempoRegistradoSegundos + Math.max(0, (serverNow - new Date(data.geradoEm)) / 1000))}</strong></footer><small className={task.atrasada ? "pv-tv-late" : ""}>Prazo: {dateLabel(task.prazo)} às {clockLabel(task.prazo)}{task.atrasada ? " · vencido" : ""}</small></article>)}{!current.items.length && <div className="pv-tv-empty"><Activity size={30} /><h2>Aguardando o próximo início</h2><p>As tarefas aparecem aqui quando a equipe inicia a execução.</p></div>}</div>
        <div className="pv-tv-paused"><h2><PauseCircle size={18} /> Pausadas <span>{paused.label}</span></h2>{paused.items.map(task => <div key={task.id}><b>{task.titulo}</b><span>{task.responsavel}</span></div>)}{!paused.items.length && <p>Nenhuma pausa em aberto.</p>}</div>
      </section>
      <aside className="pv-tv-aside"><section className="pv-tv-section"><header><h2>Plano de hoje</h2><strong>{percent(data.resumo.taxaConclusaoHoje)}</strong></header><Progress value={data.resumo.taxaConclusaoHoje} /><p>{data.resumo.concluidasHojePlanejadas} de {data.resumo.planejadasHoje} tarefas planejadas concluídas</p></section><section className="pv-tv-section pv-tv-flexible"><header><h2>Últimos 7 dias</h2></header><DailyChart compact series={data.serieDiaria} /></section><section className="pv-tv-section"><header><h2>Projetos em produção</h2><span>{projects.label}</span></header>{projects.items.map(project => <article className="pv-tv-project" key={project.id}><div><b>{project.equipamento}</b><strong>{percent(project.percentualConclusao)}</strong></div><small>{project.cliente} · {project.concluidas}/{project.total} tarefas</small><Progress value={project.percentualConclusao} /></article>)}{!projects.items.length && <p>Nenhum projeto com atividades.</p>}</section></aside></div>
      <section className="pv-tv-events"><span>ÚLTIMOS APONTAMENTOS</span>{recent.items.map(event => <div key={event.id}><i className={event.status} /><span><b>{event.status === "done" ? "Concluída" : "Iniciada / retomada"} · {event.titulo}</b><small>{event.responsavel} · {dateLabel(event.ocorridoEm)} {clockLabel(event.ocorridoEm)}</small></span></div>)}{!recent.items.length && <p>Aguardando os primeiros apontamentos.</p>}</section>
    </>}
  </main>;
}

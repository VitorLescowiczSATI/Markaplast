import { useCallback, useEffect, useMemo, useState } from "react";
import {
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  Expand,
  Factory,
  LogOut,
  PauseCircle,
  PlayCircle,
  Plus,
  RefreshCw,
  ShieldCheck,
  UserRoundCog,
  Users,
  X,
  XCircle,
} from "lucide-react";

import { api } from "./api";

const STATUS_LABELS = {
  todo: "Aguardando início",
  doing: "Em execução",
  paused: "Atividade pausada",
  blocked: "Não realizado",
  done: "Concluído",
};

const COLUMNS = [
  { id: "todo", title: "A fazer", statuses: ["todo"], icon: Clock3 },
  { id: "doing", title: "Em execução", statuses: ["doing", "paused"], icon: PlayCircle },
  { id: "blocked", title: "Não realizado", statuses: ["blocked"], icon: XCircle },
  { id: "done", title: "Concluído", statuses: ["done"], icon: CheckCircle2 },
];

function localIsoDate(value = new Date()) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function weekStart() {
  const now = new Date();
  const weekday = now.getDay() || 7;
  now.setDate(now.getDate() - weekday + 1);
  return localIsoDate(now);
}

function elapsedSeconds(task, now = Date.now()) {
  const saved = Number(task.elapsedSeconds || 0);
  if (task.status !== "doing" || !task.startedAt) return saved;
  return saved + Math.max(0, Math.floor((now - new Date(task.startedAt).getTime()) / 1000));
}

function formatDuration(seconds) {
  const value = Math.max(0, Math.floor(seconds || 0));
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const rest = value % 60;
  return [hours, minutes, rest].map((item) => String(item).padStart(2, "0")).join(":");
}

function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function Modal({ children, className = "", onClose }) {
  useEffect(() => {
    const close = (event) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [onClose]);
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className={`modal ${className}`} role="dialog" aria-modal="true">
        {children}
      </section>
    </div>
  );
}

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [senha, setSenha] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const session = await api.login(username, senha);
      api.setAccessToken(session.accessToken);
      onLogin(session.usuario);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <div className="login-brand">
        <span className="brand-mark"><Factory size={28} /></span>
        <div><strong>Gimak PCP</strong><small>Gestão da produção</small></div>
      </div>
      <form className="login-card" onSubmit={submit}>
        <div className="login-icon"><ShieldCheck size={28} /></div>
        <p className="eyebrow">ACESSO RESTRITO</p>
        <h1>Entre no painel</h1>
        <p className="muted">Use seu usuário para acompanhar e apontar as atividades da fábrica.</p>
        <label>Usuário<input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required /></label>
        <label>Senha<input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required /></label>
        {error && <p className="form-error">{error}</p>}
        <button className="primary wide" disabled={loading}>{loading ? "Entrando…" : "Entrar"}</button>
      </form>
    </main>
  );
}

function Header({ page, setPage, user, onLogout, onNewProject, onNewTask, canManage }) {
  const [clock, setClock] = useState(new Date());
  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 30000);
    return () => window.clearInterval(timer);
  }, []);
  const tabs = [
    ["board", "Painel da fábrica", Factory],
    ["projects", "Projetos", BriefcaseBusiness],
    ...(user.perfil === "Administrador" ? [["users", "Usuários", Users]] : []),
  ];
  return (
    <>
      <header className="topbar">
        <div className="brand"><span className="brand-mark"><Factory size={23} /></span><div><strong>Gimak PCP</strong><small>Painel de execução</small></div></div>
        <div className="top-actions">
          <div className="clock"><small>{clock.toLocaleDateString("pt-BR", { weekday: "long" })}</small><strong>{clock.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</strong></div>
          <button className="outline desktop-only" onClick={() => document.documentElement.requestFullscreen?.()}><Expand size={17} /> Tela cheia</button>
          {canManage && <button className="outline desktop-only" onClick={onNewProject}><Plus size={17} /> Projeto</button>}
          {canManage && <button className="primary" onClick={onNewTask}><Plus size={17} /> Nova tarefa</button>}
          <button className="icon-button" onClick={onLogout} title={`Sair — ${user.nome}`}><LogOut size={19} /></button>
        </div>
      </header>
      <nav className="page-tabs">
        {tabs.map(([id, label, Icon]) => <button key={id} className={page === id ? "active" : ""} onClick={() => setPage(id)}><Icon size={17} /> {label}</button>)}
        <span className="signed-user"><b>{user.nome}</b><small>{user.perfil}</small></span>
      </nav>
    </>
  );
}

function TaskCard({ task, project, now, onOpen }) {
  return (
    <button className={`task-card ${task.status}`} onClick={() => onOpen(task)}>
      <span className="task-top"><span className="op">{task.ordem || "TAREFA"}</span>{task.prioridade === "Urgente" && <span className="priority">URGENTE</span>}</span>
      <strong className="task-title">{task.titulo}</strong>
      <span className={`project-tag ${project ? "" : "unassigned"}`}>{project ? `${project.equipamento} · ${project.cliente}` : "Sem projeto"}</span>
      <span className="task-meta"><span><i className="avatar">{initials(task.responsavel)}</i>{task.responsavel}</span><b>{task.horario}</b></span>
      <span className={`card-timer ${task.status === "doing" ? "running" : ""}`}><span>{task.status === "doing" ? "● Contando" : "Tempo registrado"}</span><strong>{formatDuration(elapsedSeconds(task, now))}</strong></span>
      {task.motivo && <span className="reason"><b>Motivo:</b> {task.motivo}</span>}
      <span className="task-footer"><span>{STATUS_LABELS[task.status]}</span><b>Ver detalhes ›</b></span>
    </button>
  );
}

function Board({ tasks, projects, users, now, onOpen, onRefresh, refreshing }) {
  const [person, setPerson] = useState("all");
  const [period, setPeriod] = useState("today");
  const filtered = useMemo(() => tasks.filter((task) => {
    const personMatches = person === "all" || task.responsavel === person;
    const dateMatches = period === "today" ? task.dataPlanejada === localIsoDate() : task.dataPlanejada >= weekStart() && task.dataPlanejada <= localIsoDate();
    return personMatches && dateMatches;
  }), [tasks, person, period]);
  const stats = {
    todo: filtered.filter((task) => task.status === "todo").length,
    doing: filtered.filter((task) => task.status === "doing").length,
    paused: filtered.filter((task) => task.status === "paused").length,
    blocked: filtered.filter((task) => task.status === "blocked").length,
    done: filtered.filter((task) => task.status === "done").length,
  };
  return (
    <main className="page">
      <section className="intro">
        <div><p className="eyebrow">PRODUÇÃO</p><h1>O que precisa ser feito</h1><p>Selecione uma atividade para iniciar, pausar ou concluir o apontamento.</p></div>
        <div className="stats">
          {[['todo', 'A fazer'], ['doing', 'Em execução'], ['paused', 'Pausadas'], ['blocked', 'Não realizadas'], ['done', 'Concluídas']].map(([key, label]) => <div key={key}><b>{stats[key]}</b><span>{label}</span></div>)}
        </div>
      </section>
      <section className="filters">
        <label>Colaborador<select value={person} onChange={(e) => setPerson(e.target.value)}><option value="all">Todos</option>{users.filter((item) => item.ativo).map((item) => <option key={item.id} value={item.nome}>{item.nome}</option>)}</select></label>
        <div className="segmented"><button className={period === "today" ? "active" : ""} onClick={() => setPeriod("today")}>Hoje</button><button className={period === "week" ? "active" : ""} onClick={() => setPeriod("week")}>Esta semana</button></div>
        <button className="refresh" onClick={onRefresh} disabled={refreshing}><RefreshCw size={17} className={refreshing ? "spin" : ""} /> Atualizar painel</button>
      </section>
      <section className="board">
        {COLUMNS.map((column) => {
          const items = filtered.filter((task) => column.statuses.includes(task.status));
          const Icon = column.icon;
          return <section className={`column ${column.id}`} key={column.id}><header><span><Icon size={17} /><b>{column.title}</b></span><i>{items.length}</i></header><div className="cards">{items.map((task) => <TaskCard key={task.id} task={task} project={projects.find((item) => item.id === task.projetoId)} now={now} onOpen={onOpen} />)}{!items.length && <p className="empty">Nenhuma tarefa aqui</p>}</div></section>;
        })}
      </section>
    </main>
  );
}

function Projects({ projects, tasks, now, onOpen, onNew, canManage }) {
  return (
    <main className="page">
      <section className="intro"><div><p className="eyebrow">HISTÓRICO DE PRODUÇÃO</p><h1>Projetos</h1><p>Consulte o andamento e as atividades realizadas em cada equipamento.</p></div>{canManage && <button className="primary" onClick={onNew}><Plus size={17} /> Novo projeto</button>}</section>
      <section className="project-grid">
        {projects.map((project) => {
          const projectTasks = tasks.filter((task) => task.projetoId === project.id);
          const done = projectTasks.filter((task) => task.status === "done");
          const percent = projectTasks.length ? Math.round(done.length / projectTasks.length * 100) : 0;
          const total = done.reduce((sum, task) => sum + elapsedSeconds(task, now), 0);
          return <button className="project-card" key={project.id} onClick={() => onOpen(project)}><span className="project-card-top"><span className="op">PROJETO {String(project.id).padStart(4, "0")}</span><span className="project-percent">{percent}%</span></span><h2>{project.equipamento}</h2><p>{project.cliente}</p><span className="progress"><i style={{ width: `${percent}%` }} /></span><span className="project-stats"><span><b>{done.length}</b> concluídas</span><span><b>{projectTasks.length - done.length}</b> pendentes</span><span><b>{formatDuration(total)}</b> trabalhadas</span></span><strong className="open-project">Abrir histórico ›</strong></button>;
        })}
        {!projects.length && <div className="blank-state"><BriefcaseBusiness size={30} /><h2>Nenhum projeto criado</h2><p>Cadastre o primeiro projeto para organizar as atividades.</p></div>}
      </section>
    </main>
  );
}

function UsersPage({ users, onCreate, onToggle, onReset }) {
  const [form, setForm] = useState({ nome: "", username: "", senha: "", perfil: "Fábrica" });
  async function submit(event) {
    event.preventDefault();
    if (await onCreate(form)) setForm({ nome: "", username: "", senha: "", perfil: "Fábrica" });
  }
  return (
    <main className="page users-page">
      <section className="intro"><div><p className="eyebrow">ADMINISTRAÇÃO</p><h1>Usuários da Gimak</h1><p>Crie acessos próprios para o PCP e para os colaboradores da fábrica.</p></div></section>
      <div className="users-layout">
        <form className="panel user-form" onSubmit={submit}><div className="panel-title"><UserRoundCog size={20} /><div><h2>Novo acesso</h2><p>O usuário receberá apenas permissões da Gimak.</p></div></div><label>Nome completo<input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required /></label><label>Usuário<input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required /></label><label>Senha inicial<input type="password" minLength="8" value={form.senha} onChange={(e) => setForm({ ...form, senha: e.target.value })} required /></label><label>Perfil<select value={form.perfil} onChange={(e) => setForm({ ...form, perfil: e.target.value })}><option>Fábrica</option><option>PCP</option><option>Administrador</option></select></label><button className="primary wide"><Plus size={17} /> Criar usuário</button></form>
        <section className="panel user-list"><div className="panel-title"><Users size={20} /><div><h2>Acessos cadastrados</h2><p>{users.filter((item) => item.ativo).length} usuários ativos</p></div></div>{users.map((item) => <article className="user-row" key={item.id}><span className="avatar large">{initials(item.nome)}</span><span className="user-info"><b>{item.nome}</b><small>@{item.username} · {item.perfil}</small></span><span className={`status-pill ${item.ativo ? "active" : ""}`}>{item.ativo ? "Ativo" : "Inativo"}</span><button className="link-button" onClick={() => onReset(item)}>Redefinir senha</button><button className="link-button" onClick={() => onToggle(item)}>{item.ativo ? "Desativar" : "Ativar"}</button></article>)}</section>
      </div>
    </main>
  );
}

function TaskModal({ task, projects, now, canManage, onClose, onStatus, onAssign }) {
  const [pending, setPending] = useState("");
  const [reason, setReason] = useState("");
  const [projectId, setProjectId] = useState(task.projetoId || "");
  function choose(status) {
    if (["paused", "blocked"].includes(status)) setPending(status);
    else onStatus(task.id, status, "");
  }
  return <Modal onClose={onClose}><div className="modal-head"><div><span className="op">{task.ordem}</span><h2>{task.titulo}</h2></div><button className="close" onClick={onClose}><X /></button></div><div className="task-summary"><span><small>Responsável</small><b>{task.responsavel}</b></span><span><small>Prazo</small><b>{new Date(`${task.dataPlanejada}T12:00:00`).toLocaleDateString("pt-BR")} às {task.horario}</b></span><span><small>Situação</small><b>{STATUS_LABELS[task.status]}</b></span></div><div className="dialog-timer"><span>Tempo da atividade</span><strong>{formatDuration(elapsedSeconds(task, now))}</strong></div><section className="observation"><small>OBSERVAÇÕES DA TAREFA</small><p>{task.observacao || "Nenhuma observação cadastrada."}</p></section>{canManage && <div className="project-shortcut"><label>Projeto vinculado<select value={projectId} onChange={(e) => setProjectId(e.target.value)}><option value="">Sem projeto</option>{projects.map((item) => <option key={item.id} value={item.id}>{item.equipamento} — {item.cliente}</option>)}</select></label><button onClick={() => onAssign(task.id, projectId)}>Vincular</button></div>}<p className="action-title">Atualizar situação</p><div className="status-actions"><button className="start" onClick={() => choose("doing")}><PlayCircle /> {task.status === "paused" ? "Retomar" : "Iniciar"}</button><button className="pause" onClick={() => choose("paused")}><PauseCircle /> Pausar</button><button className="not-done" onClick={() => choose("blocked")}><XCircle /> Não realizado</button><button className="complete" onClick={() => choose("done")}><CheckCircle2 /> Concluir</button></div>{pending && <div className="reason-panel"><label>{pending === "paused" ? "Por que a atividade foi pausada?" : "Por que não foi realizada?"}<textarea value={reason} onChange={(e) => setReason(e.target.value)} autoFocus /></label><button className="primary wide" disabled={!reason.trim()} onClick={() => onStatus(task.id, pending, reason)}>Confirmar situação</button></div>}<div className="modal-actions"><button className="secondary" onClick={onClose}>Fechar</button></div></Modal>;
}

function TaskForm({ projects, users, onClose, onSave }) {
  const [form, setForm] = useState({ titulo: "", ordem: "", responsavel: "", dataPlanejada: localIsoDate(), horario: "08:00", prioridade: "Normal", observacao: "", projetoId: "" });
  function field(key, value) { setForm((current) => ({ ...current, [key]: value })); }
  function submit(event) { event.preventDefault(); onSave({ ...form, ordem: form.ordem || "TAREFA", projetoId: form.projetoId ? Number(form.projetoId) : null }); }
  return <Modal onClose={onClose}><form onSubmit={submit}><div className="modal-head"><div><span className="op">NOVA</span><h2>Criar tarefa da fábrica</h2></div><button type="button" className="close" onClick={onClose}><X /></button></div><label>O que deve ser feito?<input value={form.titulo} onChange={(e) => field("titulo", e.target.value)} required autoFocus /></label><div className="form-grid"><label>Ordem / projeto<input value={form.ordem} onChange={(e) => field("ordem", e.target.value)} placeholder="Ex.: OP-1052" /></label><label>Responsável<select value={form.responsavel} onChange={(e) => field("responsavel", e.target.value)} required><option value="">Selecione</option>{users.filter((item) => item.ativo).map((item) => <option key={item.id} value={item.nome}>{item.nome}</option>)}</select></label></div><div className="form-grid"><label>Data<input type="date" value={form.dataPlanejada} onChange={(e) => field("dataPlanejada", e.target.value)} required /></label><label>Horário<input type="time" value={form.horario} onChange={(e) => field("horario", e.target.value)} required /></label></div><div className="form-grid"><label>Prioridade<select value={form.prioridade} onChange={(e) => field("prioridade", e.target.value)}><option>Normal</option><option>Urgente</option></select></label><label>Projeto<select value={form.projetoId} onChange={(e) => field("projetoId", e.target.value)}><option value="">Sem projeto</option>{projects.map((item) => <option key={item.id} value={item.id}>{item.equipamento} — {item.cliente}</option>)}</select></label></div><label>Instrução ou observação<textarea value={form.observacao} onChange={(e) => field("observacao", e.target.value)} /></label><div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancelar</button><button className="primary">Criar tarefa</button></div></form></Modal>;
}

function ProjectForm({ onClose, onSave }) {
  const [cliente, setCliente] = useState("");
  const [equipamento, setEquipamento] = useState("");
  return <Modal onClose={onClose}><form onSubmit={(event) => { event.preventDefault(); onSave({ cliente, equipamento }); }}><div className="modal-head"><div><span className="op">NOVO PROJETO</span><h2>Cadastrar projeto</h2></div><button type="button" className="close" onClick={onClose}><X /></button></div><label>Cliente<input value={cliente} onChange={(e) => setCliente(e.target.value)} required autoFocus /></label><label>Equipamento<input value={equipamento} onChange={(e) => setEquipamento(e.target.value)} required placeholder="Ex.: Envolvedora GK2100" /></label><div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancelar</button><button className="primary">Criar projeto</button></div></form></Modal>;
}

function ProjectModal({ project, tasks, now, onClose }) {
  const projectTasks = tasks.filter((task) => task.projetoId === project.id);
  const done = projectTasks.filter((task) => task.status === "done").sort((a, b) => new Date(b.finishedAt) - new Date(a.finishedAt));
  const percent = projectTasks.length ? Math.round(done.length / projectTasks.length * 100) : 0;
  return <Modal onClose={onClose} className="project-modal"><div className="modal-head"><div><span className="op">PROJETO {String(project.id).padStart(4, "0")}</span><h2>{project.equipamento}</h2><p>{project.cliente}</p></div><button className="close" onClick={onClose}><X /></button></div><div className="project-progress"><span><b>{done.length} concluídas</b><b>{formatDuration(done.reduce((sum, task) => sum + elapsedSeconds(task, now), 0))} trabalhadas</b></span><span className="progress"><i style={{ width: `${percent}%` }} /></span></div><h3>Atividades realizadas</h3><div className="timeline">{done.map((task, index) => <article key={task.id}><i>{index + 1}</i><span><b>{task.titulo}</b><small>{task.responsavel} · {new Date(task.finishedAt).toLocaleString("pt-BR")}</small>{task.observacao && <p>{task.observacao}</p>}</span><strong>{formatDuration(elapsedSeconds(task, now))}</strong></article>)}{!done.length && <p className="empty">Ainda não há atividades concluídas.</p>}</div><div className="modal-actions"><button className="secondary" onClick={onClose}>Fechar</button></div></Modal>;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(api.hasToken());
  const [page, setPage] = useState("board");
  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [modal, setModal] = useState(null);
  const [now, setNow] = useState(Date.now());
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState("");

  const notify = useCallback((message) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2800);
  }, []);

  const load = useCallback(async (silent = false) => {
    if (!silent) setRefreshing(true);
    try {
      const [taskData, projectData, userData] = await Promise.all([api.listTasks(), api.listProjects(), api.listUsers()]);
      setTasks(taskData); setProjects(projectData); setUsers(userData);
    } catch (err) {
      notify(err.message);
    } finally {
      setRefreshing(false);
    }
  }, [notify]);

  useEffect(() => {
    if (!api.hasToken()) { setBooting(false); return; }
    api.me().then((current) => { setUser(current); return load(); }).catch(() => api.setAccessToken("")).finally(() => setBooting(false));
  }, [load]);

  useEffect(() => {
    const expired = () => { setUser(null); setModal(null); };
    window.addEventListener("gimak:auth-expired", expired);
    return () => window.removeEventListener("gimak:auth-expired", expired);
  }, []);

  useEffect(() => {
    const tick = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(tick);
  }, []);

  useEffect(() => {
    if (!user) return undefined;
    const polling = window.setInterval(() => load(true), 30000);
    return () => window.clearInterval(polling);
  }, [user, load]);

  const action = useCallback(async (work, success) => {
    try { await work(); await load(true); setModal(null); notify(success); return true; }
    catch (err) { notify(err.message); return false; }
  }, [load, notify]);

  if (booting) return <div className="boot"><Factory size={32} /><span>Carregando Gimak PCP…</span></div>;
  if (!user) return <Login onLogin={(logged) => { setUser(logged); load(); }} />;
  const canManage = user.perfil === "Administrador" || user.perfil === "PCP";

  return <div className="app-shell">
    <Header page={page} setPage={setPage} user={user} canManage={canManage} onLogout={() => { api.setAccessToken(""); setUser(null); }} onNewProject={() => setModal({ type: "new-project" })} onNewTask={() => setModal({ type: "new-task" })} />
    {page === "board" && <Board tasks={tasks} projects={projects} users={users} now={now} onOpen={(task) => setModal({ type: "task", data: task })} onRefresh={() => load()} refreshing={refreshing} />}
    {page === "projects" && <Projects projects={projects} tasks={tasks} now={now} canManage={canManage} onOpen={(project) => setModal({ type: "project", data: project })} onNew={() => setModal({ type: "new-project" })} />}
    {page === "users" && user.perfil === "Administrador" && <UsersPage users={users} onCreate={(payload) => action(() => api.createUser(payload), "Usuário criado") } onToggle={(item) => action(() => api.updateUser(item.id, { ativo: !item.ativo }), item.ativo ? "Usuário desativado" : "Usuário ativado")} onReset={(item) => { const password = window.prompt(`Nova senha para ${item.nome} (mínimo 8 caracteres):`); if (password) action(() => api.resetPassword(item.id, password), "Senha atualizada"); }} />}
    {modal?.type === "task" && <TaskModal task={tasks.find((item) => item.id === modal.data.id) || modal.data} projects={projects} now={now} canManage={canManage} onClose={() => setModal(null)} onStatus={(id, status, reason) => action(() => api.updateTaskStatus(id, status, reason), `Situação atualizada: ${STATUS_LABELS[status]}`)} onAssign={(id, projectId) => action(() => api.updateTask(id, { projetoId: projectId ? Number(projectId) : null }), "Projeto vinculado")} />}
    {modal?.type === "new-task" && <TaskForm projects={projects} users={users} onClose={() => setModal(null)} onSave={(payload) => action(() => api.createTask(payload), "Nova tarefa criada")} />}
    {modal?.type === "new-project" && <ProjectForm onClose={() => setModal(null)} onSave={(payload) => action(() => api.createProject(payload), "Projeto criado")} />}
    {modal?.type === "project" && <ProjectModal project={modal.data} tasks={tasks} now={now} onClose={() => setModal(null)} />}
    {toast && <div className="toast">{toast}</div>}
  </div>;
}

import { useState } from "react";
import {
  CheckCircle2,
  Clock3,
  ClipboardList,
  LogOut,
  MapPin,
  Plus,
  Trash2,
  Truck,
  Wrench,
  X,
} from "lucide-react";

import { Modal } from "./Modal";
import "./services.css";

export const SERVICE_TYPES = ["Assistência técnica", "Instalação"];

const SERVICE_STATES = {
  agendado: "Agendado",
  em_rota: "A caminho do cliente",
  concluido: "Concluído",
};

export function serviceDeadline(service) {
  return new Date(`${service.data}T${service.horario}:00`);
}

function initials(name = "") {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0] || "").join("").toUpperCase();
}

function dateLabel(value) {
  return new Date(`${value}T12:00:00`).toLocaleDateString("pt-BR");
}

function momentLabel(value) {
  return new Date(value).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

/** Horário planejado de saída e de volta, quando o administrador preencheu. */
function PlannedTrip({ service, compact = false }) {
  if (!service.horarioSaida && !service.horarioRetorno) return null;
  return (
    <span className={`trip${compact ? " compact" : ""}`}>
      {service.horarioSaida && <span><LogOut size={12} /> Sai {service.horarioSaida}</span>}
      {service.horarioRetorno && <span><Truck size={12} /> Volta {service.horarioRetorno}</span>}
    </span>
  );
}

/** Uma pendência, com o formulário de resolução aberto ali mesmo. */
function IssueCard({ issue, contexto = true, canManage, canDelete, onResolve, onReopen, onDelete }) {
  const [resolvendo, setResolvendo] = useState(false);
  const [texto, setTexto] = useState(issue.resolucao || "");
  return (
    <article className={`issue ${issue.status}`}>
      {contexto && (
        <div className="issue-head">
          <span>
            <b>{issue.cliente}</b>
            <small>{issue.tipo} · {issue.tecnico} · visita de {dateLabel(issue.dataAtendimento)}</small>
          </span>
          <span className={`status-pill ${issue.status === "aberta" ? "" : "active"}`}>
            {issue.status === "aberta" ? "Aberta" : "Resolvida"}
          </span>
        </div>
      )}
      <p className="issue-text">{issue.descricao}</p>
      {issue.resolucao && !resolvendo && <p className="issue-solution"><b>Resolução:</b> {issue.resolucao}</p>}
      {resolvendo ? (
        <div className="issue-resolve">
          <label>Como foi resolvido?<textarea value={texto} onChange={(e) => setTexto(e.target.value)} autoFocus placeholder="Opcional. Ex.: sensor comprado e instalado na visita seguinte." /></label>
          <div>
            <button className="secondary" onClick={() => setResolvendo(false)}>Cancelar</button>
            <button className="primary" onClick={() => { onResolve(issue, texto); setResolvendo(false); }}>Marcar resolvida</button>
          </div>
        </div>
      ) : (
        <div className="issue-foot">
          <small>Registrada em {momentLabel(issue.createdAt)}{issue.resolvidoEm ? ` · resolvida em ${momentLabel(issue.resolvidoEm)}` : ""}</small>
          <span>
            {issue.status === "aberta"
              ? <button className="link-button" onClick={() => setResolvendo(true)}>Marcar resolvida</button>
              : canManage && <button className="link-button" onClick={() => onReopen(issue)}>Reabrir</button>}
            {canDelete && <button className="link-button danger-link" onClick={() => onDelete(issue)} aria-label="Excluir pendência"><Trash2 size={13} /></button>}
          </span>
        </div>
      )}
    </article>
  );
}

export function ServicesPage({ services, issues, now, canManage, canDelete, onOpen, onNew, onResolveIssue, onReopenIssue, onDeleteIssue }) {
  const [tab, setTab] = useState("atendimentos");
  const [filter, setFilter] = useState("abertos");
  const [issueFilter, setIssueFilter] = useState("abertas");

  const open = services.filter((item) => item.status !== "concluido");
  const finished = services.filter((item) => item.status === "concluido");
  const late = open.filter((item) => serviceDeadline(item).getTime() < now);
  const visible = filter === "abertos" ? open : filter === "concluidos" ? finished : services;

  const openIssues = issues.filter((item) => item.status === "aberta");
  const solvedIssues = issues.filter((item) => item.status === "resolvida");
  const visibleIssues = issueFilter === "abertas" ? openIssues : issueFilter === "resolvidas" ? solvedIssues : issues;

  return (
    <main className="page">
      <section className="intro">
        <div>
          <p className="eyebrow">ATENDIMENTO EXTERNO</p>
          <h1>Assistências e instalações</h1>
          <p>Visitas a cliente: quem vai, quando sai, o relatório da volta e o que ficou pendente.</p>
        </div>
        <div className="stats">
          <div><b>{open.length}</b><span>Em aberto</span></div>
          <div><b>{late.length}</b><span>Data vencida</span></div>
          <div><b>{openIssues.length}</b><span>Pendências</span></div>
        </div>
      </section>

      <nav className="subtabs">
        <button className={tab === "atendimentos" ? "active" : ""} onClick={() => setTab("atendimentos")}>
          <Wrench size={16} /> Atendimentos
        </button>
        <button className={tab === "pendencias" ? "active" : ""} onClick={() => setTab("pendencias")}>
          <ClipboardList size={16} /> Pendências {openIssues.length > 0 && <i className="badge">{openIssues.length}</i>}
        </button>
      </nav>

      {tab === "atendimentos" ? (
        <>
          <div className="filters">
            <div className="segmented">
              {[["abertos", "Em aberto"], ["concluidos", "Concluídos"], ["todos", "Todos"]].map(([key, label]) => (
                <button key={key} className={filter === key ? "active" : ""} onClick={() => setFilter(key)}>{label}</button>
              ))}
            </div>
            {canManage && <button className="primary" onClick={onNew}><Plus size={17} /> Novo atendimento</button>}
          </div>
          <section className="service-grid">
            {visible.map((service) => {
              const overdue = service.status !== "concluido" && serviceDeadline(service).getTime() < now;
              const pendentes = (service.pendencias || []).filter((item) => item.status === "aberta").length;
              return (
                <button className={`service-card ${service.status}${overdue ? " overdue" : ""}`} key={service.id} onClick={() => onOpen(service)}>
                  <span className="service-top">
                    <span className={`service-type ${service.tipo === "Instalação" ? "install" : ""}`}>{service.tipo}</span>
                    <span className="service-state">
                      {service.status === "concluido" ? <><CheckCircle2 size={13} /> Concluído</>
                        : service.status === "em_rota" ? <><Truck size={13} /> A caminho</>
                        : overdue ? <><Clock3 size={13} /> Vencido</>
                        : <><Clock3 size={13} /> Agendado</>}
                    </span>
                  </span>
                  <h2>{service.cliente}</h2>
                  {service.local && <p className="service-place"><MapPin size={13} /> {service.local}</p>}
                  <PlannedTrip service={service} compact />
                  <span className="service-meta">
                    <span><i className="avatar">{initials(service.tecnico)}</i>{service.tecnico}</span>
                    <span className="service-when">{dateLabel(service.data)} às {service.horario}</span>
                  </span>
                  {pendentes > 0 && <span className="service-pending"><ClipboardList size={13} /> {pendentes} {pendentes === 1 ? "pendência aberta" : "pendências abertas"}</span>}
                  {service.status === "concluido"
                    ? <span className="service-report"><small>RELATÓRIO</small>{service.relatorio}</span>
                    : <strong className="open-project">Abrir atendimento ›</strong>}
                </button>
              );
            })}
            {!visible.length && (
              <div className="blank-state">
                <Wrench size={30} />
                <h2>Nenhum atendimento {filter === "concluidos" ? "concluído" : filter === "abertos" ? "em aberto" : "cadastrado"}</h2>
                <p>{canManage ? "Cadastre uma assistência técnica ou instalação para o técnico acompanhar." : "Os atendimentos agendados pelo PCP aparecem aqui."}</p>
              </div>
            )}
          </section>
        </>
      ) : (
        <>
          <div className="filters">
            <div className="segmented">
              {[["abertas", "Abertas"], ["resolvidas", "Resolvidas"], ["todas", "Todas"]].map(([key, label]) => (
                <button key={key} className={issueFilter === key ? "active" : ""} onClick={() => setIssueFilter(key)}>{label}</button>
              ))}
            </div>
          </div>
          <section className="panel issue-list">
            <div className="panel-title">
              <ClipboardList size={20} />
              <div>
                <h2>O que ficou faltando</h2>
                <p>Registrado por quem voltou do cliente. Some da lista quando você marca como resolvida.</p>
              </div>
            </div>
            {visibleIssues.map((issue) => (
              <IssueCard key={issue.id} issue={issue} canManage={canManage} canDelete={canDelete}
                onResolve={onResolveIssue} onReopen={onReopenIssue} onDelete={onDeleteIssue} />
            ))}
            {!visibleIssues.length && (
              <p className="empty">
                {issueFilter === "abertas" ? "Nenhuma pendência aberta. Tudo que voltou do cliente está fechado." : "Nada aqui ainda."}
              </p>
            )}
          </section>
        </>
      )}
    </main>
  );
}

export function ServiceForm({ service, users, onClose, onSave }) {
  const editando = Boolean(service);
  const [form, setForm] = useState(() => ({
    tipo: service?.tipo || SERVICE_TYPES[0],
    cliente: service?.cliente || "",
    local: service?.local || "",
    tecnico: service?.tecnico || "",
    data: service?.data || new Date().toISOString().slice(0, 10),
    horario: service?.horario || "08:00",
    horarioSaida: service?.horarioSaida || "",
    horarioRetorno: service?.horarioRetorno || "",
    descricao: service?.descricao || "",
  }));
  function field(key, value) { setForm((current) => ({ ...current, [key]: value })); }
  return <Modal onClose={onClose}><form onSubmit={(event) => { event.preventDefault(); onSave(form, service); }}>
    <div className="modal-head">
      <div><span className="op">{editando ? "EDITAR" : "NOVO ATENDIMENTO"}</span><h2>Assistência ou instalação</h2></div>
      <button type="button" className="close" onClick={onClose}><X /></button>
    </div>
    <div className="form-grid">
      <label>Tipo<select value={form.tipo} onChange={(e) => field("tipo", e.target.value)}>{SERVICE_TYPES.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label>Técnico<select value={form.tecnico} onChange={(e) => field("tecnico", e.target.value)} required><option value="">Selecione</option>{users.filter((item) => item.ativo && item.perfil !== "TV").map((item) => <option key={item.id} value={item.nome}>{item.nome}</option>)}</select></label>
    </div>
    <label>Cliente<input value={form.cliente} onChange={(e) => field("cliente", e.target.value)} required autoFocus placeholder="Ex.: Ambev Jaguariúna" /></label>
    <label>Endereço ou local<input value={form.local} onChange={(e) => field("local", e.target.value)} placeholder="Opcional" /></label>
    <div className="form-grid">
      <label>Data<input type="date" value={form.data} onChange={(e) => field("data", e.target.value)} required /></label>
      <label>Hora do atendimento<input type="time" value={form.horario} onChange={(e) => field("horario", e.target.value)} required /></label>
    </div>
    <div className="form-grid">
      <label>Sai da empresa<input type="time" value={form.horarioSaida} onChange={(e) => field("horarioSaida", e.target.value)} /></label>
      <label>Volta prevista<input type="time" value={form.horarioRetorno} onChange={(e) => field("horarioRetorno", e.target.value)} /></label>
    </div>
    <p className="field-note">Saída e volta são opcionais. Servem para o técnico saber a que horas precisa deixar a empresa e para você planejar o resto do dia dele.</p>
    <label>O que será feito<textarea value={form.descricao} onChange={(e) => field("descricao", e.target.value)} /></label>
    <div className="modal-actions">
      <button type="button" className="secondary" onClick={onClose}>Cancelar</button>
      <button className="primary">{editando ? "Salvar alterações" : "Agendar atendimento"}</button>
    </div>
  </form></Modal>;
}

export function ServiceModal({ service, users, canManage, canDelete, onClose, onEdit, onLeave, onFinish, onReopen, onDelete, onCreateIssue, onResolveIssue, onReopenIssue }) {
  const [report, setReport] = useState(service.relatorio || "");
  const [issueText, setIssueText] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const finished = service.status === "concluido";
  const author = users.find((item) => item.id === service.concluidoPorId);
  const leaver = users.find((item) => item.id === service.saidaPorId);
  const issues = service.pendencias || [];

  return <Modal onClose={onClose}>
    <div className="modal-head">
      <div>
        <span className="op">{service.tipo.toUpperCase()}</span>
        <h2>{service.cliente}</h2>
        {service.local && <p>{service.local}</p>}
      </div>
      <button className="close" onClick={onClose}><X /></button>
    </div>

    <div className="task-summary">
      <span><small>Técnico</small><b>{service.tecnico}</b></span>
      <span><small>Data e hora</small><b>{dateLabel(service.data)} às {service.horario}</b></span>
      <span><small>Situação</small><b>{SERVICE_STATES[service.status]}</b></span>
    </div>

    {(service.horarioSaida || service.horarioRetorno) && (
      <div className="trip-plan">
        <PlannedTrip service={service} />
        <small>Horários planejados para a viagem.</small>
      </div>
    )}

    <section className="observation"><small>O QUE SERÁ FEITO</small><p>{service.descricao || "Nenhuma instrução cadastrada."}</p></section>

    {service.saidaEm && <div className="service-trip-note"><Truck size={15} /> Saiu da empresa em {momentLabel(service.saidaEm)}{leaver ? ` por ${leaver.nome}` : ""}.</div>}
    {finished && <div className="service-done-note"><CheckCircle2 size={15} /> Concluído em {momentLabel(service.concluidoEm)}{author ? ` por ${author.nome}` : ""}.</div>}

    {!finished && !service.saidaEm && (
      <button className="leave-button" onClick={() => onLeave(service)}><LogOut size={17} /> Estou saindo para o atendimento</button>
    )}

    <p className="action-title">{finished ? "Relatório do atendimento" : "Voltou do cliente? Registre o relatório"}</p>
    <label className="report-label"><textarea value={report} onChange={(e) => setReport(e.target.value)} placeholder="Descreva o que foi feito, peças trocadas, pendências e orientações deixadas." /></label>
    <button className="primary wide" disabled={report.trim().length < 3} onClick={() => onFinish(service, report)}>
      {finished ? "Salvar correção do relatório" : "Concluir atendimento"}
    </button>

    <p className="action-title">Ficou alguma pendência?</p>
    <div className="issue-compact">
      {issues.map((issue) => (
        <IssueCard key={issue.id} issue={issue} contexto={false} canManage={canManage} canDelete={false}
          onResolve={onResolveIssue} onReopen={onReopenIssue} onDelete={() => {}} />
      ))}
      {!issues.length && <p className="issue-empty">Nada pendente deste atendimento.</p>}
      <div className="issue-new">
        <input value={issueText} onChange={(e) => setIssueText(e.target.value)} placeholder="Ex.: faltou o sensor indutivo M12" />
        <button className="secondary" disabled={issueText.trim().length < 3} onClick={() => { onCreateIssue(service, issueText); setIssueText(""); }}>Registrar</button>
      </div>
    </div>

    {canDelete && (confirmDelete
      ? <div className="danger-panel"><b>Excluir este atendimento?</b><p>O relatório e as pendências somem junto. Não dá para desfazer.</p><div><button className="secondary" onClick={() => setConfirmDelete(false)}>Cancelar</button><button className="danger" onClick={() => onDelete(service)}><Trash2 size={16} /> Excluir definitivamente</button></div></div>
      : <button className="link-danger" onClick={() => setConfirmDelete(true)}><Trash2 size={15} /> Excluir atendimento</button>)}

    <div className="modal-actions">
      {canManage && <button className="secondary" onClick={() => onEdit(service)}>Editar atendimento</button>}
      {canManage && finished && <button className="secondary" onClick={() => onReopen(service)}>Reabrir</button>}
      <button className="secondary" onClick={onClose}>Fechar</button>
    </div>
  </Modal>;
}

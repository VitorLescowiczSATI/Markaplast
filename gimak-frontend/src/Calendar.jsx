import { useMemo, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, UsersRound, Wrench } from "lucide-react";

import "./calendar.css";

const WEEKDAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const STATUS_LABELS = {
  todo: "A fazer",
  doing: "Em execução",
  paused: "Pausada",
  blocked: "Não realizada",
  done: "Concluída",
};

function isoDate(value) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDays(value, days) {
  const next = new Date(value);
  next.setDate(next.getDate() + days);
  return next;
}

function mondayOf(value) {
  return addDays(value, -((value.getDay() || 7) - 1));
}

/** Seis linhas de segunda a domingo cobrindo o mês inteiro. */
function monthGrid(reference) {
  const first = new Date(reference.getFullYear(), reference.getMonth(), 1);
  const start = mondayOf(first);
  return Array.from({ length: 42 }, (_, index) => addDays(start, index));
}

function initials(name = "") {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0] || "").join("").toUpperCase();
}

export function Calendar({ tasks, services, users, onOpenTask, onOpenService }) {
  const [mode, setMode] = useState("month");
  const [reference, setReference] = useState(() => new Date());
  const [person, setPerson] = useState("all");
  const [showServices, setShowServices] = useState(true);

  const events = useMemo(() => {
    const fromTasks = tasks.map((task) => ({
      key: `t-${task.id}`, kind: "task", data: task,
      date: task.dataPlanejada, time: task.horario,
      person: task.responsavel, status: task.status,
      title: task.titulo, detail: STATUS_LABELS[task.status] || task.status,
    }));
    const fromServices = showServices ? services.map((service) => ({
      key: `s-${service.id}`, kind: "service", data: service,
      date: service.data, time: service.horario,
      person: service.tecnico, status: service.status === "concluido" ? "done" : "doing",
      title: service.cliente, detail: service.tipo,
    })) : [];
    return [...fromTasks, ...fromServices]
      .filter((item) => person === "all" || item.person === person)
      .sort((a, b) => a.time.localeCompare(b.time) || a.title.localeCompare(b.title));
  }, [tasks, services, person, showServices]);

  const byDate = useMemo(() => {
    const map = new Map();
    for (const item of events) {
      if (!map.has(item.date)) map.set(item.date, []);
      map.get(item.date).push(item);
    }
    return map;
  }, [events]);

  const today = isoDate(new Date());
  const days = mode === "month" ? monthGrid(reference) : Array.from({ length: 7 }, (_, i) => addDays(mondayOf(reference), i));

  // Quem executa entra na grade mesmo sem nada marcado, porque a linha vazia é o ponto:
  // é assim que se enxerga quem ficou sem tarefa. PCP e administrador só aparecem
  // quando realmente têm algo atribuído, senão viram ruído toda semana.
  const rows = useMemo(() => {
    const names = new Set(users.filter((item) => item.ativo && item.perfil === "Fábrica").map((item) => item.nome));
    for (const item of events) names.add(item.person);
    return [...names].sort((a, b) => a.localeCompare(b, "pt-BR"));
  }, [users, events]);

  function step(direction) {
    setReference((current) => mode === "month"
      ? new Date(current.getFullYear(), current.getMonth() + direction, 1)
      : addDays(current, direction * 7));
  }

  function open(item) {
    if (item.kind === "task") onOpenTask(item.data);
    else onOpenService(item.data);
  }

  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(mondayOf(reference), i));
  const periodLabel = mode === "month"
    ? reference.toLocaleDateString("pt-BR", { month: "long", year: "numeric" })
    : `${weekDays[0].toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })} a ${weekDays[6].toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}`;

  return (
    <main className="page">
      <section className="intro">
        <div>
          <p className="eyebrow">PLANEJAMENTO</p>
          <h1>Calendário</h1>
          <p>Tudo que está marcado por dia, para enxergar o que falta e quem ficou sem tarefa.</p>
        </div>
        <div className="stats">
          <div><b>{events.filter((item) => item.date === today).length}</b><span>Marcado hoje</span></div>
          <div><b>{events.filter((item) => item.date > today).length}</b><span>Daqui pra frente</span></div>
        </div>
      </section>

      <div className="filters cal-toolbar">
        <div className="segmented">
          <button className={mode === "month" ? "active" : ""} onClick={() => setMode("month")}><CalendarDays size={15} /> Mês</button>
          <button className={mode === "team" ? "active" : ""} onClick={() => setMode("team")}><UsersRound size={15} /> Semana por pessoa</button>
        </div>
        <div className="cal-nav">
          <button onClick={() => step(-1)} aria-label="Período anterior"><ChevronLeft size={17} /></button>
          <strong>{periodLabel}</strong>
          <button onClick={() => step(1)} aria-label="Próximo período"><ChevronRight size={17} /></button>
          <button className="cal-today" onClick={() => setReference(new Date())}>Hoje</button>
        </div>
        {mode === "month" && (
          <label>Colaborador<select value={person} onChange={(e) => setPerson(e.target.value)}>
            <option value="all">Todos</option>
            {rows.map((name) => <option key={name} value={name}>{name}</option>)}
          </select></label>
        )}
        <label className="cal-switch"><input type="checkbox" checked={showServices} onChange={(e) => setShowServices(e.target.checked)} /> Mostrar assistências</label>
      </div>

      {mode === "month" ? (
        <section className="cal-month">
          {WEEKDAYS.map((label) => <div className="cal-weekday" key={label}>{label}</div>)}
          {days.map((day) => {
            const key = isoDate(day);
            const items = byDate.get(key) || [];
            const outside = day.getMonth() !== reference.getMonth();
            return (
              <div className={`cal-day${outside ? " outside" : ""}${key === today ? " today" : ""}`} key={key}>
                <span className="cal-day-number">{day.getDate()}</span>
                <div className="cal-day-items">
                  {items.slice(0, 3).map((item) => (
                    <button className={`cal-chip ${item.status}`} key={item.key} onClick={() => open(item)} title={`${item.time} · ${item.title} · ${item.person}`}>
                      {item.kind === "service" && <Wrench size={11} />}
                      <b>{item.time}</b>
                      <span>{item.title}</span>
                    </button>
                  ))}
                  {items.length > 3 && <span className="cal-more">mais {items.length - 3}</span>}
                </div>
              </div>
            );
          })}
        </section>
      ) : (
        <section className="cal-team-wrap">
          <table className="cal-team">
            <thead>
              <tr>
                <th>Colaborador</th>
                {weekDays.map((day) => (
                  <th key={isoDate(day)} className={isoDate(day) === today ? "today" : ""}>
                    {WEEKDAYS[(day.getDay() || 7) - 1]}<small>{day.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })}</small>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((name) => {
                const doSemana = weekDays.map((day) => (byDate.get(isoDate(day)) || []).filter((item) => item.person === name));
                const total = doSemana.reduce((sum, list) => sum + list.length, 0);
                return (
                  <tr key={name}>
                    <th scope="row"><span className="avatar">{initials(name)}</span><span><b>{name}</b><small>{total ? `${total} na semana` : "nada marcado"}</small></span></th>
                    {doSemana.map((list, index) => (
                      <td key={index} className={list.length ? "" : "vazio"}>
                        {list.map((item) => (
                          <button className={`cal-chip ${item.status}`} key={item.key} onClick={() => open(item)} title={`${item.time} · ${item.title}`}>
                            {item.kind === "service" && <Wrench size={11} />}
                            <b>{item.time}</b>
                            <span>{item.title}</span>
                          </button>
                        ))}
                      </td>
                    ))}
                  </tr>
                );
              })}
              {!rows.length && <tr><td colSpan={8} className="cal-empty">Nenhum colaborador ativo cadastrado.</td></tr>}
            </tbody>
          </table>
        </section>
      )}

      <p className="cal-legend">
        <span><i className="todo" /> A fazer</span>
        <span><i className="doing" /> Em execução</span>
        <span><i className="paused" /> Pausada</span>
        <span><i className="blocked" /> Não realizada</span>
        <span><i className="done" /> Concluída</span>
        <span><Wrench size={13} /> Assistência ou instalação</span>
      </p>
    </main>
  );
}

// Modo demonstração: a mesma interface do api.js, mas tudo em memória no navegador.
// Nada daqui chega na API nem no banco da fábrica. O estado fica no localStorage de
// quem está vendo, e é recriado todo dia para o quadro de "hoje" nunca ficar vazio.
//
// As regras de negócio espelham backend/app/gimak/api.py e analytics.py. Mudou lá,
// muda aqui, senão a demonstração mostra um sistema que não existe.

const STORAGE_KEY = "gimak.demo.v2";
const OPEN_STATUSES = new Set(["todo", "doing", "paused"]);
const ADMIN = "Administrador";

// ---------------------------------------------------------------- datas

function pad(value) {
  return String(value).padStart(2, "0");
}

function isoDate(value) {
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`;
}

// n-ésimo dia útil a partir de hoje (0 = hoje, negativo = para trás).
function businessDay(offset) {
  const day = new Date();
  day.setHours(12, 0, 0, 0);
  const step = offset < 0 ? -1 : 1;
  let remaining = Math.abs(offset);
  while (remaining > 0) {
    day.setDate(day.getDate() + step);
    if (day.getDay() !== 0 && day.getDay() !== 6) remaining -= 1;
  }
  return isoDate(day);
}

function at(dateIso, hhmm) {
  return new Date(`${dateIso}T${hhmm}:00`);
}

function plusSeconds(date, seconds) {
  return new Date(date.getTime() + seconds * 1000);
}

function localDateOf(value) {
  return isoDate(new Date(value));
}

function deadline(task) {
  return at(task.dataPlanejada, task.horario);
}

// ---------------------------------------------------------------- dados fictícios

const USERS = [
  { nome: "Administrador Demo", username: "admin", perfil: ADMIN, cargo: "Diretoria" },
  { nome: "Paula Ribeiro", username: "paula", perfil: "PCP", cargo: "Planejamento" },
  { nome: "Marcos Silva", username: "marcos", perfil: "Fábrica", cargo: "Montador" },
  { nome: "Rafael Costa", username: "rafael", perfil: "Fábrica", cargo: "Soldador" },
  { nome: "Juliana Alves", username: "juliana", perfil: "Fábrica", cargo: "Eletricista" },
  { nome: "Leandro Souza", username: "leandro", perfil: "Fábrica", cargo: "Técnico de campo" },
  { nome: "Diego Martins", username: "diego", perfil: "Fábrica", cargo: "Técnico de campo" },
  { nome: "TV da fábrica", username: "tv", perfil: "TV", cargo: "" },
];

const PROJECTS = [
  { cliente: "Laticínios Boa Vista", equipamento: "Envasadora GK 500" },
  { cliente: "Cooperativa Vale Verde", equipamento: "Misturador MX 300" },
  { cliente: "Alimentos Serra Azul", equipamento: "Esteira transportadora ET 12" },
  { cliente: "Bebidas Rio Claro", equipamento: "Rotuladora RT 80" },
  { cliente: "Frigorífico Campo Belo", equipamento: "Seladora SL 40" },
  { cliente: "Grãos do Sul", equipamento: "Silo pulmão SP 20", concluidoHaDias: 7 },
];

// [dia útil, prazo, ordem, título, responsável, projeto (1 a 6), situação, detalhes]
// Detalhes: inicio (HH:MM), horas trabalhadas, pausa (motivo de uma pausa já retomada),
// motivo (pausa ou não realizada atual), urgente.
const TASKS = [
  [-10, "17:00", "OS 1011", "Montagem da estrutura do silo", "Marcos Silva", 6, "done", { inicio: "08:00", horas: 5.5 }],
  [-9, "17:00", "OS 1012", "Solda das chapas do silo", "Rafael Costa", 6, "done", { inicio: "07:40", horas: 6 }],
  [-8, "12:00", "OS 1013", "Teste de carga do silo", "Juliana Alves", 6, "done", { inicio: "08:10", horas: 3 }],
  [-7, "17:00", "OS 1021", "Corte das chapas", "Rafael Costa", 1, "done", { inicio: "08:00", horas: 3.17 }],
  [-6, "17:00", "OS 1022", "Dobra da carenagem", "Marcos Silva", 1, "done", { inicio: "08:15", horas: 4, pausa: "Aguardando a ponte rolante liberar" }],
  [-5, "12:00", "OS 1023", "Usinagem dos flanges", "Rafael Costa", 1, "done", { inicio: "07:30", horas: 6.4 }],
  [-5, "17:00", "OS 1030", "Corte do chassi", "Marcos Silva", 2, "done", { inicio: "08:00", horas: 2.67 }],
  [-4, "17:00", "OS 1031", "Solda do chassi", "Rafael Costa", 2, "done", { inicio: "08:00", horas: 5 }],
  [-4, "17:00", "OS 1040", "Montagem dos roletes", "Juliana Alves", 3, "done", { inicio: "09:00", horas: 3 }],
  [-3, "17:00", "OS 1032", "Montagem do tanque", "Marcos Silva", 2, "done", { inicio: "08:00", horas: 6 }],
  [-3, "15:00", "OS 1041", "Instalação do motorredutor", "Juliana Alves", 3, "done", { inicio: "08:30", horas: 2.5 }],
  [-2, "17:00", "OS 1024", "Pintura da base", "Marcos Silva", 1, "done", { inicio: "08:00", horas: 3 }],
  [-2, "17:00", "OS 1050", "Corte da estrutura", "Rafael Costa", 4, "done", { inicio: "13:00", horas: 2 }],
  [-1, "17:00", "OS 1033", "Instalação das pás", "Marcos Silva", 2, "done", { inicio: "08:00", horas: 4 }],
  [0, "17:00", "OS 1042", "Ajuste de tensão da correia", "Juliana Alves", 3, "blocked", { motivo: "A correia veio do fornecedor na medida errada" }],
  [-1, "17:00", "OS 1051", "Solda da estrutura da rotuladora", "Rafael Costa", 4, "doing", { desdeMinutos: 55, horas: 3 }],
  [0, "10:00", "TAREFA", "Organização do almoxarifado", "Marcos Silva", null, "done", { inicio: "07:30", horas: 1 }],
  [0, "17:00", "OS 1025", "Montagem do carrossel de bicos", "Marcos Silva", 1, "doing", { desdeMinutos: 102, urgente: true }],
  [0, "17:00", "OS 1034", "Elétrica do painel do misturador", "Juliana Alves", 2, "paused", { horas: 1.08, motivo: "Faltou disjuntor de 32A no estoque" }],
  [0, "17:00", "OS 1026", "Teste de vazamento", "Marcos Silva", 1, "todo", {}],
  [0, "17:00", "OS 1043", "Proteções da esteira", "Juliana Alves", 3, "todo", {}],
  [0, "17:00", "OS 1060", "Corte das chapas da seladora", "Rafael Costa", 5, "todo", {}],
  [1, "17:00", "OS 1027", "Montagem do painel elétrico", "Juliana Alves", 1, "todo", {}],
  [1, "17:00", "OS 1061", "Dobra da carenagem da seladora", "Marcos Silva", 5, "todo", {}],
  [1, "12:00", "OS 1053", "Montagem do cabeçote", "Rafael Costa", 4, "todo", { urgente: true }],
  [2, "17:00", "OS 1035", "Teste de mistura", "Marcos Silva", 2, "todo", {}],
  [2, "17:00", "OS 1044", "Teste da esteira com carga", "Juliana Alves", 3, "todo", {}],
  [3, "17:00", "OS 1028", "Comissionamento interno", "Marcos Silva", 1, "todo", {}],
  [3, "17:00", "OS 1062", "Solda da seladora", "Rafael Costa", 5, "todo", {}],
  [4, "17:00", "OS 1054", "Pintura da rotuladora", "Marcos Silva", 4, "todo", {}],
];

// [tipo, cliente, local, técnico, ida, volta, saída, retorno, descrição, situação, relatório, pendências]
// Pendência: [descrição, resolução ou null].
const SERVICES = [
  ["Instalação", "Grãos do Sul", "Rodovia BR 277, km 40, Cascavel PR", "Diego Martins", -8, -6, "06:00", "18:00",
    "Instalação do silo pulmão SP 20 e treinamento da equipe.", "concluido",
    "Silo instalado e testado com carga. Equipe do cliente treinada na operação e na limpeza.", []],
  ["Assistência técnica", "Indústria de Sucos Primavera", "Av. das Indústrias, 1200, Londrina PR", "Leandro Souza", -6, null, "07:00", "17:00",
    "Dosadora com variação de volume.", "concluido",
    "Troca do sensor de nível e regulagem da dosadora. Máquina liberada para produção.",
    [["Enviar sensor de nível reserva para o cliente", "Enviado pela transportadora com nota de remessa."]]],
  ["Assistência técnica", "Panificadora Estrela", "Rua Sete de Setembro, 455, Maringá PR", "Diego Martins", -4, null, "08:00", "15:00",
    "Esteira fazendo ruído na saída do forno.", "concluido",
    "Rolamento da esteira desgastado. Lubrificado para seguir rodando até a troca.",
    [["Trocar o rolamento da esteira na próxima visita", null]]],
  ["Assistência técnica", "Laticínios Boa Vista", "Estrada Municipal, 80, Toledo PR", "Diego Martins", -2, null, "07:30", "16:00",
    "Vazamento em dois bicos da envasadora antiga.", "concluido",
    "Alinhamento dos bicos refeito e vedações trocadas. Faltou o anel de vedação do bico 4.",
    [["Anel de vedação do bico 4 precisa ser enviado", null]]],
  ["Instalação", "Cooperativa Vale Verde", "Linha São Pedro, s/n, Chapecó SC", "Leandro Souza", 0, 2, "06:00", "18:00",
    "Instalação do misturador antigo na unidade nova da cooperativa.", "em_rota", "", []],
  ["Assistência técnica", "Frigorífico Campo Belo", "Rua Bento Gonçalves, 90, Xanxerê SC", "Diego Martins", 0, null, "13:30", "18:00",
    "Seladora antiga perdendo temperatura.", "agendado", "", []],
  ["Assistência técnica", "Bebidas Rio Claro", "Av. Brasil, 3100, Cascavel PR", "Diego Martins", 1, null, "07:00", "17:00",
    "Visita técnica para medir a linha antes da rotuladora nova.", "agendado", "", []],
  ["Assistência técnica", "Alimentos Serra Azul", "Rodovia PR 317, km 12, Toledo PR", "Leandro Souza", 3, null, "07:00", "16:00",
    "Revisão preventiva da esteira de saída.", "agendado", "", []],
];

function seed() {
  const now = new Date();
  const state = {
    seededOn: isoDate(now),
    session: { username: "admin", loggedOut: false },
    seq: { user: 0, project: 0, task: 0, entry: 0, service: 0, issue: 0 },
    users: [], projects: [], tasks: [], services: [], issues: [],
  };
  const next = (kind) => (state.seq[kind] += 1);
  const userId = (nome) => state.users.find((item) => item.nome === nome)?.id ?? null;

  USERS.forEach((item) => state.users.push({ id: next("user"), ativo: true, ...item }));

  const createdAt = at(businessDay(-12), "08:00").toISOString();
  PROJECTS.forEach(({ concluidoHaDias, ...item }) => {
    state.projects.push({
      id: next("project"), ativo: true, createdAt, ...item,
      concluidoEm: concluidoHaDias ? at(businessDay(-concluidoHaDias), "16:00").toISOString() : null,
    });
  });

  for (const [offset, horario, ordem, titulo, responsavel, projeto, status, extra] of TASKS) {
    const dataPlanejada = businessDay(offset);
    const task = {
      id: next("task"), titulo, ordem, responsavel, dataPlanejada, horario,
      prioridade: extra.urgente ? "Urgente" : "Normal", status, observacao: "", motivo: "",
      elapsedSeconds: 0, startedAt: null, finishedAt: null, projetoId: projeto,
      createdAt: at(businessDay(Math.min(offset, 0) - 2), "07:00").toISOString(), historico: [],
    };
    const actor = userId(responsavel);
    const log = (previous, novo, when, motivo = "") => task.historico.push({
      id: next("entry"), usuarioId: actor, statusAnterior: previous, statusNovo: novo, motivo,
      createdAt: when.toISOString(),
    });
    const worked = Math.round((extra.horas || 0) * 3600);

    if (status === "done") {
      const start = at(dataPlanejada, extra.inicio);
      if (extra.pausa) {
        const half = Math.round(worked / 2);
        const pausedAt = plusSeconds(start, half);
        const resumedAt = plusSeconds(pausedAt, 40 * 60);
        log("todo", "doing", start);
        log("doing", "paused", pausedAt, extra.pausa);
        log("paused", "doing", resumedAt);
        task.finishedAt = plusSeconds(resumedAt, worked - half).toISOString();
      } else {
        log("todo", "doing", start);
        task.finishedAt = plusSeconds(start, worked).toISOString();
      }
      log("doing", "done", new Date(task.finishedAt));
      task.elapsedSeconds = worked;
    } else if (status === "doing") {
      const startedAt = new Date(now.getTime() - extra.desdeMinutos * 60 * 1000);
      if (worked) {
        // Já trabalhou num dia anterior, pausou e retomou hoje.
        const firstStart = at(dataPlanejada, "08:00");
        log("todo", "doing", firstStart);
        log("doing", "paused", plusSeconds(firstStart, worked), "Fim do expediente");
        log("paused", "doing", startedAt);
      } else {
        log("todo", "doing", startedAt);
      }
      task.elapsedSeconds = worked;
      task.startedAt = startedAt.toISOString();
    } else if (status === "paused") {
      const start = new Date(now.getTime() - (worked + 25 * 60) * 1000);
      log("todo", "doing", start);
      log("doing", "paused", plusSeconds(start, worked), extra.motivo);
      task.elapsedSeconds = worked;
      task.motivo = extra.motivo;
    } else if (status === "blocked") {
      const when = at(dataPlanejada, "10:20");
      log("todo", "blocked", when, extra.motivo);
      task.motivo = extra.motivo;
      task.finishedAt = when.toISOString();
    }
    state.tasks.push(task);
  }

  for (const [tipo, cliente, local, tecnico, ida, volta, saida, retorno, descricao, status, relatorio, pendencias] of SERVICES) {
    const data = businessDay(ida);
    const dataVolta = volta === null ? null : businessDay(volta);
    const tecnicoId = userId(tecnico);
    const ultimoDia = dataVolta || data;
    const service = {
      id: next("service"), tipo, cliente, local, tecnico, data, dataVolta,
      horario: saida, horarioSaida: saida, horarioRetorno: retorno, descricao, status, relatorio,
      saidaEm: null, saidaPorId: null, concluidoEm: null, concluidoPorId: null,
      createdAt: at(businessDay(Math.min(ida, 0) - 3), "10:00").toISOString(), pendencias: [],
    };
    if (status !== "agendado") {
      service.saidaEm = plusSeconds(at(data, saida), 10 * 60).toISOString();
      service.saidaPorId = tecnicoId;
    }
    if (status === "concluido") {
      service.concluidoEm = at(ultimoDia, retorno).toISOString();
      service.concluidoPorId = tecnicoId;
    }
    state.services.push(service);
    for (const [texto, resolucao] of pendencias) {
      state.issues.push({
        id: next("issue"), atendimentoId: service.id, descricao: texto,
        status: resolucao ? "resolvida" : "aberta", resolucao: resolucao || "",
        criadoPorId: tecnicoId, resolvidoPorId: resolucao ? userId("Paula Ribeiro") : null,
        resolvidoEm: resolucao ? at(businessDay(ida + 2), "11:00").toISOString() : null,
        createdAt: at(ultimoDia, retorno).toISOString(),
      });
    }
  }
  return state;
}

// ---------------------------------------------------------------- estado

let state = null;

function load() {
  if (state) return state;
  try {
    const saved = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null");
    if (saved && saved.seededOn === isoDate(new Date())) state = saved;
  } catch {
    // Armazenamento bloqueado ou corrompido: começa do zero.
  }
  if (!state) {
    state = seed();
    save();
  }
  return state;
}

function save() {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Sem armazenamento a demonstração segue funcionando, só não sobrevive ao recarregar.
  }
}

function reset(username) {
  const previous = username || load().session.username;
  state = seed();
  state.session.username = previous;
  save();
}

function fail(message) {
  throw new Error(message);
}

function clone(value) {
  return value === undefined ? null : JSON.parse(JSON.stringify(value));
}

function currentUser() {
  const { session, users } = load();
  if (session.loggedOut) fail("Sessão encerrada");
  return users.find((item) => item.username === session.username) || users[0];
}

// Mesma regra do require_gimak_roles: o administrador passa sempre.
function requireRoles(...roles) {
  const user = currentUser();
  if (user.perfil !== ADMIN && !roles.includes(user.perfil)) fail("Seu perfil não tem acesso a esta ação");
  return user;
}

function respond(work) {
  return new Promise((resolve, reject) => {
    // Um respiro curto para os estados de carregamento aparecerem como no sistema real.
    window.setTimeout(() => {
      try {
        const result = work();
        save();
        resolve(clone(result));
      } catch (err) {
        reject(err);
      }
    }, 120);
  });
}

function findOr404(list, id, message) {
  const item = list.find((entry) => entry.id === Number(id));
  if (!item) fail(message);
  return item;
}

function cleanText(value) {
  return typeof value === "string" ? value.trim() : value;
}

function applyPatch(target, payload, { skipNull = false } = {}) {
  for (const [key, value] of Object.entries(payload || {})) {
    if (value === undefined || (skipNull && value === null)) continue;
    target[key] = cleanText(value);
  }
}

function serviceWithIssues(service) {
  return { ...service, pendencias: load().issues.filter((item) => item.atendimentoId === service.id) };
}

function normalizeName(value = "") {
  return value.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLocaleLowerCase("pt-BR").split(/\s+/).filter(Boolean).join(" ");
}

// ---------------------------------------------------------------- indicadores e TV (analytics.py)

function percentage(numerator, denominator) {
  return denominator ? Math.round((1000 * numerator) / denominator) / 10 : null;
}

function completionTime(task) {
  if (task.status !== "done") return null;
  let completed = null;
  const entries = [...task.historico].sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt) || a.id - b.id);
  for (const entry of entries) {
    if (entry.statusNovo !== "done") completed = null;
    else if (completed === null) completed = new Date(entry.createdAt);
  }
  return completed || (task.finishedAt ? new Date(task.finishedAt) : null);
}

function recordedSeconds(task, now) {
  let seconds = task.elapsedSeconds || 0;
  if (task.status === "doing" && task.startedAt) seconds += Math.max(0, Math.floor((now - new Date(task.startedAt)) / 1000));
  return Math.max(0, seconds);
}

function isOverdue(task, now) {
  return OPEN_STATUSES.has(task.status) && deadline(task) < now;
}

function byDeadline(a, b) {
  return deadline(a) - deadline(b) || a.id - b.id;
}

function taskPayload(task, now, projects) {
  const project = projects.get(task.projetoId);
  const overdue = isOverdue(task, now);
  return {
    id: task.id, titulo: task.titulo, ordem: task.ordem, responsavel: task.responsavel,
    prioridade: task.prioridade, status: task.status, dataPlanejada: task.dataPlanejada,
    horario: task.horario, prazo: deadline(task).toISOString(), atrasada: overdue,
    atrasoSegundos: overdue ? Math.max(0, Math.floor((now - deadline(task)) / 1000)) : 0,
    tempoRegistradoSegundos: recordedSeconds(task, now), projetoId: task.projetoId,
    projeto: project ? `${project.cliente} · ${project.equipamento}` : null,
    startedAt: task.startedAt,
  };
}

function projectPayloads(projects, tasks, now) {
  const result = [];
  for (const project of projects.values()) {
    if (!project.ativo || project.concluidoEm) continue;
    const own = tasks.filter((task) => task.projetoId === project.id);
    const completed = own.filter((task) => task.status === "done").length;
    result.push({
      id: project.id, cliente: project.cliente, equipamento: project.equipamento,
      total: own.length, concluidas: completed,
      emExecucao: own.filter((task) => task.status === "doing").length,
      atrasadas: own.filter((task) => isOverdue(task, now)).length,
      percentualConclusao: percentage(completed, own.length),
    });
  }
  return result.sort((a, b) => b.emExecucao - a.emExecucao || b.atrasadas - a.atrasadas || b.id - a.id);
}

function daysBetween(inicio, fim) {
  const days = [];
  const cursor = new Date(`${inicio}T12:00:00`);
  const last = new Date(`${fim}T12:00:00`);
  while (cursor <= last) {
    days.push(isoDate(cursor));
    cursor.setDate(cursor.getDate() + 1);
  }
  return days;
}

function dailySeries(tasks, completions, inicio, fim) {
  return daysBetween(inicio, fim).map((day) => ({
    data: day,
    planejadas: tasks.filter((task) => task.dataPlanejada === day).length,
    concluidas: [...completions.values()].filter((value) => value && localDateOf(value) === day).length,
  }));
}

const CRITERIOS = {
  coorte: "Resumo e ranking consideram tarefas com data planejada no período, no estado atual. Atrasos em aberto incluem todo o histórico.",
  prazo: "Prazo = data planejada + horário cadastrado, no fuso America/Sao_Paulo. Tarefas não realizadas são contadas à parte dos atrasos em aberto.",
  ranking: "Ordenado por tarefas concluídas atribuídas ao responsável. Quantidade e tempo registrados não medem qualidade, esforço ou produtividade individual. Vínculo de nome só é feito quando corresponde a um único usuário.",
  adesao: "Apontamentos são mudanças de status feitas pelo usuário no período. Apontamento próprio é a proporção de tarefas atribuídas no período em que ele registrou uma mudança. Não mede presença nem login; contas compartilhadas não identificam pessoas.",
  tempo: "Tempo registrado acumulado nas tarefas planejadas no período, incluindo execução em andamento. Pode incluir trabalho realizado fora do período; não representa jornada.",
  serieDiaria: "Planejadas por data de planejamento; concluídas por data da conclusão final das tarefas atualmente concluídas, independentemente do planejamento. Reaberturas deixam de contar como concluídas.",
};

function buildIndicators(inicioParam, fimParam) {
  const { tasks, users } = load();
  const now = new Date();
  const today = isoDate(now);
  const inicio = inicioParam || today;
  const fim = fimParam || today;
  if (fim < inicio) fail("A data final deve ser igual ou posterior à inicial");
  if (daysBetween(inicio, fim).length > 366) fail("Selecione um período de até 366 dias");
  const lower = new Date(`${inicio}T00:00:00`);
  const upper = new Date(`${fim}T00:00:00`);
  upper.setDate(upper.getDate() + 1);

  const projects = new Map(load().projects.map((item) => [item.id, item]));
  const completions = new Map(tasks.map((task) => [task.id, completionTime(task)]));
  const inPeriod = (task) => task.dataPlanejada >= inicio && task.dataPlanejada <= fim;
  const cohort = tasks.filter(inPeriod);
  const overdue = tasks.filter((task) => isOverdue(task, now)).sort(byDeadline);
  const completed = cohort.filter((task) => task.status === "done");
  const known = completed.filter((task) => completions.get(task.id));
  const onTime = known.filter((task) => completions.get(task.id) <= deadline(task)).length;
  const count = (status) => cohort.filter((task) => task.status === status).length;

  const byName = new Map();
  for (const user of users) {
    if (user.perfil === "TV") continue;
    const key = normalizeName(user.nome);
    byName.set(key, [...(byName.get(key) || []), user]);
  }
  const assignments = new Map();
  const groups = new Map();
  for (const task of tasks) {
    const key = normalizeName(task.responsavel);
    const matches = byName.get(key) || [];
    assignments.set(task.id, matches.length === 1 ? matches[0].id : null);
    if (inPeriod(task)) groups.set(key, [...(groups.get(key) || []), task]);
  }

  const ranking = [...groups.entries()].map(([key, group]) => {
    const matches = byName.get(key) || [];
    const linked = matches.length === 1 ? matches[0] : null;
    const finished = group.filter((task) => task.status === "done");
    const knownGroup = finished.filter((task) => completions.get(task.id));
    const inTime = knownGroup.filter((task) => completions.get(task.id) <= deadline(task)).length;
    return {
      usuarioId: linked ? linked.id : null,
      nome: linked ? linked.nome : group[0].responsavel,
      vinculo: linked ? "unico" : matches.length ? "ambiguo" : "sem_usuario",
      planejadas: group.length, concluidas: finished.length,
      naoRealizadas: group.filter((task) => task.status === "blocked").length,
      atrasadas: group.filter((task) => isOverdue(task, now)).length,
      noPrazo: inTime, concluidasComPrazoConhecido: knownGroup.length,
      taxaConclusao: percentage(finished.length, group.length),
      taxaNoPrazo: percentage(inTime, knownGroup.length),
      tempoRegistradoSegundos: group.reduce((sum, task) => sum + recordedSeconds(task, now), 0),
    };
  }).sort((a, b) => b.concluidas - a.concluidas || normalizeName(a.nome).localeCompare(normalizeName(b.nome)));

  const eventsByUser = new Map();
  for (const task of tasks) {
    for (const entry of task.historico) {
      const when = new Date(entry.createdAt);
      if (when >= lower && when < upper && when <= now) {
        eventsByUser.set(entry.usuarioId, [...(eventsByUser.get(entry.usuarioId) || []), { ...entry, tarefaId: task.id }]);
      }
    }
  }
  const assignedByUser = new Map();
  for (const task of cohort) {
    const owner = assignments.get(task.id);
    if (owner !== null) assignedByUser.set(owner, new Set([...(assignedByUser.get(owner) || []), task.id]));
  }
  const adesao = [...users]
    .sort((a, b) => normalizeName(a.nome).localeCompare(normalizeName(b.nome)))
    .filter((user) => user.perfil !== "TV")
    .map((user) => {
      const events = eventsByUser.get(user.id) || [];
      const touched = new Set(events.map((entry) => entry.tarefaId));
      const own = assignedByUser.get(user.id) || new Set();
      const ownTouched = [...own].filter((id) => touched.has(id)).length;
      const last = events.reduce((latest, entry) => (!latest || new Date(entry.createdAt) > new Date(latest) ? entry.createdAt : latest), null);
      return {
        usuarioId: user.id, nome: user.nome, username: user.username, perfil: user.perfil, ativo: user.ativo,
        apontamentos: events.length, tarefasMovimentadas: touched.size,
        diasAtivos: new Set(events.map((entry) => localDateOf(entry.createdAt))).size,
        ultimoApontamento: last, tarefasAtribuidas: own.size, tarefasPropriasApontadas: ownTouched,
        taxaApontamentoProprio: percentage(ownTouched, own.size),
      };
    });

  const pauses = new Map();
  for (const task of tasks.filter((item) => item.status === "paused")) {
    const reason = task.motivo.trim() || "Sem justificativa registrada";
    pauses.set(reason, (pauses.get(reason) || 0) + 1);
  }

  return {
    geradoEm: now.toISOString(), fusoHorario: "America/Sao_Paulo", periodo: { inicio, fim },
    criterios: CRITERIOS,
    resumo: {
      planejadas: cohort.length, concluidas: completed.length, aFazer: count("todo"),
      emExecucao: count("doing"), pausadas: count("paused"), naoRealizadas: count("blocked"),
      atrasadasNoPeriodo: cohort.filter((task) => isOverdue(task, now)).length,
      atrasadasEmAberto: overdue.length, concluidasNoPrazo: onTime, concluidasComPrazoConhecido: known.length,
      taxaConclusao: percentage(completed.length, cohort.length), taxaNoPrazo: percentage(onTime, known.length),
      tempoRegistradoSegundos: cohort.reduce((sum, task) => sum + recordedSeconds(task, now), 0),
    },
    ranking, adesao,
    serieDiaria: dailySeries(tasks, completions, inicio, fim),
    atrasadas: overdue.map((task) => taskPayload(task, now, projects)),
    motivosPausa: [...pauses.entries()].sort((a, b) => b[1] - a[1]).map(([motivo, quantidade]) => ({ motivo, quantidade })),
    projetos: projectPayloads(projects, tasks, now),
  };
}

function buildTvPanel() {
  const { tasks } = load();
  const now = new Date();
  const today = isoDate(now);
  const weekAgo = new Date(now);
  weekAgo.setDate(weekAgo.getDate() - 6);
  const projects = new Map(load().projects.map((item) => [item.id, item]));
  const completions = new Map(tasks.map((task) => [task.id, completionTime(task)]));
  const todayTasks = tasks.filter((task) => task.dataPlanejada === today);
  const doing = tasks.filter((task) => task.status === "doing").sort(byDeadline);
  const paused = tasks.filter((task) => task.status === "paused").sort(byDeadline);
  const overdue = tasks.filter((task) => isOverdue(task, now)).sort(byDeadline);
  const events = tasks
    .flatMap((task) => task.historico.map((entry) => ({ entry, task })))
    .filter(({ entry }) => ["doing", "done"].includes(entry.statusNovo) && entry.statusAnterior !== entry.statusNovo && new Date(entry.createdAt) <= now)
    .sort((a, b) => new Date(b.entry.createdAt) - new Date(a.entry.createdAt) || b.entry.id - a.entry.id);
  const plannedDone = todayTasks.filter((task) => task.status === "done").length;
  return {
    geradoEm: now.toISOString(), fusoHorario: "America/Sao_Paulo", hoje: today,
    resumo: {
      planejadasHoje: todayTasks.length, concluidasHojePlanejadas: plannedDone,
      taxaConclusaoHoje: percentage(plannedDone, todayTasks.length),
      emExecucao: doing.length, pausadas: paused.length, atrasadasEmAberto: overdue.length,
      concluidasHoje: [...completions.values()].filter((value) => value && localDateOf(value) === today).length,
    },
    emExecucao: doing.map((task) => taskPayload(task, now, projects)),
    pausadas: paused.map((task) => taskPayload(task, now, projects)),
    atrasadas: overdue.map((task) => taskPayload(task, now, projects)),
    serieDiaria: dailySeries(tasks, completions, isoDate(weekAgo), today),
    projetos: projectPayloads(projects, tasks, now),
    ultimosEventos: events.slice(0, 12).map(({ entry, task }) => ({
      id: entry.id, tarefaId: task.id, titulo: task.titulo, responsavel: task.responsavel,
      status: entry.statusNovo, ocorridoEm: entry.createdAt,
    })),
  };
}

// ---------------------------------------------------------------- ordenações do backend

function sortTasks(list) {
  return [...list].sort((a, b) =>
    b.dataPlanejada.localeCompare(a.dataPlanejada) || a.horario.localeCompare(b.horario) || b.id - a.id);
}

function sortServices(list) {
  const departure = (item) => item.horarioSaida || item.horario;
  return [...list].sort((a, b) =>
    b.data.localeCompare(a.data) || departure(a).localeCompare(departure(b)) || b.id - a.id);
}

// ---------------------------------------------------------------- API

const HORARIO = /^([01]\d|2[0-3]):[0-5]\d$/;

export const demoApi = {
  isDemo: true,
  hasToken: () => !load().session.loggedOut,
  setAccessToken: (token) => {
    load().session.loggedOut = !token;
    save();
  },
  login: (username, senha) => respond(() => {
    const user = load().users.find((item) => item.username === String(username).trim().toLowerCase());
    if (!user || !user.ativo || !String(senha || "").length) fail("Usuário ou senha inválidos");
    state.session = { username: user.username, loggedOut: false };
    return { accessToken: "demo", tokenType: "bearer", usuario: user };
  }),
  me: () => respond(() => currentUser()),

  getIndicators: (inicio, fim) => respond(() => {
    requireRoles(ADMIN);
    return buildIndicators(inicio, fim);
  }),
  getTVPanel: () => respond(() => {
    currentUser();
    return buildTvPanel();
  }),

  listUsers: () => respond(() => {
    requireRoles("PCP", "Fábrica");
    return [...load().users].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  }),
  createUser: (payload) => respond(() => {
    requireRoles(ADMIN);
    const username = cleanText(payload.username || "").toLowerCase();
    if (!/^[a-z0-9._-]{3,80}$/.test(username)) fail("Nome de usuário inválido");
    if ((payload.senha || "").length < 8) fail("A senha precisa ter pelo menos 8 caracteres");
    if (load().users.some((item) => item.username === username)) fail("Nome de usuário já está em uso");
    const user = {
      id: (state.seq.user += 1), nome: cleanText(payload.nome), username,
      perfil: payload.perfil || "Fábrica", cargo: cleanText(payload.cargo || ""), ativo: true,
    };
    state.users.push(user);
    return user;
  }),
  updateUser: (id, payload) => respond(() => {
    const admin = requireRoles(ADMIN);
    const user = findOr404(load().users, id, "Usuário não encontrado");
    if (user.id === admin.id && (payload.ativo === false || (payload.perfil && payload.perfil !== ADMIN))) {
      fail("O administrador não pode remover o próprio acesso");
    }
    const antigo = user.nome;
    applyPatch(user, payload, { skipNull: true });
    if (user.nome !== antigo) {
      const homonimo = state.users.some((item) => item.id !== user.id && normalizeName(item.nome) === normalizeName(antigo));
      if (!homonimo) {
        state.tasks.filter((task) => task.responsavel === antigo).forEach((task) => { task.responsavel = user.nome; });
        state.services.filter((item) => item.tecnico === antigo).forEach((item) => { item.tecnico = user.nome; });
      }
    }
    return user;
  }),
  resetPassword: (id, senha) => respond(() => {
    requireRoles(ADMIN);
    findOr404(load().users, id, "Usuário não encontrado");
    if ((senha || "").length < 8) fail("A senha precisa ter pelo menos 8 caracteres");
    return null;
  }),

  listProjects: (situacao = "andamento") => respond(() => {
    requireRoles("PCP", "Fábrica");
    let list = load().projects.filter((item) => item.ativo);
    if (situacao === "andamento") list = list.filter((item) => !item.concluidoEm);
    else if (situacao === "concluidos") list = list.filter((item) => item.concluidoEm);
    return list.sort((a, b) => b.id - a.id);
  }),
  createProject: (payload) => respond(() => {
    requireRoles("PCP");
    const project = {
      id: (state.seq.project += 1), cliente: cleanText(payload.cliente), equipamento: cleanText(payload.equipamento),
      ativo: true, concluidoEm: null, createdAt: new Date().toISOString(),
    };
    state.projects.push(project);
    return project;
  }),
  updateProject: (id, payload) => respond(() => {
    requireRoles("PCP");
    const project = findOr404(load().projects.filter((item) => item.ativo), id, "Projeto não encontrado");
    const { concluido, ...rest } = payload;
    applyPatch(project, rest);
    if (concluido === true && !project.concluidoEm) project.concluidoEm = new Date().toISOString();
    else if (concluido === false) project.concluidoEm = null;
    return project;
  }),

  listTasks: () => respond(() => {
    requireRoles("PCP", "Fábrica");
    return sortTasks(load().tasks);
  }),
  createTask: (payload) => respond(() => {
    requireRoles("PCP");
    if (payload.projetoId && !load().projects.some((item) => item.id === Number(payload.projetoId))) fail("Projeto não encontrado");
    if (payload.horario && !HORARIO.test(payload.horario)) fail("Horário inválido");
    const task = {
      id: (state.seq.task += 1), titulo: cleanText(payload.titulo), ordem: cleanText(payload.ordem || "TAREFA"),
      responsavel: cleanText(payload.responsavel), dataPlanejada: payload.dataPlanejada,
      horario: payload.horario || "08:00", prioridade: payload.prioridade || "Normal", status: "todo",
      observacao: cleanText(payload.observacao || ""), motivo: "", elapsedSeconds: 0, startedAt: null,
      finishedAt: null, projetoId: payload.projetoId ? Number(payload.projetoId) : null,
      createdAt: new Date().toISOString(), historico: [],
    };
    state.tasks.push(task);
    return task;
  }),
  updateTask: (id, payload) => respond(() => {
    requireRoles("PCP");
    const task = findOr404(load().tasks, id, "Tarefa não encontrada");
    if (payload.projetoId && !state.projects.some((item) => item.id === Number(payload.projetoId))) fail("Projeto não encontrado");
    applyPatch(task, payload);
    return task;
  }),
  updateTaskStatus: (id, status, motivo = "") => respond(() => {
    const user = requireRoles("PCP", "Fábrica");
    const task = findOr404(load().tasks, id, "Tarefa não encontrada");
    const reason = String(motivo || "").trim();
    if ((status === "paused" || status === "blocked") && !reason) fail("Informe o motivo dessa situação");
    const previous = task.status;
    if (previous === status && (status === "doing" || status === "done")) return task;
    const now = new Date();
    if (previous === "doing" && task.startedAt) {
      task.elapsedSeconds += Math.max(0, Math.floor((now - new Date(task.startedAt)) / 1000));
      task.startedAt = null;
    }
    if (status === "doing") {
      if (previous !== "doing") task.startedAt = now.toISOString();
      task.finishedAt = null;
      task.motivo = "";
    } else {
      task.motivo = reason;
      task.finishedAt = status === "done" || status === "blocked" ? now.toISOString() : null;
    }
    task.status = status;
    task.historico.push({
      id: (state.seq.entry += 1), usuarioId: user.id, statusAnterior: previous, statusNovo: status,
      motivo: reason, createdAt: now.toISOString(),
    });
    // O roteiro da demonstração marca o primeiro passo quando alguém inicia uma tarefa.
    if (status === "doing") window.dispatchEvent(new Event("gimak:demo-iniciou"));
    return task;
  }),
  deleteTask: (id) => respond(() => {
    requireRoles(ADMIN);
    findOr404(load().tasks, id, "Tarefa não encontrada");
    state.tasks = state.tasks.filter((item) => item.id !== Number(id));
    return null;
  }),

  listServices: (situacao = "todos") => respond(() => {
    requireRoles("PCP", "Fábrica");
    let list = load().services;
    if (situacao === "agendados") list = list.filter((item) => item.status === "agendado" || item.status === "em_rota");
    else if (situacao === "concluidos") list = list.filter((item) => item.status === "concluido");
    return sortServices(list).map(serviceWithIssues);
  }),
  createService: (payload) => respond(() => {
    requireRoles("PCP");
    if (payload.dataVolta && payload.dataVolta < payload.data) fail("A data de volta não pode ser antes da ida");
    const service = {
      id: (state.seq.service += 1), tipo: payload.tipo || "Assistência técnica", cliente: cleanText(payload.cliente),
      local: cleanText(payload.local || ""), tecnico: cleanText(payload.tecnico), data: payload.data,
      dataVolta: payload.dataVolta || null, horario: payload.horario || "08:00",
      horarioSaida: payload.horarioSaida || "", horarioRetorno: payload.horarioRetorno || "",
      descricao: cleanText(payload.descricao || ""), status: "agendado", relatorio: "",
      saidaEm: null, saidaPorId: null, concluidoEm: null, concluidoPorId: null,
      createdAt: new Date().toISOString(),
    };
    state.services.push(service);
    return serviceWithIssues(service);
  }),
  updateService: (id, payload) => respond(() => {
    requireRoles("PCP");
    const service = findOr404(load().services, id, "Atendimento não encontrado");
    const next = { ...service };
    applyPatch(next, payload);
    if (next.dataVolta && next.dataVolta < next.data) fail("A data de volta não pode ser antes da ida");
    Object.assign(service, next);
    return serviceWithIssues(service);
  }),
  finishService: (id, relatorio) => respond(() => {
    const user = requireRoles("PCP", "Fábrica");
    const service = findOr404(load().services, id, "Atendimento não encontrado");
    const text = String(relatorio || "").trim();
    if (text.length < 3) fail("Escreva o relatório do atendimento");
    service.relatorio = text;
    service.status = "concluido";
    if (!service.concluidoEm) {
      service.concluidoEm = new Date().toISOString();
      service.concluidoPorId = user.id;
    }
    return serviceWithIssues(service);
  }),
  reopenService: (id) => respond(() => {
    requireRoles("PCP");
    const service = findOr404(load().services, id, "Atendimento não encontrado");
    service.status = service.saidaEm ? "em_rota" : "agendado";
    service.concluidoEm = null;
    service.concluidoPorId = null;
    return serviceWithIssues(service);
  }),
  leaveForService: (id) => respond(() => {
    const user = requireRoles("PCP", "Fábrica");
    const service = findOr404(load().services, id, "Atendimento não encontrado");
    if (service.status === "concluido") fail("Este atendimento já foi concluído");
    if (!service.saidaEm) {
      service.saidaEm = new Date().toISOString();
      service.saidaPorId = user.id;
    }
    service.status = "em_rota";
    return serviceWithIssues(service);
  }),
  deleteService: (id) => respond(() => {
    requireRoles(ADMIN);
    findOr404(load().services, id, "Atendimento não encontrado");
    state.services = state.services.filter((item) => item.id !== Number(id));
    state.issues = state.issues.filter((item) => item.atendimentoId !== Number(id));
    return null;
  }),

  listIssues: (situacao = "abertas") => respond(() => {
    requireRoles("PCP", "Fábrica");
    let list = load().issues;
    if (situacao === "abertas") list = list.filter((item) => item.status === "aberta");
    else if (situacao === "resolvidas") list = list.filter((item) => item.status === "resolvida");
    return [...list]
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt) || b.id - a.id)
      .map((issue) => {
        const service = state.services.find((item) => item.id === issue.atendimentoId);
        return { ...issue, cliente: service.cliente, tecnico: service.tecnico, tipo: service.tipo, dataAtendimento: service.data };
      });
  }),
  createIssue: (serviceId, descricao) => respond(() => {
    const user = requireRoles("PCP", "Fábrica");
    findOr404(load().services, serviceId, "Atendimento não encontrado");
    const text = String(descricao || "").trim();
    if (text.length < 3) fail("Descreva a pendência");
    const issue = {
      id: (state.seq.issue += 1), atendimentoId: Number(serviceId), descricao: text, status: "aberta",
      resolucao: "", criadoPorId: user.id, resolvidoPorId: null, resolvidoEm: null, createdAt: new Date().toISOString(),
    };
    state.issues.push(issue);
    return issue;
  }),
  updateIssue: (id, payload) => respond(() => {
    requireRoles("PCP");
    const issue = findOr404(load().issues, id, "Pendência não encontrada");
    applyPatch(issue, payload, { skipNull: true });
    return issue;
  }),
  resolveIssue: (id, resolucao) => respond(() => {
    const user = requireRoles("PCP", "Fábrica");
    const issue = findOr404(load().issues, id, "Pendência não encontrada");
    issue.resolucao = String(resolucao || "").trim();
    issue.status = "resolvida";
    if (!issue.resolvidoEm) {
      issue.resolvidoEm = new Date().toISOString();
      issue.resolvidoPorId = user.id;
    }
    return issue;
  }),
  reopenIssue: (id) => respond(() => {
    requireRoles("PCP");
    const issue = findOr404(load().issues, id, "Pendência não encontrada");
    issue.status = "aberta";
    issue.resolvidoEm = null;
    issue.resolvidoPorId = null;
    return issue;
  }),
  deleteIssue: (id) => respond(() => {
    requireRoles(ADMIN);
    findOr404(load().issues, id, "Pendência não encontrada");
    state.issues = state.issues.filter((item) => item.id !== Number(id));
    return null;
  }),
};

// Controles da faixa de demonstração, fora da interface do api.js.
export const demoControls = {
  users: () => load().users.filter((item) => item.ativo),
  currentUsername: () => load().session.username,
  switchUser: (username) => {
    load().session = { username, loggedOut: false };
    save();
  },
  reset,
};

"""Read-only production views. Counts describe task records, not worker productivity."""

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
import unicodedata
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.gimak.auth import PERFIL_TV
from app.gimak.models import GimakProjeto, GimakTarefa, GimakUsuario


FACTORY_TZ = ZoneInfo("America/Sao_Paulo")
OPEN_STATUSES = {"todo", "doing", "paused"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).casefold().split())


def percentage(numerator: int, denominator: int) -> float | None:
    return round(100 * numerator / denominator, 1) if denominator else None


def deadline(task: GimakTarefa) -> datetime:
    return datetime.combine(task.dataPlanejada, time.fromisoformat(task.horario), tzinfo=FACTORY_TZ)


def completion_time(task: GimakTarefa) -> datetime | None:
    """Use first entry in the final done run; repeated done clicks do not move it."""
    if task.status != "done":
        return None
    completed = None
    for entry in sorted(task.historico, key=lambda item: (aware(item.createdAt), item.id)):
        if entry.statusNovo != "done":
            completed = None
        elif completed is None:
            completed = aware(entry.createdAt)
    return completed or (aware(task.finishedAt) if task.finishedAt else None)


def recorded_seconds(task: GimakTarefa, now: datetime) -> int:
    seconds = task.elapsedSeconds or 0
    if task.status == "doing" and task.startedAt:
        seconds += max(0, int((now - aware(task.startedAt)).total_seconds()))
    return max(0, seconds)


def is_overdue(task: GimakTarefa, now: datetime) -> bool:
    return task.status in OPEN_STATUSES and deadline(task) < now


def _load_tasks(db: Session) -> list[GimakTarefa]:
    # selectinload batches the history query, independent of the number of users.
    return list(db.scalars(select(GimakTarefa).options(selectinload(GimakTarefa.historico))).all())


def _period(inicio: date | None, fim: date | None, now: datetime):
    today = now.astimezone(FACTORY_TZ).date()
    inicio, fim = inicio or today, fim or today
    if fim < inicio:
        raise HTTPException(status_code=422, detail="A data final deve ser igual ou posterior à inicial")
    if (fim - inicio).days >= 366:
        raise HTTPException(status_code=422, detail="Selecione um período de até 366 dias")
    lower = datetime.combine(inicio, time.min, tzinfo=FACTORY_TZ)
    upper = datetime.combine(fim + timedelta(days=1), time.min, tzinfo=FACTORY_TZ)
    return inicio, fim, lower, upper


def _task_payload(task, now, projects):
    project = projects.get(task.projetoId)
    overdue = is_overdue(task, now)
    return {
        "id": task.id, "titulo": task.titulo, "ordem": task.ordem,
        "responsavel": task.responsavel, "prioridade": task.prioridade, "status": task.status,
        "dataPlanejada": task.dataPlanejada, "horario": task.horario, "prazo": deadline(task),
        "atrasada": overdue, "atrasoSegundos": max(0, int((now - deadline(task)).total_seconds())) if overdue else 0,
        "tempoRegistradoSegundos": recorded_seconds(task, now), "projetoId": task.projetoId,
        "projeto": f"{project.cliente} · {project.equipamento}" if project else None,
        "startedAt": aware(task.startedAt) if task.startedAt else None,
    }


def _project_payloads(projects, tasks, now):
    grouped = defaultdict(list)
    for task in tasks:
        grouped[task.projetoId].append(task)
    result = []
    for project in projects.values():
        # Projeto concluído ou desativado sai dos painéis de produção.
        if not project.ativo or project.concluidoEm is not None:
            continue
        project_tasks = grouped[project.id]
        completed = sum(t.status == "done" for t in project_tasks)
        result.append({
            "id": project.id, "cliente": project.cliente, "equipamento": project.equipamento,
            "total": len(project_tasks), "concluidas": completed,
            "emExecucao": sum(t.status == "doing" for t in project_tasks),
            "atrasadas": sum(is_overdue(t, now) for t in project_tasks),
            "percentualConclusao": percentage(completed, len(project_tasks)),
        })
    return sorted(result, key=lambda p: (-p["emExecucao"], -p["atrasadas"], -p["id"]))


def _daily_series(tasks, completions, inicio, fim):
    planned = Counter(t.dataPlanejada for t in tasks)
    completed = Counter(value.astimezone(FACTORY_TZ).date() for value in completions.values() if value)
    return [{"data": day, "planejadas": planned[day], "concluidas": completed[day]}
            for offset in range((fim - inicio).days + 1)
            for day in [inicio + timedelta(days=offset)]]


def build_indicators(db: Session, inicio: date | None = None, fim: date | None = None):
    now = utc_now()
    inicio, fim, lower, upper = _period(inicio, fim, now)
    tasks = _load_tasks(db)
    users = list(db.scalars(select(GimakUsuario)).all())
    projects = {p.id: p for p in db.scalars(select(GimakProjeto)).all()}
    completions = {t.id: completion_time(t) for t in tasks}
    cohort = [t for t in tasks if inicio <= t.dataPlanejada <= fim]
    overdue = sorted((t for t in tasks if is_overdue(t, now)), key=lambda t: (deadline(t), t.id))
    completed = [t for t in cohort if t.status == "done"]
    known_completions = [t for t in completed if completions[t.id]]
    on_time = sum(completions[t.id] <= deadline(t) for t in known_completions)
    statuses = Counter(t.status for t in cohort)

    by_name = defaultdict(list)
    for user in users:
        # A display-only account is not an eligible task assignee.
        if user.perfil != PERFIL_TV:
            by_name[normalize_name(user.nome)].append(user)
    assignments = {}
    groups = defaultdict(list)
    for task in tasks:
        key = normalize_name(task.responsavel)
        matches = by_name[key]
        assignments[task.id] = matches[0].id if len(matches) == 1 else None
        if inicio <= task.dataPlanejada <= fim:
            groups[key].append(task)

    ranking = []
    for key, group in groups.items():
        matches = by_name[key]
        linked = matches[0] if len(matches) == 1 else None
        finished = [t for t in group if t.status == "done"]
        known = [t for t in finished if completions[t.id]]
        in_time = sum(completions[t.id] <= deadline(t) for t in known)
        ranking.append({
            "usuarioId": linked.id if linked else None,
            "nome": linked.nome if linked else group[0].responsavel,
            "vinculo": "unico" if linked else "ambiguo" if matches else "sem_usuario",
            "planejadas": len(group), "concluidas": len(finished),
            "naoRealizadas": sum(t.status == "blocked" for t in group),
            "atrasadas": sum(is_overdue(t, now) for t in group),
            "noPrazo": in_time, "concluidasComPrazoConhecido": len(known),
            "taxaConclusao": percentage(len(finished), len(group)),
            "taxaNoPrazo": percentage(in_time, len(known)),
            "tempoRegistradoSegundos": sum(recorded_seconds(t, now) for t in group),
        })
    ranking.sort(key=lambda row: (-row["concluidas"], normalize_name(row["nome"])))

    # Actor IDs measure who used the app; task responsibility is a separate dimension.
    events_by_user = defaultdict(list)
    for task in tasks:
        for entry in task.historico:
            if lower <= aware(entry.createdAt) < upper and aware(entry.createdAt) <= now:
                events_by_user[entry.usuarioId].append(entry)
    assigned_by_user = defaultdict(set)
    for task in cohort:
        if assignments[task.id] is not None:
            assigned_by_user[assignments[task.id]].add(task.id)
    adoption = []
    for user in sorted(users, key=lambda u: normalize_name(u.nome)):
        if user.perfil == PERFIL_TV:
            continue
        events = events_by_user[user.id]
        touched = {e.tarefaId for e in events}
        own_tasks = assigned_by_user[user.id]
        adoption.append({
            "usuarioId": user.id, "nome": user.nome, "username": user.username,
            "perfil": user.perfil, "ativo": user.ativo, "apontamentos": len(events),
            "tarefasMovimentadas": len(touched),
            "diasAtivos": len({aware(e.createdAt).astimezone(FACTORY_TZ).date() for e in events}),
            "ultimoApontamento": max((aware(e.createdAt) for e in events), default=None),
            "tarefasAtribuidas": len(own_tasks), "tarefasPropriasApontadas": len(touched & own_tasks),
            "taxaApontamentoProprio": percentage(len(touched & own_tasks), len(own_tasks)),
        })
    pause_reasons = Counter(t.motivo.strip() or "Sem justificativa registrada" for t in tasks if t.status == "paused")
    return {
        "geradoEm": now, "fusoHorario": str(FACTORY_TZ), "periodo": {"inicio": inicio, "fim": fim},
        "criterios": {
            "coorte": "Resumo e ranking consideram tarefas com data planejada no período, no estado atual. Atrasos em aberto incluem todo o histórico.",
            "prazo": "Prazo = data planejada + horário cadastrado, no fuso America/Sao_Paulo. Tarefas não realizadas são contadas à parte dos atrasos em aberto.",
            "ranking": "Ordenado por tarefas concluídas atribuídas ao responsável. Quantidade e tempo registrados não medem qualidade, esforço ou produtividade individual. Vínculo de nome só é feito quando corresponde a um único usuário.",
            "adesao": "Apontamentos são mudanças de status feitas pelo usuário no período. Apontamento próprio é a proporção de tarefas atribuídas no período em que ele registrou uma mudança. Não mede presença nem login; contas compartilhadas não identificam pessoas.",
            "tempo": "Tempo registrado acumulado nas tarefas planejadas no período, incluindo execução em andamento. Pode incluir trabalho realizado fora do período; não representa jornada.",
            "serieDiaria": "Planejadas por data de planejamento; concluídas por data da conclusão final das tarefas atualmente concluídas, independentemente do planejamento. Reaberturas deixam de contar como concluídas.",
        },
        "resumo": {
            "planejadas": len(cohort), "concluidas": len(completed), "aFazer": statuses["todo"],
            "emExecucao": statuses["doing"], "pausadas": statuses["paused"], "naoRealizadas": statuses["blocked"],
            "atrasadasNoPeriodo": sum(is_overdue(t, now) for t in cohort), "atrasadasEmAberto": len(overdue),
            "concluidasNoPrazo": on_time, "concluidasComPrazoConhecido": len(known_completions),
            "taxaConclusao": percentage(len(completed), len(cohort)),
            "taxaNoPrazo": percentage(on_time, len(known_completions)),
            "tempoRegistradoSegundos": sum(recorded_seconds(t, now) for t in cohort),
        },
        "ranking": ranking, "adesao": adoption,
        "serieDiaria": _daily_series(tasks, completions, inicio, fim),
        "atrasadas": [_task_payload(t, now, projects) for t in overdue],
        "motivosPausa": [{"motivo": reason, "quantidade": count} for reason, count in pause_reasons.most_common()],
        "projetos": _project_payloads(projects, tasks, now),
    }


def build_tv_panel(db: Session):
    now = utc_now()
    today = now.astimezone(FACTORY_TZ).date()
    tasks = _load_tasks(db)
    projects = {p.id: p for p in db.scalars(select(GimakProjeto)).all()}
    completions = {t.id: completion_time(t) for t in tasks}
    today_tasks = [t for t in tasks if t.dataPlanejada == today]
    doing = sorted((t for t in tasks if t.status == "doing"), key=lambda t: (deadline(t), t.id))
    paused = sorted((t for t in tasks if t.status == "paused"), key=lambda t: (deadline(t), t.id))
    overdue = sorted((t for t in tasks if is_overdue(t, now)), key=lambda t: (deadline(t), t.id))
    events = [(entry, task) for task in tasks for entry in task.historico
              if entry.statusNovo in {"doing", "done"} and entry.statusAnterior != entry.statusNovo
              and aware(entry.createdAt) <= now]
    events.sort(key=lambda pair: (aware(pair[0].createdAt), pair[0].id), reverse=True)
    completed_today = sum(value is not None and value.astimezone(FACTORY_TZ).date() == today for value in completions.values())
    today_planned_completed = sum(t.status == "done" for t in today_tasks)
    return {
        "geradoEm": now, "fusoHorario": str(FACTORY_TZ), "hoje": today,
        "resumo": {
            "planejadasHoje": len(today_tasks), "concluidasHojePlanejadas": today_planned_completed,
            "taxaConclusaoHoje": percentage(today_planned_completed, len(today_tasks)),
            "emExecucao": len(doing), "pausadas": len(paused), "atrasadasEmAberto": len(overdue),
            "concluidasHoje": completed_today,
        },
        "emExecucao": [_task_payload(t, now, projects) for t in doing],
        "pausadas": [_task_payload(t, now, projects) for t in paused],
        "atrasadas": [_task_payload(t, now, projects) for t in overdue],
        "serieDiaria": _daily_series(tasks, completions, today - timedelta(days=6), today),
        "projetos": _project_payloads(projects, tasks, now),
        "ultimosEventos": [{"id": entry.id, "tarefaId": task.id, "titulo": task.titulo,
                            "responsavel": task.responsavel, "status": entry.statusNovo,
                            "ocorridoEm": aware(entry.createdAt)} for entry, task in events[:12]],
    }

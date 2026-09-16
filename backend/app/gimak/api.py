from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.gimak.analytics import build_indicators, build_tv_panel
from app.gimak.auth import PERFIL_ADMIN, PERFIL_FABRICA, PERFIL_PCP, PERFIL_TV
from app.gimak.db import get_gimak_db
from app.gimak.deps import get_gimak_current_user, require_gimak_roles
from app.gimak.models import (
    GimakApontamento,
    GimakAtendimento,
    GimakPendencia,
    GimakProjeto,
    GimakTarefa,
    GimakUsuario,
)
from app.gimak.schemas import (
    AtendimentoConclusao,
    AtendimentoCreate,
    AtendimentoRead,
    AtendimentoUpdate,
    GimakSituacaoAtendimento,
    GimakSituacaoPendencia,
    GimakSituacaoProjeto,
    LoginRequest,
    LoginResponse,
    PendenciaComAtendimento,
    PendenciaCreate,
    PendenciaRead,
    PendenciaResolucao,
    PendenciaUpdate,
    ProjetoCreate,
    ProjetoRead,
    ProjetoUpdate,
    SenhaUpdate,
    StatusUpdate,
    TarefaCreate,
    TarefaRead,
    TarefaUpdate,
    UsuarioCreate,
    UsuarioRead,
    UsuarioUpdate,
)
from app.services.auth import criar_token, hash_senha, verificar_senha


router = APIRouter(prefix="/gimak", tags=["gimak"])


def _get_task(db: Session, task_id: int) -> GimakTarefa:
    task = db.scalar(
        select(GimakTarefa).options(selectinload(GimakTarefa.historico)).where(GimakTarefa.id == task_id)
    )
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return task


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@router.get("/health")
def health(db: Session = Depends(get_gimak_db)):
    db.execute(select(1))
    return {"status": "ok", "database": "gimak_pcp"}


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_gimak_db)):
    username = payload.username.strip().lower()
    user = db.scalar(select(GimakUsuario).where(func.lower(GimakUsuario.username) == username))
    if not user or not user.ativo or not verificar_senha(payload.senha, user.senhaHash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")
    settings = get_settings()
    return LoginResponse(
        accessToken=criar_token(
            user, settings.gimak_auth_secret,
            30 * 24 * 60 if user.perfil == PERFIL_TV else settings.gimak_auth_token_minutes,
        ),
        usuario=user,
    )


@router.get("/auth/me", response_model=UsuarioRead)
def me(user: GimakUsuario = Depends(get_gimak_current_user)):
    return user


@router.get("/indicadores")
def indicators(
    inicio: date | None = None,
    fim: date | None = None,
    db: Session = Depends(get_gimak_db),
    _admin: GimakUsuario = Depends(require_gimak_roles(PERFIL_ADMIN)),
):
    return build_indicators(db, inicio, fim)


@router.get("/painel-tv")
def tv_panel(
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(get_gimak_current_user),
):
    return build_tv_panel(db)


@router.get("/usuarios", response_model=list[UsuarioRead])
def list_users(
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    return db.scalars(select(GimakUsuario).order_by(GimakUsuario.nome)).all()


@router.post("/usuarios", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UsuarioCreate,
    db: Session = Depends(get_gimak_db),
    _admin: GimakUsuario = Depends(require_gimak_roles(PERFIL_ADMIN)),
):
    username = payload.username.strip().lower()
    if db.scalar(select(GimakUsuario).where(func.lower(GimakUsuario.username) == username)):
        raise HTTPException(status_code=409, detail="Nome de usuário já está em uso")
    user = GimakUsuario(
        nome=payload.nome.strip(),
        username=username,
        senhaHash=hash_senha(payload.senha),
        perfil=payload.perfil,
        cargo=payload.cargo,
        ativo=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Nome de usuário já está em uso") from exc
    db.refresh(user)
    return user


def _rename_responsible(db: Session, antigo: str, novo: str, user_id: int) -> None:
    """Tarefa e atendimento guardam o nome, não o id. Corrigir o nome sem levar o
    histórico junto deixaria os apontamentos antigos orfãos e fora do ranking.

    Se outro usuário tiver o mesmo nome, não dá para saber de quem é cada registro,
    então o histórico fica como está.
    """
    homonimo = db.scalar(
        select(GimakUsuario).where(
            func.lower(GimakUsuario.nome) == antigo.lower(), GimakUsuario.id != user_id
        )
    )
    if homonimo:
        return
    for modelo, campo in ((GimakTarefa, GimakTarefa.responsavel), (GimakAtendimento, GimakAtendimento.tecnico)):
        for registro in db.scalars(select(modelo).where(campo == antigo)).all():
            setattr(registro, campo.key, novo)

@router.patch("/usuarios/{user_id}", response_model=UsuarioRead)
def update_user(
    user_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_gimak_db),
    admin: GimakUsuario = Depends(require_gimak_roles(PERFIL_ADMIN)),
):
    user = db.get(GimakUsuario, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    data = payload.model_dump(exclude_unset=True)
    if user.id == admin.id and (data.get("ativo") is False or data.get("perfil", PERFIL_ADMIN) != PERFIL_ADMIN):
        raise HTTPException(status_code=400, detail="O administrador não pode remover o próprio acesso")
    nome_antigo = user.nome
    for key, value in data.items():
        if value is not None:
            setattr(user, key, value.strip() if isinstance(value, str) else value)
    if user.nome != nome_antigo:
        _rename_responsible(db, nome_antigo, user.nome, user.id)
    db.commit()
    db.refresh(user)
    return user


@router.post("/usuarios/{user_id}/senha", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: int,
    payload: SenhaUpdate,
    db: Session = Depends(get_gimak_db),
    _admin: GimakUsuario = Depends(require_gimak_roles(PERFIL_ADMIN)),
):
    user = db.get(GimakUsuario, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user.senhaHash = hash_senha(payload.senha)
    db.commit()


@router.get("/projetos", response_model=list[ProjetoRead])
def list_projects(
    situacao: GimakSituacaoProjeto = "andamento",
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    """Projeto concluído sai da lista padrão e só aparece quando é pedido pelo filtro."""
    statement = select(GimakProjeto).where(GimakProjeto.ativo.is_(True)).order_by(GimakProjeto.id.desc())
    if situacao == "andamento":
        statement = statement.where(GimakProjeto.concluidoEm.is_(None))
    elif situacao == "concluidos":
        statement = statement.where(GimakProjeto.concluidoEm.is_not(None))
    return db.scalars(statement).all()


@router.post("/projetos", response_model=ProjetoRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjetoCreate,
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP)),
):
    project = GimakProjeto(cliente=payload.cliente.strip(), equipamento=payload.equipamento.strip())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/projetos/{project_id}", response_model=ProjetoRead)
def update_project(
    project_id: int,
    payload: ProjetoUpdate,
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP)),
):
    project = db.get(GimakProjeto, project_id)
    if not project or not project.ativo:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    data = payload.model_dump(exclude_unset=True)
    concluido = data.pop("concluido", None)
    for key, value in data.items():
        setattr(project, key, value.strip() if isinstance(value, str) else value)
    if concluido is True and project.concluidoEm is None:
        project.concluidoEm = datetime.now(timezone.utc)
    elif concluido is False:
        project.concluidoEm = None
    db.commit()
    db.refresh(project)
    return project


@router.get("/tarefas", response_model=list[TarefaRead])
def list_tasks(
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    statement = select(GimakTarefa).options(selectinload(GimakTarefa.historico)).order_by(
        GimakTarefa.dataPlanejada.desc(), GimakTarefa.horario, GimakTarefa.id.desc()
    )
    return db.scalars(statement).all()


@router.post("/tarefas", response_model=TarefaRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TarefaCreate,
    db: Session = Depends(get_gimak_db),
    user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP)),
):
    if payload.projetoId and not db.get(GimakProjeto, payload.projetoId):
        raise HTTPException(status_code=422, detail="Projeto não encontrado")
    task = GimakTarefa(**payload.model_dump(), createdById=user.id)
    db.add(task)
    db.commit()
    return _get_task(db, task.id)


@router.patch("/tarefas/{task_id}", response_model=TarefaRead)
def update_task(
    task_id: int,
    payload: TarefaUpdate,
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP)),
):
    task = _get_task(db, task_id)
    data = payload.model_dump(exclude_unset=True)
    project_id = data.get("projetoId")
    if project_id and not db.get(GimakProjeto, project_id):
        raise HTTPException(status_code=422, detail="Projeto não encontrado")
    for key, value in data.items():
        setattr(task, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    return _get_task(db, task.id)


@router.patch("/tarefas/{task_id}/status", response_model=TarefaRead)
def update_task_status(
    task_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_gimak_db),
    user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    task = _get_task(db, task_id)
    reason = payload.motivo.strip()
    if payload.status in {"paused", "blocked"} and not reason:
        raise HTTPException(status_code=422, detail="Informe o motivo dessa situação")

    previous = task.status
    # Repetir "iniciar" ou "concluir" não traz informação nova e mexeria no cronômetro
    # e na data de conclusão. Já "não realizada" pode ser reenviada para corrigir o motivo.
    if previous == payload.status and payload.status in {"doing", "done"}:
        return task
    now = datetime.now(timezone.utc)
    if previous == "doing" and task.startedAt:
        task.elapsedSeconds += max(0, int((now - _aware(task.startedAt)).total_seconds()))
        task.startedAt = None

    if payload.status == "doing":
        if previous != "doing":
            task.startedAt = now
        task.finishedAt = None
        task.motivo = ""
    else:
        task.motivo = reason
        task.finishedAt = now if payload.status in {"done", "blocked"} else None

    task.status = payload.status
    db.add(
        GimakApontamento(
            tarefaId=task.id,
            usuarioId=user.id,
            statusAnterior=previous,
            statusNovo=payload.status,
            motivo=reason,
        )
    )
    db.commit()
    return _get_task(db, task.id)


@router.delete("/tarefas/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_gimak_db),
    _admin: GimakUsuario = Depends(require_gimak_roles(PERFIL_ADMIN)),
):
    """Exclusão definitiva, só do administrador. Leva junto o histórico de apontamentos."""
    task = _get_task(db, task_id)
    db.delete(task)
    db.commit()


def _get_service(db: Session, service_id: int) -> GimakAtendimento:
    service = db.scalar(
        select(GimakAtendimento)
        .options(selectinload(GimakAtendimento.pendencias))
        .where(GimakAtendimento.id == service_id)
    )
    if not service:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    return service


@router.get("/atendimentos", response_model=list[AtendimentoRead])
def list_services(
    situacao: GimakSituacaoAtendimento = "todos",
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    statement = select(GimakAtendimento).options(selectinload(GimakAtendimento.pendencias)).order_by(
        GimakAtendimento.data.desc(), GimakAtendimento.horario, GimakAtendimento.id.desc()
    )
    if situacao == "agendados":
        # "Em rota" ainda é um atendimento em aberto: ele continua na lista de agendados.
        statement = statement.where(GimakAtendimento.status.in_(("agendado", "em_rota")))
    elif situacao == "concluidos":
        statement = statement.where(GimakAtendimento.status == "concluido")
    return db.scalars(statement).all()


@router.post("/atendimentos", response_model=AtendimentoRead, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: AtendimentoCreate,
    db: Session = Depends(get_gimak_db),
    user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP)),
):
    service = GimakAtendimento(**payload.model_dump(), createdById=user.id)
    db.add(service)
    db.commit()
    return _get_service(db, service.id)


@router.patch("/atendimentos/{service_id}", response_model=AtendimentoRead)
def update_service(
    service_id: int,
    payload: AtendimentoUpdate,
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP)),
):
    service = _get_service(db, service_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    return _get_service(db, service.id)


@router.post("/atendimentos/{service_id}/concluir", response_model=AtendimentoRead)
def finish_service(
    service_id: int,
    payload: AtendimentoConclusao,
    db: Session = Depends(get_gimak_db),
    user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    """Quem voltou do cliente marca como concluído e escreve o relatório.

    Reenviar corrige o relatório sem mexer na data da primeira conclusão.
    """
    service = _get_service(db, service_id)
    service.relatorio = payload.relatorio
    service.status = "concluido"
    if service.concluidoEm is None:
        service.concluidoEm = datetime.now(timezone.utc)
        service.concluidoPorId = user.id
    db.commit()
    return _get_service(db, service.id)


@router.post("/atendimentos/{service_id}/reabrir", response_model=AtendimentoRead)
def reopen_service(
    service_id: int,
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP)),
):
    service = _get_service(db, service_id)
    service.status = "em_rota" if service.saidaEm else "agendado"
    service.concluidoEm = None
    service.concluidoPorId = None
    db.commit()
    return _get_service(db, service.id)


@router.delete("/atendimentos/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    db: Session = Depends(get_gimak_db),
    _admin: GimakUsuario = Depends(require_gimak_roles(PERFIL_ADMIN)),
):
    db.delete(_get_service(db, service_id))
    db.commit()

@router.post("/atendimentos/{service_id}/sair", response_model=AtendimentoRead)
def leave_for_service(
    service_id: int,
    db: Session = Depends(get_gimak_db),
    user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    """O técnico marca que está saindo da empresa. Reenviar não move a hora registrada."""
    service = _get_service(db, service_id)
    if service.status == "concluido":
        raise HTTPException(status_code=422, detail="Este atendimento já foi concluído")
    if service.saidaEm is None:
        service.saidaEm = datetime.now(timezone.utc)
        service.saidaPorId = user.id
    service.status = "em_rota"
    db.commit()
    return _get_service(db, service.id)


def _get_issue(db: Session, issue_id: int) -> GimakPendencia:
    issue = db.get(GimakPendencia, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Pendência não encontrada")
    return issue


@router.get("/pendencias", response_model=list[PendenciaComAtendimento])
def list_issues(
    situacao: GimakSituacaoPendencia = "abertas",
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    statement = (
        select(GimakPendencia, GimakAtendimento)
        .join(GimakAtendimento, GimakAtendimento.id == GimakPendencia.atendimentoId)
        .order_by(GimakPendencia.createdAt.desc(), GimakPendencia.id.desc())
    )
    if situacao != "todas":
        statement = statement.where(
            GimakPendencia.status == {"abertas": "aberta", "resolvidas": "resolvida"}[situacao]
        )
    return [
        PendenciaComAtendimento(
            **PendenciaRead.model_validate(issue).model_dump(),
            cliente=service.cliente,
            tecnico=service.tecnico,
            tipo=service.tipo,
            dataAtendimento=service.data,
        )
        for issue, service in db.execute(statement).all()
    ]


@router.post(
    "/atendimentos/{service_id}/pendencias",
    response_model=PendenciaRead,
    status_code=status.HTTP_201_CREATED,
)
def create_issue(
    service_id: int,
    payload: PendenciaCreate,
    db: Session = Depends(get_gimak_db),
    user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    """Quem voltou registra o que ficou faltando, para não morrer no relatório."""
    _get_service(db, service_id)
    issue = GimakPendencia(atendimentoId=service_id, descricao=payload.descricao, criadoPorId=user.id)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


@router.patch("/pendencias/{issue_id}", response_model=PendenciaRead)
def update_issue(
    issue_id: int,
    payload: PendenciaUpdate,
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP)),
):
    issue = _get_issue(db, issue_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(issue, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(issue)
    return issue


@router.post("/pendencias/{issue_id}/resolver", response_model=PendenciaRead)
def resolve_issue(
    issue_id: int,
    payload: PendenciaResolucao,
    db: Session = Depends(get_gimak_db),
    user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP, PERFIL_FABRICA)),
):
    issue = _get_issue(db, issue_id)
    issue.resolucao = payload.resolucao.strip()
    issue.status = "resolvida"
    if issue.resolvidoEm is None:
        issue.resolvidoEm = datetime.now(timezone.utc)
        issue.resolvidoPorId = user.id
    db.commit()
    db.refresh(issue)
    return issue


@router.post("/pendencias/{issue_id}/reabrir", response_model=PendenciaRead)
def reopen_issue(
    issue_id: int,
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(require_gimak_roles(PERFIL_PCP)),
):
    issue = _get_issue(db, issue_id)
    issue.status = "aberta"
    issue.resolvidoEm = None
    issue.resolvidoPorId = None
    db.commit()
    db.refresh(issue)
    return issue


@router.delete("/pendencias/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_gimak_db),
    _admin: GimakUsuario = Depends(require_gimak_roles(PERFIL_ADMIN)),
):
    db.delete(_get_issue(db, issue_id))
    db.commit()

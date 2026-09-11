from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.gimak.auth import PERFIL_ADMIN, PERFIL_FABRICA, PERFIL_PCP
from app.gimak.db import get_gimak_db
from app.gimak.deps import get_gimak_current_user, require_gimak_roles
from app.gimak.models import GimakApontamento, GimakProjeto, GimakTarefa, GimakUsuario
from app.gimak.schemas import (
    LoginRequest,
    LoginResponse,
    ProjetoCreate,
    ProjetoRead,
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
        accessToken=criar_token(user, settings.gimak_auth_secret, settings.gimak_auth_token_minutes),
        usuario=user,
    )


@router.get("/auth/me", response_model=UsuarioRead)
def me(user: GimakUsuario = Depends(get_gimak_current_user)):
    return user


@router.get("/usuarios", response_model=list[UsuarioRead])
def list_users(
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(get_gimak_current_user),
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
    for key, value in data.items():
        if value is not None:
            setattr(user, key, value.strip() if isinstance(value, str) else value)
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
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(get_gimak_current_user),
):
    return db.scalars(select(GimakProjeto).where(GimakProjeto.ativo.is_(True)).order_by(GimakProjeto.id.desc())).all()


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


@router.get("/tarefas", response_model=list[TarefaRead])
def list_tasks(
    db: Session = Depends(get_gimak_db),
    _user: GimakUsuario = Depends(get_gimak_current_user),
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
    if previous == "doing" and payload.status == "doing":
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

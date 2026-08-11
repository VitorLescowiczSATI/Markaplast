from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_profiles
from app.core.config import get_settings
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, LoginResponse, UsuarioCreate, UsuarioRead, UsuarioSenhaUpdate, UsuarioUpdate
from app.services.auth import PERFIL_ADMIN, criar_token, hash_senha, verificar_senha


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    usuario = db.scalar(select(Usuario).where(func.lower(Usuario.username) == username))
    if not usuario or not usuario.ativo or not verificar_senha(payload.senha, usuario.senhaHash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")
    settings = get_settings()
    return LoginResponse(
        accessToken=criar_token(usuario, settings.auth_secret, settings.auth_token_minutes),
        usuario=usuario,
    )


@router.get("/me", response_model=UsuarioRead)
def me(usuario: Usuario = Depends(get_current_user)):
    return usuario


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_usuario: Usuario = Depends(get_current_user)):
    return None


@router.get("/usuarios", response_model=list[UsuarioRead])
def listar_usuarios(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_profiles(PERFIL_ADMIN)),
):
    return db.scalars(select(Usuario).order_by(Usuario.nome, Usuario.username)).all()


@router.post("/usuarios", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_profiles(PERFIL_ADMIN)),
):
    username = payload.username.strip().lower()
    existente = db.scalar(select(Usuario).where(func.lower(Usuario.username) == username))
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome de usuário já está em uso")
    usuario = Usuario(
        nome=payload.nome.strip(),
        username=username,
        senhaHash=hash_senha(payload.senha),
        perfil=payload.perfil,
        ativo=True,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome de usuário já está em uso") from exc
    db.refresh(usuario)
    return usuario


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioRead)
def atualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    administrador: Usuario = Depends(require_profiles(PERFIL_ADMIN)),
):
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    dados = {campo: valor for campo, valor in payload.model_dump(exclude_unset=True).items() if valor is not None}
    if usuario.id == administrador.id and (dados.get("ativo") is False or dados.get("perfil", PERFIL_ADMIN) != PERFIL_ADMIN):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O administrador não pode remover o próprio acesso")
    for campo, valor in dados.items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/usuarios/{usuario_id}/senha", status_code=status.HTTP_204_NO_CONTENT)
def redefinir_senha(
    usuario_id: int,
    payload: UsuarioSenhaUpdate,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_profiles(PERFIL_ADMIN)),
):
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    usuario.senhaHash = hash_senha(payload.senha)
    db.commit()
    return None

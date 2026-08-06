from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, LoginResponse, UsuarioRead
from app.services.auth import criar_token, verificar_senha


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

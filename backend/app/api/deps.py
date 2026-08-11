from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.usuario import Usuario
from app.services.auth import PERFIL_ADMIN, ler_token


bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    erro = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão inválida ou expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials or credentials.scheme.lower() != "bearer":
        raise erro
    try:
        usuario_id = ler_token(credentials.credentials, get_settings().auth_secret)
    except ValueError as exc:
        raise erro from exc
    usuario = db.get(Usuario, usuario_id)
    if not usuario or not usuario.ativo:
        raise erro
    return usuario


def require_profiles(*perfis: str):
    def verificar(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.perfil != PERFIL_ADMIN and usuario.perfil not in perfis:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seu perfil não pode acessar este recurso")
        return usuario

    return verificar

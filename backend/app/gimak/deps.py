from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.gimak.auth import PERFIL_ADMIN
from app.gimak.db import get_gimak_db
from app.gimak.models import GimakUsuario
from app.services.auth import ler_token


gimak_bearer = HTTPBearer(auto_error=False)


def get_gimak_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(gimak_bearer),
    db: Session = Depends(get_gimak_db),
) -> GimakUsuario:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão Gimak inválida ou expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials or credentials.scheme.lower() != "bearer":
        raise error
    try:
        user_id = ler_token(credentials.credentials, get_settings().gimak_auth_secret)
    except ValueError as exc:
        raise error from exc
    user = db.get(GimakUsuario, user_id)
    if not user or not user.ativo:
        raise error
    return user


def require_gimak_roles(*roles: str):
    def verify(user: GimakUsuario = Depends(get_gimak_current_user)) -> GimakUsuario:
        if user.perfil != PERFIL_ADMIN and user.perfil not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seu perfil não pode acessar este recurso")
        return user

    return verify

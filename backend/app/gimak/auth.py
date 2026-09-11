import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.gimak.models import GimakUsuario
from app.services.auth import hash_senha


logger = logging.getLogger(__name__)

PERFIL_ADMIN = "Administrador"
PERFIL_PCP = "PCP"
PERFIL_FABRICA = "Fábrica"


def seed_gimak_admin(db: Session, initial_password: str) -> None:
    admin = db.scalar(select(GimakUsuario).where(func.lower(GimakUsuario.username) == "admin"))
    if admin:
        return
    if not initial_password:
        logger.warning("GIMAK_INITIAL_ADMIN_PASSWORD não configurada; administrador Gimak não foi criado")
        return
    db.add(
        GimakUsuario(
            nome="Administrador Gimak",
            username="admin",
            senhaHash=hash_senha(initial_password),
            perfil=PERFIL_ADMIN,
            ativo=True,
        )
    )
    db.commit()

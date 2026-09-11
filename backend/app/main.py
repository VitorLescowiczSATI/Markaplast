import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import auth, cargas, clientes, dashboard, fiscal, historico, integracoes, metas, pedidos, precos, produtos
from app.core.config import get_settings
from app.db.migrations import ensure_runtime_migrations
from app.db.session import Base, SessionLocal, engine
from app import models  # noqa: F401
from app.services.seed import seed_produtos
from app.services.auth import seed_usuarios
from app.gimak.api import router as gimak_router
from app.gimak.auth import seed_gimak_admin
from app.gimak.db import GimakSessionLocal, initialize_gimak_database
from app.gimak import models as gimak_models  # noqa: F401


settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    if settings.environment == "production" and settings.auth_secret == "development-only-change-me":
        raise RuntimeError("AUTH_SECRET precisa ser configurada em produção")
    Base.metadata.create_all(bind=engine)
    ensure_runtime_migrations(engine)
    db = SessionLocal()
    try:
        seed_produtos(db)
        seed_usuarios(db, settings.auth_initial_password)
    finally:
        db.close()
    try:
        if settings.environment == "production" and settings.gimak_auth_secret == "gimak-development-only-change-me":
            raise RuntimeError("GIMAK_AUTH_SECRET precisa ser configurada em produção")
        initialize_gimak_database()
        with GimakSessionLocal() as gimak_db:
            seed_gimak_admin(gimak_db, settings.gimak_initial_admin_password)
    except Exception:
        # A Gimak compartilha o processo, mas uma falha no segundo banco não deve
        # impedir a Markaplast de iniciar.
        logger.exception("Não foi possível inicializar o banco lógico da Gimak")


@app.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database_unavailable") from exc
    return {"status": "ok", "environment": settings.environment, "database": "ok"}


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "ok",
        "health": "/health",
        "docs": "/docs",
    }


app.include_router(auth.router, prefix="/api")
app.include_router(pedidos.router, prefix="/api")
app.include_router(cargas.router, prefix="/api")
app.include_router(clientes.router, prefix="/api")
app.include_router(produtos.router, prefix="/api")
app.include_router(precos.router, prefix="/api")
app.include_router(metas.router, prefix="/api")
app.include_router(integracoes.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(fiscal.router, prefix="/api")
app.include_router(historico.router, prefix="/api")
app.include_router(gimak_router, prefix="/api")

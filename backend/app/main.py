from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cargas, clientes, dashboard, fiscal, historico, integracoes, pedidos, produtos
from app.core.config import get_settings
from app.db.migrations import ensure_runtime_migrations
from app.db.session import Base, SessionLocal, engine
from app import models  # noqa: F401
from app.services.seed import seed_produtos


settings = get_settings()

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
    Base.metadata.create_all(bind=engine)
    ensure_runtime_migrations(engine)
    db = SessionLocal()
    try:
        seed_produtos(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "ok",
        "health": "/health",
        "docs": "/docs",
    }


app.include_router(pedidos.router, prefix="/api")
app.include_router(cargas.router, prefix="/api")
app.include_router(clientes.router, prefix="/api")
app.include_router(produtos.router, prefix="/api")
app.include_router(integracoes.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(fiscal.router, prefix="/api")
app.include_router(historico.router, prefix="/api")

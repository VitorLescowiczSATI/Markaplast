import re

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings
from app.db.session import engine as primary_engine
from app.db.session import normalize_database_url


class GimakBase(DeclarativeBase):
    pass


def build_gimak_database_url(primary_url: str, explicit_url: str = "", database_name: str = "gimak_pcp") -> str:
    if explicit_url:
        return normalize_database_url(explicit_url)
    normalized_primary = normalize_database_url(primary_url)
    if normalized_primary.startswith("sqlite"):
        return "sqlite:///./gimak_dev.db"
    return make_url(normalized_primary).set(database=database_name).render_as_string(hide_password=False)


settings = get_settings()
gimak_database_url = build_gimak_database_url(
    settings.database_url,
    settings.gimak_database_url,
    settings.gimak_database_name,
)
connect_args = {"check_same_thread": False} if gimak_database_url.startswith("sqlite") else {}

gimak_engine = create_engine(
    gimak_database_url,
    pool_pre_ping=True,
    pool_size=2 if not gimak_database_url.startswith("sqlite") else 5,
    max_overflow=3 if not gimak_database_url.startswith("sqlite") else 10,
    connect_args=connect_args,
)
GimakSessionLocal = sessionmaker(bind=gimak_engine, autoflush=False, autocommit=False)


def ensure_gimak_database_exists() -> None:
    """Cria o segundo banco lógico na instância atual quando não há URL explícita."""
    if settings.gimak_database_url or primary_engine.dialect.name != "postgresql":
        return
    database_name = settings.gimak_database_name
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,62}", database_name):
        raise RuntimeError("GIMAK_DATABASE_NAME inválido")
    with primary_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        exists = connection.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database_name})
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))


# create_all cria tabela nova, mas nunca altera tabela que já existe. Colunas
# acrescentadas depois do primeiro deploy entram por aqui, como o
# ensure_runtime_migrations faz no banco da Markaplast.
# O tipo muda por dialeto de propósito: em Postgres a coluna precisa guardar o
# fuso, senão a data volta ingênua e a tela mostra a hora errada.
COLUNAS_ACRESCENTADAS = (
    ("projetos", "concluido_em", "TIMESTAMP WITH TIME ZONE", "TIMESTAMP"),
    ("usuarios", "cargo", "VARCHAR(80) NOT NULL DEFAULT ''", "VARCHAR(80) NOT NULL DEFAULT ''"),
)


def ensure_gimak_columns() -> None:
    inspector = inspect(gimak_engine)
    postgres = gimak_engine.dialect.name == "postgresql"
    for table, column, pg_type, sqlite_type in COLUNAS_ACRESCENTADAS:
        if not inspector.has_table(table):
            continue
        if column in {item["name"] for item in inspector.get_columns(table)}:
            continue
        tipo = pg_type if postgres else sqlite_type
        with gimak_engine.begin() as connection:
            connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {tipo}'))


def initialize_gimak_database() -> None:
    ensure_gimak_database_exists()
    GimakBase.metadata.create_all(bind=gimak_engine)
    ensure_gimak_columns()


def get_gimak_db():
    db = GimakSessionLocal()
    try:
        yield db
    finally:
        db.close()

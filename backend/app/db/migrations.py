from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


PEDIDOS_COLUMNS = {
    "pcp_previsao_producao": "VARCHAR(120) NOT NULL DEFAULT ''",
    "pcp_previsao_pronto": "VARCHAR(120) NOT NULL DEFAULT ''",
    "pcp_quantidade_produzida": "INTEGER NOT NULL DEFAULT 0",
    "pcp_observacoes": "TEXT NOT NULL DEFAULT ''",
}


def ensure_runtime_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("pedidos"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("pedidos")}
    missing_columns = {
        column_name: column_definition
        for column_name, column_definition in PEDIDOS_COLUMNS.items()
        if column_name not in existing_columns
    }
    if not missing_columns:
        return

    with engine.begin() as connection:
        for column_name, column_definition in missing_columns.items():
            connection.execute(text(f"ALTER TABLE pedidos ADD COLUMN {column_name} {column_definition}"))

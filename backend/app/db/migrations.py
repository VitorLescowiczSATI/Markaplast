from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


PEDIDOS_COLUMNS = {
    "cep": "VARCHAR(16) NOT NULL DEFAULT ''",
    "logradouro": "VARCHAR(180) NOT NULL DEFAULT ''",
    "numero": "VARCHAR(32) NOT NULL DEFAULT ''",
    "bairro": "VARCHAR(120) NOT NULL DEFAULT ''",
    "uf": "VARCHAR(2) NOT NULL DEFAULT ''",
    "pcp_previsao_producao": "VARCHAR(120) NOT NULL DEFAULT ''",
    "pcp_previsao_pronto": "VARCHAR(120) NOT NULL DEFAULT ''",
    "pcp_quantidade_produzida": "INTEGER NOT NULL DEFAULT 0",
    "pcp_observacoes": "TEXT NOT NULL DEFAULT ''",
}


TIMESTAMP_TABLES = {
    "produtos": ("created_at", "updated_at"),
}


def _repair_timestamp_columns(engine: Engine, inspector) -> None:
    for table_name, column_names in TIMESTAMP_TABLES.items():
        if not inspector.has_table(table_name):
            continue

        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        with engine.begin() as connection:
            for column_name in column_names:
                if column_name not in existing_columns:
                    continue

                connection.execute(
                    text(
                        f"UPDATE {table_name} "
                        f"SET {column_name} = CURRENT_TIMESTAMP "
                        f"WHERE {column_name} IS NULL"
                    )
                )

                if engine.dialect.name == "postgresql":
                    connection.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET DEFAULT now()"))
                    connection.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET NOT NULL"))


def ensure_runtime_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    _repair_timestamp_columns(engine, inspector)

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

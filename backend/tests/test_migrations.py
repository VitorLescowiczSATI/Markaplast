from sqlalchemy import create_engine, inspect, text

from app.db.migrations import ensure_runtime_migrations


def test_ensure_runtime_migrations_adds_pcp_columns_to_existing_pedidos_table():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE pedidos (id INTEGER PRIMARY KEY)"))

    ensure_runtime_migrations(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("pedidos")}
    assert {
        "cep",
        "logradouro",
        "numero",
        "bairro",
        "uf",
        "pcp_previsao_producao",
        "pcp_previsao_pronto",
        "pcp_quantidade_produzida",
        "pcp_observacoes",
    }.issubset(columns)


def test_ensure_runtime_migrations_backfills_null_product_timestamps():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE produtos (
                    id INTEGER PRIMARY KEY,
                    nome VARCHAR(120) NOT NULL,
                    created_at DATETIME NULL,
                    updated_at DATETIME NULL
                )
                """
            )
        )
        connection.execute(text("INSERT INTO produtos (id, nome, created_at, updated_at) VALUES (1, '5L M6', NULL, NULL)"))

    ensure_runtime_migrations(engine)

    with engine.connect() as connection:
        row = connection.execute(text("SELECT created_at, updated_at FROM produtos WHERE id = 1")).one()

    assert row.created_at is not None
    assert row.updated_at is not None

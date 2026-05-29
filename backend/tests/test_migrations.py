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

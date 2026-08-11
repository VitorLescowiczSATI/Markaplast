from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.db.session import Base
from app.db.migrations import ensure_runtime_migrations
from app.models.pedido import Pedido, PedidoItem


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


def test_migrate_status_values_relabels_and_collapses():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE pedidos (id INTEGER PRIMARY KEY, status VARCHAR(80))"))
        connection.execute(text("CREATE TABLE cargas (id INTEGER PRIMARY KEY, status_destino VARCHAR(80))"))
        connection.execute(
            text(
                "INSERT INTO pedidos (id, status) VALUES "
                "(1, 'Vai produzir'), (2, 'Pronto para faturar'), (3, 'Separado para entrega'), "
                "(4, 'Enviado'), (5, 'Finalizado'), (6, 'Em produção')"
            )
        )
        connection.execute(
            text("INSERT INTO cargas (id, status_destino) VALUES (1, 'Pronto para faturar'), (2, 'Separado para entrega')")
        )

    ensure_runtime_migrations(engine)

    with engine.connect() as connection:
        pedidos = dict(connection.execute(text("SELECT id, status FROM pedidos")).all())
        cargas = dict(connection.execute(text("SELECT id, status_destino FROM cargas")).all())

    assert pedidos[1] == "A produzir"
    assert pedidos[2] == "Prontos"
    assert pedidos[3] == pedidos[4] == pedidos[5] == "Nota emitida"  # trilha de entrega legada colapsada
    assert pedidos[6] == "Em produção"  # inalterado
    assert cargas[1] == cargas[2] == "Pronto para o envio"


def test_ensure_runtime_migrations_adds_produto_attribute_columns():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE produtos (id INTEGER PRIMARY KEY, nome VARCHAR(120) NOT NULL)"))

    ensure_runtime_migrations(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("produtos")}
    assert {"capacidade", "modelo", "peso", "alca"}.issubset(columns)


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


def test_runtime_migration_cria_item_para_pedido_antigo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        pedido = Pedido(cliente="Legado", produto="5L", cor="Azul", tampa="Rosca", quantidade=20, valor=2, valorTampa=0.5)
        db.add(pedido)
        db.commit()
        pedido_id = pedido.id

    ensure_runtime_migrations(engine)

    with Session(engine) as db:
        item = db.scalar(select(PedidoItem).where(PedidoItem.pedidoId == pedido_id))
        assert item is not None
        assert (item.produto, item.cor, item.quantidade) == ("5L", "Azul", 20)

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
    "data_emissao": "DATE",
    "numero_nota": "VARCHAR(40) NOT NULL DEFAULT ''",
}


PRODUTOS_COLUMNS = {
    "capacidade": "VARCHAR(40) NOT NULL DEFAULT ''",
    "modelo": "VARCHAR(60) NOT NULL DEFAULT ''",
    "peso": "VARCHAR(40) NOT NULL DEFAULT ''",
    "alca": "VARCHAR(3) NOT NULL DEFAULT 'nao'",
}


USUARIOS_COLUMNS = {
    "vendedor": "VARCHAR(80) NOT NULL DEFAULT ''",
}


CLIENTES_COLUMNS = {
    "vendedor": "VARCHAR(80) NOT NULL DEFAULT ''",
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


def _add_missing_columns(engine: Engine, inspector, table_name: str, columns: dict[str, str]) -> None:
    if not inspector.has_table(table_name):
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    missing_columns = {
        column_name: column_definition
        for column_name, column_definition in columns.items()
        if column_name not in existing_columns
    }
    if not missing_columns:
        return

    with engine.begin() as connection:
        for column_name, column_definition in missing_columns.items():
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))


def _migrate_status_values(engine: Engine, inspector) -> None:
    """Renomeia status antigos e colapsa a trilha de entrega legada. Idempotente (seguro a cada boot)."""
    if inspector.has_table("pedidos") and "status" in {c["name"] for c in inspector.get_columns("pedidos")}:
        with engine.begin() as connection:
            connection.execute(text("UPDATE pedidos SET status = 'A produzir' WHERE status = 'Vai produzir'"))
            connection.execute(text("UPDATE pedidos SET status = 'Prontos' WHERE status = 'Pronto para faturar'"))
            connection.execute(
                text("UPDATE pedidos SET status = 'Nota emitida' WHERE status IN ('Separado para entrega', 'Enviado', 'Finalizado')")
            )
    if inspector.has_table("cargas") and "status_destino" in {c["name"] for c in inspector.get_columns("cargas")}:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE cargas SET status_destino = 'Pronto para o envio' "
                    "WHERE status_destino IN ('Pronto para faturar', 'Separado para entrega')"
                )
            )


def _backfill_pedido_itens(engine: Engine, inspector) -> None:
    """Cria o primeiro item dos pedidos antigos. Idempotente e seguro a cada boot."""
    if not inspector.has_table("pedidos") or not inspector.has_table("pedido_itens"):
        return
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO pedido_itens "
                "(pedido_id, ordem, produto, tampa, cor, quantidade, valor, valor_tampa) "
                "SELECT p.id, 0, p.produto, p.tampa, p.cor, p.quantidade, p.valor, p.valor_tampa "
                "FROM pedidos p "
                "WHERE NOT EXISTS (SELECT 1 FROM pedido_itens i WHERE i.pedido_id = p.id)"
            )
        )


def _so_digitos(valor) -> str:
    return "".join(char for char in str(valor or "") if char.isdigit())


def _backfill_vendedor_clientes(engine: Engine) -> None:
    """Carga inicial do responsável: o vendedor do pedido mais recente do cliente (por CNPJ, senão nome).

    Roda só no boot em que a coluna nasce, para não refazer atribuições que o admin limpou depois.
    """
    with engine.begin() as connection:
        pedidos = connection.execute(
            text("SELECT cliente, cnpj, vendedor FROM pedidos WHERE vendedor <> '' ORDER BY id DESC")
        ).all()
        por_cnpj: dict[str, str] = {}
        por_nome: dict[str, str] = {}
        for nome, cnpj, vendedor in pedidos:
            por_cnpj.setdefault(_so_digitos(cnpj), vendedor)
            por_nome.setdefault((nome or "").strip().casefold(), vendedor)
        por_cnpj.pop("", None)
        por_nome.pop("", None)
        for cliente_id, nome, cnpj in connection.execute(text("SELECT id, nome, cnpj FROM clientes")).all():
            vendedor = por_cnpj.get(_so_digitos(cnpj)) or por_nome.get((nome or "").strip().casefold())
            if vendedor:
                connection.execute(
                    text("UPDATE clientes SET vendedor = :vendedor WHERE id = :id"), {"vendedor": vendedor, "id": cliente_id}
                )


def ensure_runtime_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    clientes_sem_vendedor = inspector.has_table("clientes") and "vendedor" not in {
        column["name"] for column in inspector.get_columns("clientes")
    }
    _repair_timestamp_columns(engine, inspector)
    _add_missing_columns(engine, inspector, "pedidos", PEDIDOS_COLUMNS)
    _add_missing_columns(engine, inspector, "produtos", PRODUTOS_COLUMNS)
    _add_missing_columns(engine, inspector, "usuarios", USUARIOS_COLUMNS)
    _add_missing_columns(engine, inspector, "clientes", CLIENTES_COLUMNS)
    if clientes_sem_vendedor and inspector.has_table("pedidos"):
        _backfill_vendedor_clientes(engine)
    _migrate_status_values(engine, inspector)
    _backfill_pedido_itens(engine, inspector)

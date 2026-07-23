from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.preco_cliente import PrecoCliente


def lookup_preco(db: Session, cliente_id: int, produto_id: int) -> PrecoCliente | None:
    return db.scalars(
        select(PrecoCliente).where(
            PrecoCliente.clienteId == cliente_id,
            PrecoCliente.produtoId == produto_id,
        )
    ).first()


def upsert_preco(db: Session, cliente_id: int, produto_id: int, valor, valor_tampa) -> PrecoCliente:
    preco = lookup_preco(db, cliente_id, produto_id)
    if not preco:
        preco = PrecoCliente(clienteId=cliente_id, produtoId=produto_id)
        db.add(preco)
        try:
            db.flush()
        except IntegrityError:
            # Outra requisição criou o mesmo par entre o lookup e o insert: atualiza a linha existente.
            db.rollback()
            preco = lookup_preco(db, cliente_id, produto_id)
    preco.valor = valor
    preco.valorTampa = valor_tampa
    return preco

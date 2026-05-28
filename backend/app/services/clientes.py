from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate


def only_digits(value: str) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def upsert_cliente_do_pedido(db: Session, payload) -> Cliente | None:
    nome = getattr(payload, "cliente", "") or ""
    if not nome.strip():
        return None

    cnpj = only_digits(getattr(payload, "cnpj", ""))
    statement = select(Cliente).where(
        or_(
            Cliente.cnpj == cnpj if cnpj else Cliente.nome == nome,
            Cliente.nome == nome,
        )
    )
    cliente = db.scalars(statement).first()
    if not cliente:
        cliente = Cliente(nome=nome, cnpj=cnpj)
        db.add(cliente)

    cliente.nome = nome
    cliente.cnpj = cnpj or cliente.cnpj
    cliente.cidade = getattr(payload, "cidade", "") or cliente.cidade
    cliente.condicaoPagamento = getattr(payload, "pagamento", "") or cliente.condicaoPagamento
    return cliente


def create_cliente(db: Session, payload: ClienteCreate) -> Cliente:
    cliente = Cliente(**payload.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

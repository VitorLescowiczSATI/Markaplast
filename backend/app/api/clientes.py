from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteRead, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_model=list[ClienteRead])
def listar_clientes(busca: str = "", db: Session = Depends(get_db)):
    statement = select(Cliente).order_by(Cliente.nome)
    if busca:
        termo = f"%{busca}%"
        statement = statement.where(
            or_(
                Cliente.nome.ilike(termo),
                Cliente.cnpj.ilike(termo),
                Cliente.cidade.ilike(termo),
            )
        )
    return db.scalars(statement).all()


@router.post("", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
def criar_cliente(payload: ClienteCreate, db: Session = Depends(get_db)):
    cliente = Cliente(**payload.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.patch("/{cliente_id}", response_model=ClienteRead)
def atualizar_cliente(cliente_id: int, payload: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(cliente, key, value)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")
    db.delete(cliente)
    db.commit()

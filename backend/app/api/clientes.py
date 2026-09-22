from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_profiles
from app.db.session import get_db
from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.models.usuario import Usuario
from app.services.auth import PERFIL_VENDEDOR
from app.services.escopo import filtrar_clientes, filtrar_pedidos, vendedor_do_usuario
from app.schemas.cliente import ClienteCreate, ClienteRead, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_model=list[ClienteRead])
def listar_clientes(
    busca: str = "",
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_profiles("Comercial", "Clientes", PERFIL_VENDEDOR)),
):
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
    clientes = db.scalars(statement).all()
    vendedor_escopo = vendedor_do_usuario(usuario)
    if vendedor_escopo is None:
        return clientes
    pedidos = filtrar_pedidos(db.scalars(select(Pedido)).all(), vendedor_escopo)
    return filtrar_clientes(clientes, pedidos)


@router.post("", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
def criar_cliente(payload: ClienteCreate, db: Session = Depends(get_db), _usuario=Depends(require_profiles("Clientes"))):
    cliente = Cliente(**payload.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.patch("/{cliente_id}", response_model=ClienteRead)
def atualizar_cliente(
    cliente_id: int,
    payload: ClienteUpdate,
    db: Session = Depends(get_db),
    _usuario=Depends(require_profiles("Clientes")),
):
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(cliente, key, value)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_cliente(cliente_id: int, db: Session = Depends(get_db), _usuario=Depends(require_profiles("Clientes"))):
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")
    db.delete(cliente)
    db.commit()

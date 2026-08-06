from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_profiles
from app.db.session import get_db
from app.models.cliente import Cliente
from app.models.preco_cliente import PrecoCliente
from app.models.produto import Produto
from app.schemas.preco_cliente import PrecoClienteItem, PrecoClienteRead, PrecoClienteUpsert
from app.services.precos import lookup_preco, upsert_preco

router = APIRouter(prefix="/precos", tags=["precos"])


@router.get("", response_model=list[PrecoClienteItem])
def listar_precos(
    clienteId: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_profiles("Comercial", "Clientes")),
):
    rows = db.execute(
        select(PrecoCliente, Produto.nome)
        .join(Produto, Produto.id == PrecoCliente.produtoId)
        .where(PrecoCliente.clienteId == clienteId)
        .order_by(Produto.nome)
    ).all()
    return [
        PrecoClienteItem(
            id=preco.id,
            produtoId=preco.produtoId,
            produtoNome=nome,
            valor=float(preco.valor),
            valorTampa=float(preco.valorTampa),
        )
        for preco, nome in rows
    ]


@router.get("/lookup", response_model=PrecoClienteRead | None)
def lookup(
    clienteId: int,
    produtoId: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_profiles("Comercial", "Clientes")),
):
    return lookup_preco(db, clienteId, produtoId)


@router.post("", response_model=PrecoClienteRead, status_code=status.HTTP_201_CREATED)
def salvar_preco(
    payload: PrecoClienteUpsert,
    db: Session = Depends(get_db),
    _usuario=Depends(require_profiles("Clientes")),
):
    if not db.get(Cliente, payload.clienteId):
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")
    if not db.get(Produto, payload.produtoId):
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    preco = upsert_preco(db, payload.clienteId, payload.produtoId, payload.valor, payload.valorTampa)
    db.commit()
    db.refresh(preco)
    return preco


@router.delete("/{preco_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_preco(preco_id: int, db: Session = Depends(get_db), _usuario=Depends(require_profiles("Clientes"))):
    preco = db.get(PrecoCliente, preco_id)
    if not preco:
        raise HTTPException(status_code=404, detail="Preco nao encontrado")
    db.delete(preco)
    db.commit()

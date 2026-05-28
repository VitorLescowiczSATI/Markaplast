from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.carga import Carga
from app.models.pedido import Pedido
from app.schemas.carga import CargaCreate, CargaRead

router = APIRouter(prefix="/cargas", tags=["cargas"])


@router.get("", response_model=list[CargaRead])
def listar_cargas(db: Session = Depends(get_db)):
    statement = select(Carga).options(selectinload(Carga.pedidos)).order_by(Carga.id.desc())
    return db.scalars(statement).all()


@router.post("", response_model=CargaRead, status_code=status.HTTP_201_CREATED)
def criar_carga(payload: CargaCreate, db: Session = Depends(get_db)):
    pedidos = db.scalars(select(Pedido).where(Pedido.id.in_(payload.pedidoIds))).all()
    encontrados = {pedido.id for pedido in pedidos}
    faltantes = [pedido_id for pedido_id in payload.pedidoIds if pedido_id not in encontrados]
    if faltantes:
        raise HTTPException(status_code=404, detail=f"Pedidos não encontrados: {faltantes}")

    carga = Carga(
        regiao=payload.regiao,
        motorista=payload.motorista,
        placa=payload.placa,
        statusDestino=payload.statusDestino,
        pedidos=list(pedidos),
    )
    for pedido in pedidos:
        pedido.status = payload.statusDestino

    db.add(carga)
    db.commit()
    db.refresh(carga)
    return carga

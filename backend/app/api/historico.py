from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pedido_historico import PedidoHistorico
from app.schemas.historico import PedidoHistoricoRead

router = APIRouter(prefix="/historico", tags=["historico"])


@router.get("/pedidos", response_model=list[PedidoHistoricoRead])
def historico_recente(db: Session = Depends(get_db), limit: int = 40):
    return db.scalars(select(PedidoHistorico).order_by(PedidoHistorico.id.desc()).limit(limit)).all()


@router.get("/pedidos/{pedido_id}", response_model=list[PedidoHistoricoRead])
def historico_pedido(pedido_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(PedidoHistorico).where(PedidoHistorico.pedidoId == pedido_id).order_by(PedidoHistorico.id.desc())
    ).all()

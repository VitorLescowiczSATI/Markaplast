from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PedidoHistorico(Base):
    __tablename__ = "pedidos_historico"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pedidoId: Mapped[int] = mapped_column("pedido_id", ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    deValor: Mapped[str] = mapped_column("de_valor", String(120), default="", nullable=False)
    paraValor: Mapped[str] = mapped_column("para_valor", String(120), default="", nullable=False)
    usuario: Mapped[str] = mapped_column(String(120), default="Sistema", nullable=False)
    observacao: Mapped[str] = mapped_column(Text, default="", nullable=False)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)

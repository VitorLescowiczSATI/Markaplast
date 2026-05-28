from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


carga_pedidos = Table(
    "carga_pedidos",
    Base.metadata,
    Column("carga_id", ForeignKey("cargas.id", ondelete="CASCADE"), primary_key=True),
    Column("pedido_id", ForeignKey("pedidos.id", ondelete="CASCADE"), primary_key=True),
)


class Carga(Base):
    __tablename__ = "cargas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    regiao: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    motorista: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    placa: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    statusDestino: Mapped[str] = mapped_column("status_destino", String(80), default="Pronto para faturar", nullable=False)
    data: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)

    pedidos = relationship("Pedido", secondary=carga_pedidos, back_populates="cargas")

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PrecoCliente(Base):
    __tablename__ = "precos_cliente"
    __table_args__ = (UniqueConstraint("cliente_id", "produto_id", name="uq_preco_cliente_produto"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    clienteId: Mapped[int] = mapped_column(
        "cliente_id", ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    produtoId: Mapped[int] = mapped_column(
        "produto_id", ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0, nullable=False)
    valorTampa: Mapped[Decimal] = mapped_column("valor_tampa", Numeric(12, 4), default=0, nullable=False)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

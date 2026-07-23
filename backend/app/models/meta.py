from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Meta(Base):
    """Meta de faturamento. escopo='empresa' (vendedor='') ou escopo='vendedor'."""

    __tablename__ = "metas"
    __table_args__ = (UniqueConstraint("escopo", "vendedor", "periodo", name="uq_meta_escopo_vendedor_periodo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    escopo: Mapped[str] = mapped_column(String(20), default="empresa", nullable=False)
    vendedor: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)  # diaria | mensal | trimestral
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

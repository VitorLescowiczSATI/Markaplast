from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class NotaFiscalDraft(Base):
    __tablename__ = "notas_fiscais"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pedidoId: Mapped[int] = mapped_column("pedido_id", ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True)
    referencia: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    provedor: Mapped[str] = mapped_column(String(80), default="Focus NFe", nullable=False)
    ambiente: Mapped[str] = mapped_column(String(40), default="homologacao", nullable=False)
    status: Mapped[str] = mapped_column(String(80), default="Rascunho fiscal", nullable=False, index=True)
    numero: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    serie: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    chaveAcesso: Mapped[str] = mapped_column("chave_acesso", String(80), default="", nullable=False)
    xmlUrl: Mapped[str] = mapped_column("xml_url", Text, default="", nullable=False)
    danfeUrl: Mapped[str] = mapped_column("danfe_url", Text, default="", nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

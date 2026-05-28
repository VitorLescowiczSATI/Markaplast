from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    cnpj: Mapped[str] = mapped_column(String(32), default="", nullable=False, index=True)
    contato: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    telefone: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    email: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    cep: Mapped[str] = mapped_column(String(16), default="", nullable=False)
    logradouro: Mapped[str] = mapped_column(String(180), default="", nullable=False)
    numero: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    bairro: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    cidade: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    uf: Mapped[str] = mapped_column(String(2), default="", nullable=False)
    condicaoPagamento: Mapped[str] = mapped_column("condicao_pagamento", String(160), default="", nullable=False)
    observacoes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

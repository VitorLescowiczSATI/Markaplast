from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    categoria: Mapped[str] = mapped_column(String(80), default="Embalagem", nullable=False)
    unidade: Mapped[str] = mapped_column(String(20), default="un", nullable=False)
    precoBase: Mapped[Decimal] = mapped_column("preco_base", Numeric(12, 4), default=0, nullable=False)
    valorTampaPadrao: Mapped[Decimal] = mapped_column("valor_tampa_padrao", Numeric(12, 4), default=0, nullable=False)
    estoqueAtual: Mapped[int] = mapped_column("estoque_atual", Integer, default=0, nullable=False)
    estoqueReservado: Mapped[int] = mapped_column("estoque_reservado", Integer, default=0, nullable=False)
    estoqueMinimo: Mapped[int] = mapped_column("estoque_minimo", Integer, default=0, nullable=False)
    ativo: Mapped[str] = mapped_column(String(3), default="sim", nullable=False)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    @property
    def disponivel(self) -> int:
        return max(0, int(self.estoqueAtual or 0) - int(self.estoqueReservado or 0))


class MovimentoEstoque(Base):
    __tablename__ = "movimentos_estoque"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    produtoId: Mapped[int] = mapped_column("produto_id", ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True)
    pedidoId: Mapped[int | None] = mapped_column("pedido_id", ForeignKey("pedidos.id", ondelete="SET NULL"), nullable=True, index=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    saldoAnterior: Mapped[int] = mapped_column("saldo_anterior", Integer, nullable=False)
    saldoPosterior: Mapped[int] = mapped_column("saldo_posterior", Integer, nullable=False)
    observacao: Mapped[str] = mapped_column(Text, default="", nullable=False)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)

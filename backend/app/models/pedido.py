from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    data: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    cliente: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    cnpj: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    cep: Mapped[str] = mapped_column(String(16), default="", nullable=False)
    logradouro: Mapped[str] = mapped_column(String(180), default="", nullable=False)
    numero: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    bairro: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    cidade: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    uf: Mapped[str] = mapped_column(String(2), default="", nullable=False)
    produto: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    tampa: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    cor: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0, nullable=False)
    valorTampa: Mapped[Decimal] = mapped_column("valor_tampa", Numeric(12, 4), default=0, nullable=False)
    pagamento: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    vendedor: Mapped[str] = mapped_column(String(80), default="", nullable=False, index=True)
    transporte: Mapped[str] = mapped_column(String(180), default="", nullable=False)
    tipoFrete: Mapped[str] = mapped_column("tipo_frete", String(16), default="", nullable=False)
    detalheFOB: Mapped[str] = mapped_column("detalhe_fob", String(180), default="", nullable=False)
    faturamento: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    tipoEntrega: Mapped[str] = mapped_column("tipo_entrega", String(80), default="", nullable=False)
    observacoes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    pcpPrevisaoProducao: Mapped[str] = mapped_column("pcp_previsao_producao", String(120), default="", nullable=False)
    pcpPrevisaoPronto: Mapped[str] = mapped_column("pcp_previsao_pronto", String(120), default="", nullable=False)
    pcpQuantidadeProduzida: Mapped[int] = mapped_column("pcp_quantidade_produzida", Integer, default=0, nullable=False)
    pcpObservacoes: Mapped[str] = mapped_column("pcp_observacoes", Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(80), default="Novo pedido", nullable=False, index=True)
    statusFinanceiro: Mapped[str] = mapped_column("status_financeiro", String(80), default="Aguardando pagamento", nullable=False, index=True)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    cargas = relationship("Carga", secondary="carga_pedidos", back_populates="pedidos")

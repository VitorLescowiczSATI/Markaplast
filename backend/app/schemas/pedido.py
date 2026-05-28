from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PedidoBase(BaseModel):
    cliente: str = Field(..., min_length=1, max_length=180)
    cnpj: str = ""
    cidade: str = ""
    produto: str = Field(..., min_length=1, max_length=120)
    tampa: str = ""
    cor: str = ""
    quantidade: int = Field(..., gt=0)
    valor: float = Field(0, ge=0)
    valorTampa: float = Field(0, ge=0)
    pagamento: str = ""
    vendedor: str = ""
    transporte: str = ""
    tipoFrete: str = ""
    detalheFOB: str = ""
    faturamento: str = ""
    tipoEntrega: str = ""
    observacoes: str = ""
    pcpPrevisaoProducao: str = ""
    pcpPrevisaoPronto: str = ""
    pcpQuantidadeProduzida: int = Field(0, ge=0)
    pcpObservacoes: str = ""


class PedidoCreate(PedidoBase):
    pass


class PedidoUpdate(BaseModel):
    cliente: str | None = None
    cnpj: str | None = None
    cidade: str | None = None
    produto: str | None = None
    tampa: str | None = None
    cor: str | None = None
    quantidade: int | None = Field(default=None, gt=0)
    valor: float | None = Field(default=None, ge=0)
    valorTampa: float | None = Field(default=None, ge=0)
    pagamento: str | None = None
    vendedor: str | None = None
    transporte: str | None = None
    tipoFrete: str | None = None
    detalheFOB: str | None = None
    faturamento: str | None = None
    tipoEntrega: str | None = None
    observacoes: str | None = None
    pcpPrevisaoProducao: str | None = None
    pcpPrevisaoPronto: str | None = None
    pcpQuantidadeProduzida: int | None = Field(default=None, ge=0)
    pcpObservacoes: str | None = None
    status: str | None = None
    statusFinanceiro: str | None = None


class PedidoStatusUpdate(BaseModel):
    status: str


class PedidoFinanceiroUpdate(BaseModel):
    statusFinanceiro: str


class PedidoRead(PedidoBase):
    id: int
    data: date
    status: str
    statusFinanceiro: str
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumoRead(BaseModel):
    totalPedidos: int
    novos: int
    aguardando: int
    vaiProduzir: int
    producao: int
    faturar: int
    notasEmitidas: int
    financeiroPago: int
    financeiroPendente: int
    total: float

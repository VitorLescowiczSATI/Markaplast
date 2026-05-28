from pydantic import BaseModel


class DashboardItem(BaseModel):
    label: str
    valor: float
    quantidade: int | None = None


class AlertaRead(BaseModel):
    tipo: str
    prioridade: str
    titulo: str
    detalhe: str
    entidadeId: int | None = None


class DashboardRead(BaseModel):
    resumo: dict
    porStatus: list[DashboardItem]
    porVendedor: list[DashboardItem]
    porProduto: list[DashboardItem]
    estoqueCritico: list[dict]
    alertas: list[AlertaRead]

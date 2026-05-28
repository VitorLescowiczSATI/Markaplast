from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pedido import PedidoRead


class CargaCreate(BaseModel):
    regiao: str = Field(..., min_length=1, max_length=160)
    motorista: str = ""
    placa: str = ""
    pedidoIds: list[int] = Field(..., min_length=1)
    statusDestino: str = "Pronto para faturar"


class CargaRead(BaseModel):
    id: int
    regiao: str
    motorista: str
    placa: str
    statusDestino: str
    data: date
    createdAt: datetime
    pedidos: list[PedidoRead]

    model_config = ConfigDict(from_attributes=True)

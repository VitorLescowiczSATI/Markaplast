from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PedidoHistoricoRead(BaseModel):
    id: int
    pedidoId: int
    tipo: str
    deValor: str
    paraValor: str
    usuario: str
    observacao: str
    createdAt: datetime

    model_config = ConfigDict(from_attributes=True)

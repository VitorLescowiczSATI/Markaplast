from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotaFiscalRead(BaseModel):
    id: int
    pedidoId: int
    referencia: str
    provedor: str
    ambiente: str
    status: str
    numero: str
    serie: str
    chaveAcesso: str
    xmlUrl: str
    danfeUrl: str
    payload: dict
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


class NotaFiscalUpdate(BaseModel):
    status: str | None = None
    numero: str | None = None
    serie: str | None = None
    chaveAcesso: str | None = None
    xmlUrl: str | None = None
    danfeUrl: str | None = None
    payload: dict | None = None

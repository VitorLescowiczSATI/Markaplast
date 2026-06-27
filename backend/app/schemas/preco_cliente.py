from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrecoClienteBase(BaseModel):
    clienteId: int
    produtoId: int
    valor: float = Field(0, ge=0)
    valorTampa: float = Field(0, ge=0)


class PrecoClienteUpsert(PrecoClienteBase):
    pass


class PrecoClienteRead(PrecoClienteBase):
    id: int
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


class PrecoClienteItem(BaseModel):
    """Preço de um produto para um cliente, já com o nome do produto resolvido."""

    id: int
    produtoId: int
    produtoNome: str
    valor: float
    valorTampa: float

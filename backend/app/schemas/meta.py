from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetaBase(BaseModel):
    escopo: str = "empresa"  # empresa | vendedor
    vendedor: str = ""
    periodo: str  # diaria | mensal | trimestral
    valor: float = Field(0, ge=0)


class MetaUpsert(MetaBase):
    pass


class MetaRead(MetaBase):
    id: int
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)

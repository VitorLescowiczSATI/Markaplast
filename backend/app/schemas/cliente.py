from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClienteBase(BaseModel):
    nome: str
    cnpj: str = ""
    contato: str = ""
    telefone: str = ""
    email: str = ""
    cep: str = ""
    logradouro: str = ""
    numero: str = ""
    bairro: str = ""
    cidade: str = ""
    uf: str = ""
    condicaoPagamento: str = ""
    observacoes: str = ""


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: str | None = None
    cnpj: str | None = None
    contato: str | None = None
    telefone: str | None = None
    email: str | None = None
    cep: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    condicaoPagamento: str | None = None
    observacoes: str | None = None


class ClienteRead(ClienteBase):
    id: int
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)

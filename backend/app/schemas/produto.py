from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProdutoBase(BaseModel):
    nome: str
    categoria: str = "Embalagem"
    unidade: str = "un"
    precoBase: float = Field(0, ge=0)
    valorTampaPadrao: float = Field(0, ge=0)
    estoqueAtual: int = Field(0, ge=0)
    estoqueReservado: int = Field(0, ge=0)
    estoqueMinimo: int = Field(0, ge=0)
    ativo: str = "sim"


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    nome: str | None = None
    categoria: str | None = None
    unidade: str | None = None
    precoBase: float | None = Field(default=None, ge=0)
    valorTampaPadrao: float | None = Field(default=None, ge=0)
    estoqueAtual: int | None = Field(default=None, ge=0)
    estoqueReservado: int | None = Field(default=None, ge=0)
    estoqueMinimo: int | None = Field(default=None, ge=0)
    ativo: str | None = None


class ProdutoRead(ProdutoBase):
    id: int
    disponivel: int
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


class MovimentoEstoqueCreate(BaseModel):
    tipo: str
    quantidade: int = Field(..., gt=0)
    observacao: str = ""


class MovimentoEstoqueRead(BaseModel):
    id: int
    produtoId: int
    pedidoId: int | None
    tipo: str
    quantidade: int
    saldoAnterior: int
    saldoPosterior: int
    observacao: str
    createdAt: datetime

    model_config = ConfigDict(from_attributes=True)

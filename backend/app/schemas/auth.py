from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


PerfilUsuario = Literal[
    "Administrador",
    "Inteligência",
    "Comercial",
    "Clientes",
    "Estoque",
    "PCP",
    "Logística",
    "Faturamento",
    "Financeiro",
    "Fiscal",
]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    senha: str = Field(min_length=1, max_length=200)


class UsuarioRead(BaseModel):
    id: int
    nome: str
    username: str
    perfil: str
    ativo: bool

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    usuario: UsuarioRead


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    senha: str = Field(min_length=8, max_length=200)
    perfil: PerfilUsuario

    @field_validator("nome", "username", mode="before")
    @classmethod
    def limpar_texto(cls, valor: str) -> str:
        return valor.strip()


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    perfil: PerfilUsuario | None = None
    ativo: bool | None = None

    @field_validator("nome", mode="before")
    @classmethod
    def limpar_nome(cls, valor: str | None) -> str | None:
        return valor.strip() if valor is not None else None


class UsuarioSenhaUpdate(BaseModel):
    senha: str = Field(min_length=8, max_length=200)

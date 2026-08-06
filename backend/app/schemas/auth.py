from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    senha: str = Field(min_length=1, max_length=200)


class UsuarioRead(BaseModel):
    id: int
    nome: str
    username: str
    perfil: str

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    usuario: UsuarioRead

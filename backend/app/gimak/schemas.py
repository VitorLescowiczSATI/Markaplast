from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


GimakPerfil = Literal["Administrador", "PCP", "Fábrica", "TV"]
GimakStatus = Literal["todo", "doing", "paused", "blocked", "done"]
GimakTipoAtendimento = Literal["Assistência técnica", "Instalação"]
GimakSituacaoProjeto = Literal["andamento", "concluidos", "todos"]
GimakSituacaoAtendimento = Literal["agendados", "concluidos", "todos"]


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
    perfil: GimakPerfil = "Fábrica"

    @field_validator("nome", "username", mode="before")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip()


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    perfil: GimakPerfil | None = None
    ativo: bool | None = None


class SenhaUpdate(BaseModel):
    senha: str = Field(min_length=8, max_length=200)


class ProjetoCreate(BaseModel):
    cliente: str = Field(min_length=2, max_length=180)
    equipamento: str = Field(min_length=2, max_length=180)


class ProjetoUpdate(BaseModel):
    cliente: str | None = Field(default=None, min_length=2, max_length=180)
    equipamento: str | None = Field(default=None, min_length=2, max_length=180)
    concluido: bool | None = None


class ProjetoRead(BaseModel):
    id: int
    cliente: str
    equipamento: str
    ativo: bool
    concluidoEm: datetime | None = None
    createdAt: datetime
    model_config = ConfigDict(from_attributes=True)


class TarefaCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=240)
    ordem: str = Field(default="TAREFA", max_length=80)
    responsavel: str = Field(min_length=2, max_length=120)
    dataPlanejada: date
    horario: str = Field(default="08:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    prioridade: Literal["Normal", "Urgente"] = "Normal"
    observacao: str = Field(default="", max_length=4000)
    projetoId: int | None = None


class TarefaUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=2, max_length=240)
    ordem: str | None = Field(default=None, max_length=80)
    responsavel: str | None = Field(default=None, min_length=2, max_length=120)
    dataPlanejada: date | None = None
    horario: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    prioridade: Literal["Normal", "Urgente"] | None = None
    observacao: str | None = Field(default=None, max_length=4000)
    projetoId: int | None = None


class StatusUpdate(BaseModel):
    status: GimakStatus
    motivo: str = Field(default="", max_length=4000)


class ApontamentoRead(BaseModel):
    id: int
    usuarioId: int | None
    statusAnterior: str
    statusNovo: str
    motivo: str
    createdAt: datetime
    model_config = ConfigDict(from_attributes=True)


class TarefaRead(BaseModel):
    id: int
    titulo: str
    ordem: str
    responsavel: str
    dataPlanejada: date
    horario: str
    prioridade: str
    status: str
    observacao: str
    motivo: str
    elapsedSeconds: int
    startedAt: datetime | None
    finishedAt: datetime | None
    projetoId: int | None
    createdAt: datetime
    historico: list[ApontamentoRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class AtendimentoCreate(BaseModel):
    tipo: GimakTipoAtendimento = "Assistência técnica"
    cliente: str = Field(min_length=2, max_length=180)
    local: str = Field(default="", max_length=240)
    tecnico: str = Field(min_length=2, max_length=120)
    data: date
    horario: str = Field(default="08:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    descricao: str = Field(default="", max_length=4000)

    @field_validator("cliente", "local", "tecnico", "descricao", mode="before")
    @classmethod
    def clean_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class AtendimentoUpdate(BaseModel):
    tipo: GimakTipoAtendimento | None = None
    cliente: str | None = Field(default=None, min_length=2, max_length=180)
    local: str | None = Field(default=None, max_length=240)
    tecnico: str | None = Field(default=None, min_length=2, max_length=120)
    data: date | None = None
    horario: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    descricao: str | None = Field(default=None, max_length=4000)


class AtendimentoConclusao(BaseModel):
    relatorio: str = Field(min_length=3, max_length=8000)

    @field_validator("relatorio", mode="before")
    @classmethod
    def clean_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class AtendimentoRead(BaseModel):
    id: int
    tipo: str
    cliente: str
    local: str
    tecnico: str
    data: date
    horario: str
    descricao: str
    status: str
    relatorio: str
    concluidoEm: datetime | None
    concluidoPorId: int | None
    createdAt: datetime
    model_config = ConfigDict(from_attributes=True)

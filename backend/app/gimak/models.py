from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.gimak.db import GimakBase


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GimakUsuario(GimakBase):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    senhaHash: Mapped[str] = mapped_column("senha_hash", String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(40), nullable=False, default="Fábrica", index=True)
    cargo: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GimakProjeto(GimakBase):
    __tablename__ = "projetos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    equipamento: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    concluidoEm: Mapped[datetime | None] = mapped_column(
        "concluido_em", DateTime(timezone=True), nullable=True, index=True
    )
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tarefas: Mapped[list["GimakTarefa"]] = relationship(back_populates="projeto")


class GimakTarefa(GimakBase):
    __tablename__ = "tarefas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    ordem: Mapped[str] = mapped_column(String(80), nullable=False, default="TAREFA", index=True)
    responsavel: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    dataPlanejada: Mapped[date] = mapped_column("data_planejada", Date, nullable=False, default=date.today, index=True)
    horario: Mapped[str] = mapped_column(String(5), nullable=False, default="08:00")
    prioridade: Mapped[str] = mapped_column(String(20), nullable=False, default="Normal")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo", index=True)
    observacao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    motivo: Mapped[str] = mapped_column(Text, nullable=False, default="")
    elapsedSeconds: Mapped[int] = mapped_column("elapsed_seconds", Integer, nullable=False, default=0)
    startedAt: Mapped[datetime | None] = mapped_column("started_at", DateTime(timezone=True), nullable=True)
    finishedAt: Mapped[datetime | None] = mapped_column("finished_at", DateTime(timezone=True), nullable=True)
    projetoId: Mapped[int | None] = mapped_column(
        "projeto_id", ForeignKey("projetos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    createdById: Mapped[int | None] = mapped_column(
        "created_by_id", ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    projeto: Mapped[GimakProjeto | None] = relationship(back_populates="tarefas")
    historico: Mapped[list["GimakApontamento"]] = relationship(
        back_populates="tarefa", cascade="all, delete-orphan", order_by="GimakApontamento.createdAt"
    )


class GimakApontamento(GimakBase):
    __tablename__ = "apontamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tarefaId: Mapped[int] = mapped_column(
        "tarefa_id", ForeignKey("tarefas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usuarioId: Mapped[int | None] = mapped_column(
        "usuario_id", ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    statusAnterior: Mapped[str] = mapped_column("status_anterior", String(20), nullable=False)
    statusNovo: Mapped[str] = mapped_column("status_novo", String(20), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False, default="")
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), default=utc_now, nullable=False)

    tarefa: Mapped[GimakTarefa] = relationship(back_populates="historico")


class GimakAtendimento(GimakBase):
    """Assistência técnica ou instalação: trabalho feito fora da empresa, no cliente."""

    __tablename__ = "atendimentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, default="Assistência técnica", index=True)
    cliente: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    local: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    tecnico: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    # Data de ida. dataVolta só existe quando a visita passa de um dia.
    data: Mapped[date] = mapped_column(Date, nullable=False, default=date.today, index=True)
    dataVolta: Mapped[date | None] = mapped_column("data_volta", Date, nullable=True)
    # horario é herança do formato antigo: continua no banco para os registros que já
    # existiam, mas quem manda hoje é horarioSaida.
    horario: Mapped[str] = mapped_column(String(5), nullable=False, default="08:00")
    # Horários planejados pelo administrador. O que de fato aconteceu fica em saidaEm e concluidoEm.
    horarioSaida: Mapped[str] = mapped_column("horario_saida", String(5), nullable=False, default="")
    horarioRetorno: Mapped[str] = mapped_column("horario_retorno", String(5), nullable=False, default="")
    descricao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="agendado", index=True)
    relatorio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    saidaEm: Mapped[datetime | None] = mapped_column("saida_em", DateTime(timezone=True), nullable=True)
    saidaPorId: Mapped[int | None] = mapped_column(
        "saida_por_id", ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    concluidoEm: Mapped[datetime | None] = mapped_column("concluido_em", DateTime(timezone=True), nullable=True)
    concluidoPorId: Mapped[int | None] = mapped_column(
        "concluido_por_id", ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    createdById: Mapped[int | None] = mapped_column(
        "created_by_id", ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    pendencias: Mapped[list["GimakPendencia"]] = relationship(
        back_populates="atendimento", cascade="all, delete-orphan", order_by="GimakPendencia.createdAt"
    )


class GimakPendencia(GimakBase):
    """O que ficou faltando depois de um atendimento, para o administrador não esquecer."""

    __tablename__ = "pendencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    atendimentoId: Mapped[int] = mapped_column(
        "atendimento_id", ForeignKey("atendimentos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="aberta", index=True)
    resolucao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    criadoPorId: Mapped[int | None] = mapped_column(
        "criado_por_id", ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    resolvidoPorId: Mapped[int | None] = mapped_column(
        "resolvido_por_id", ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    resolvidoEm: Mapped[datetime | None] = mapped_column("resolvido_em", DateTime(timezone=True), nullable=True)
    createdAt: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True), default=utc_now, nullable=False)

    atendimento: Mapped[GimakAtendimento] = relationship(back_populates="pendencias")

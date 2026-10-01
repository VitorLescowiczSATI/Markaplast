"""Escopo do perfil Vendedor: clientes de que ele é responsável, os pedidos desses clientes e os lançados no nome dele."""

import unicodedata
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.models.usuario import Usuario
from app.services.auth import PERFIL_VENDEDOR
from app.services.clientes import only_digits


def normalizar_vendedor(nome: str | None) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.split()).casefold()


def _nome_cliente(nome: str | None) -> str:
    return (nome or "").strip().casefold()


def vendedor_do_usuario(usuario: Usuario) -> str | None:
    """Nome normalizado do vendedor quando o login é restrito; None quando enxerga tudo."""
    if usuario.perfil != PERFIL_VENDEDOR:
        return None
    # Perfil Vendedor sem vínculo não pode cair em "vê tudo": casa com nada.
    return normalizar_vendedor(usuario.vendedor) or "\x00sem-vinculo"


@dataclass
class EscopoVendedor:
    """vendedor=None significa sem restrição."""

    vendedor: str | None
    clientes: list[Cliente] = field(default_factory=list)
    cnpjs: set[str] = field(default_factory=set)
    nomes: set[str] = field(default_factory=set)

    def ve_pedido(self, pedido: Pedido) -> bool:
        if self.vendedor is None or normalizar_vendedor(pedido.vendedor) == self.vendedor:
            return True
        cnpj = only_digits(pedido.cnpj)
        if cnpj:
            return cnpj in self.cnpjs
        return _nome_cliente(pedido.cliente) in self.nomes

    def filtrar_pedidos(self, pedidos) -> list[Pedido]:
        return [pedido for pedido in pedidos if self.ve_pedido(pedido)]


def escopo_do_usuario(db: Session, usuario: Usuario) -> EscopoVendedor:
    vendedor = vendedor_do_usuario(usuario)
    if vendedor is None:
        return EscopoVendedor(vendedor=None)
    clientes = [
        cliente
        for cliente in db.scalars(select(Cliente).order_by(Cliente.nome)).all()
        if normalizar_vendedor(cliente.vendedor) == vendedor
    ]
    return EscopoVendedor(
        vendedor=vendedor,
        clientes=clientes,
        cnpjs={only_digits(cliente.cnpj) for cliente in clientes} - {""},
        nomes={_nome_cliente(cliente.nome) for cliente in clientes} - {""},
    )

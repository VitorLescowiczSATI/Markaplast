"""Escopo do perfil Vendedor: o login enxerga só os pedidos com o nome dele e os clientes desses pedidos."""

import unicodedata

from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.models.usuario import Usuario
from app.services.auth import PERFIL_VENDEDOR
from app.services.clientes import only_digits


def normalizar_vendedor(nome: str | None) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.split()).casefold()


def vendedor_do_usuario(usuario: Usuario) -> str | None:
    """Nome normalizado do vendedor quando o login é restrito; None quando enxerga tudo."""
    if usuario.perfil != PERFIL_VENDEDOR:
        return None
    # Perfil Vendedor sem vínculo não pode cair em "vê tudo": casa com nada.
    return normalizar_vendedor(usuario.vendedor) or "\x00sem-vinculo"


def pedido_do_vendedor(pedido: Pedido, vendedor: str | None) -> bool:
    return vendedor is None or normalizar_vendedor(pedido.vendedor) == vendedor


def filtrar_pedidos(pedidos, vendedor: str | None) -> list[Pedido]:
    return [pedido for pedido in pedidos if pedido_do_vendedor(pedido, vendedor)]


def filtrar_clientes(clientes, pedidos_do_vendedor) -> list[Cliente]:
    """Clientes que aparecem em algum pedido do vendedor, por CNPJ ou pelo nome exato."""
    cnpjs = {only_digits(pedido.cnpj) for pedido in pedidos_do_vendedor} - {""}
    nomes = {(pedido.cliente or "").strip().casefold() for pedido in pedidos_do_vendedor} - {""}
    return [
        cliente
        for cliente in clientes
        if (only_digits(cliente.cnpj) and only_digits(cliente.cnpj) in cnpjs)
        or (cliente.nome or "").strip().casefold() in nomes
    ]

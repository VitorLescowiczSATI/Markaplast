from sqlalchemy.orm import Session

from app.models.pedido_historico import PedidoHistorico


def registrar_historico(
    db: Session,
    pedido_id: int,
    tipo: str,
    de_valor: str = "",
    para_valor: str = "",
    usuario: str = "Sistema",
    observacao: str = "",
) -> PedidoHistorico:
    item = PedidoHistorico(
        pedidoId=pedido_id,
        tipo=tipo,
        deValor=de_valor or "",
        paraValor=para_valor or "",
        usuario=usuario,
        observacao=observacao,
    )
    db.add(item)
    return item

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.produto import MovimentoEstoque, Produto


def get_produto_por_nome(db: Session, nome: str) -> Produto | None:
    if not nome:
        return None
    return db.scalars(select(Produto).where(Produto.nome == nome)).first()


def registrar_movimento(
    db: Session,
    produto: Produto,
    tipo: str,
    quantidade: int,
    pedido_id: int | None = None,
    observacao: str = "",
) -> MovimentoEstoque:
    saldo_anterior = int(produto.estoqueAtual or 0)
    reserva_anterior = int(produto.estoqueReservado or 0)

    if tipo == "Entrada":
        produto.estoqueAtual = saldo_anterior + quantidade
    elif tipo == "Saida":
        produto.estoqueAtual = saldo_anterior - quantidade
    elif tipo == "Ajuste":
        produto.estoqueAtual = quantidade
    elif tipo == "Reserva":
        produto.estoqueReservado = reserva_anterior + quantidade
    elif tipo == "Liberacao":
        produto.estoqueReservado = max(0, reserva_anterior - quantidade)
    elif tipo == "Baixa reserva":
        produto.estoqueReservado = max(0, reserva_anterior - quantidade)
        produto.estoqueAtual = saldo_anterior - quantidade

    movimento = MovimentoEstoque(
        produtoId=produto.id,
        pedidoId=pedido_id,
        tipo=tipo,
        quantidade=quantidade,
        saldoAnterior=saldo_anterior,
        saldoPosterior=int(produto.estoqueAtual or 0),
        observacao=observacao,
    )
    db.add(movimento)
    return movimento


def reservar_estoque_para_pedido(db: Session, pedido) -> None:
    produto = get_produto_por_nome(db, pedido.produto)
    if not produto:
        return
    registrar_movimento(
        db,
        produto,
        "Reserva",
        int(pedido.quantidade or 0),
        pedido_id=pedido.id,
        observacao=f"Reserva automatica do pedido #{pedido.id}",
    )


def liberar_reserva_do_pedido(db: Session, pedido) -> None:
    produto = get_produto_por_nome(db, pedido.produto)
    if not produto:
        return
    registrar_movimento(
        db,
        produto,
        "Liberacao",
        int(pedido.quantidade or 0),
        pedido_id=pedido.id,
        observacao=f"Liberacao de reserva do pedido #{pedido.id}",
    )


def baixar_reserva_do_pedido(db: Session, pedido) -> None:
    produto = get_produto_por_nome(db, pedido.produto)
    if not produto:
        return
    registrar_movimento(
        db,
        produto,
        "Baixa reserva",
        int(pedido.quantidade or 0),
        pedido_id=pedido.id,
        observacao=f"Baixa de estoque ao finalizar pedido #{pedido.id}",
    )


def recalcular_reserva_do_pedido(
    db: Session,
    pedido,
    produto_anterior: str,
    quantidade_anterior: int,
) -> None:
    produto_novo = pedido.produto
    quantidade_nova = int(pedido.quantidade or 0)

    if produto_anterior == produto_novo:
        delta = quantidade_nova - int(quantidade_anterior or 0)
        produto = get_produto_por_nome(db, produto_novo)
        if not produto or delta == 0:
            return
        if delta > 0:
            registrar_movimento(
                db,
                produto,
                "Reserva",
                delta,
                pedido_id=pedido.id,
                observacao=f"Ajuste de reserva do pedido #{pedido.id}",
            )
        else:
            registrar_movimento(
                db,
                produto,
                "Liberacao",
                abs(delta),
                pedido_id=pedido.id,
                observacao=f"Reducao de reserva do pedido #{pedido.id}",
            )
        return

    produto_antigo = get_produto_por_nome(db, produto_anterior)
    if produto_antigo:
        registrar_movimento(
            db,
            produto_antigo,
            "Liberacao",
            int(quantidade_anterior or 0),
            pedido_id=pedido.id,
            observacao=f"Liberacao por troca de produto no pedido #{pedido.id}",
        )

    reservar_estoque_para_pedido(db, pedido)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.produto import MovimentoEstoque, Produto


def itens_do_pedido(pedido) -> list:
    itens = list(getattr(pedido, "itens", None) or [])
    return itens or [pedido]


def quantidades_por_produto(pedido) -> dict[str, int]:
    totais: dict[str, int] = {}
    for item in itens_do_pedido(pedido):
        nome = str(item.produto or "")
        if nome:
            totais[nome] = totais.get(nome, 0) + int(item.quantidade or 0)
    return totais


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
    for nome, quantidade in quantidades_por_produto(pedido).items():
        produto = get_produto_por_nome(db, nome)
        if produto:
            registrar_movimento(
                db,
                produto,
                "Reserva",
                quantidade,
                pedido_id=pedido.id,
                observacao=f"Reserva automatica do pedido #{pedido.id}",
            )


def liberar_reserva_do_pedido(db: Session, pedido) -> None:
    for nome, quantidade in quantidades_por_produto(pedido).items():
        produto = get_produto_por_nome(db, nome)
        if produto:
            registrar_movimento(
                db,
                produto,
                "Liberacao",
                quantidade,
                pedido_id=pedido.id,
                observacao=f"Liberacao de reserva do pedido #{pedido.id}",
            )


def baixar_reserva_do_pedido(db: Session, pedido) -> None:
    for nome, quantidade in quantidades_por_produto(pedido).items():
        produto = get_produto_por_nome(db, nome)
        if produto:
            registrar_movimento(
                db,
                produto,
                "Baixa reserva",
                quantidade,
                pedido_id=pedido.id,
                observacao=f"Baixa de estoque ao finalizar pedido #{pedido.id}",
            )


def estornar_baixa_do_pedido(db: Session, pedido) -> None:
    """Desfaz a baixa da emissao: devolve a mercadoria ao saldo e recoloca a reserva."""
    for nome, quantidade in quantidades_por_produto(pedido).items():
        produto = get_produto_por_nome(db, nome)
        if not produto:
            continue
        registrar_movimento(
            db,
            produto,
            "Entrada",
            quantidade,
            pedido_id=pedido.id,
            observacao=f"Estorno da baixa por exclusao da nota do pedido #{pedido.id}",
        )
        registrar_movimento(
            db,
            produto,
            "Reserva",
            quantidade,
            pedido_id=pedido.id,
            observacao=f"Reserva restaurada por exclusao da nota do pedido #{pedido.id}",
        )


def recalcular_reservas_do_pedido(db: Session, pedido, quantidades_anteriores: dict[str, int]) -> None:
    quantidades_novas = quantidades_por_produto(pedido)
    for nome in set(quantidades_anteriores) | set(quantidades_novas):
        delta = quantidades_novas.get(nome, 0) - quantidades_anteriores.get(nome, 0)
        produto = get_produto_por_nome(db, nome)
        if not produto or delta == 0:
            continue
        registrar_movimento(
            db,
            produto,
            "Reserva" if delta > 0 else "Liberacao",
            abs(delta),
            pedido_id=pedido.id,
            observacao=f"Ajuste de reserva do pedido #{pedido.id}",
        )


def recalcular_reserva_do_pedido(
    db: Session,
    pedido,
    produto_anterior: str,
    quantidade_anterior: int,
) -> None:
    recalcular_reservas_do_pedido(db, pedido, {produto_anterior: int(quantidade_anterior or 0)})

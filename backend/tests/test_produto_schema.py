from datetime import datetime, timezone

from app.schemas.produto import ProdutoRead


def test_produto_read_accepts_negative_current_stock():
    produto = ProdutoRead(
        id=1,
        nome="5L M6",
        estoqueAtual=-1500,
        estoqueReservado=0,
        disponivel=0,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )

    assert produto.estoqueAtual == -1500

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.produto import Produto


PRODUTOS_INICIAIS = [
    "1L sem alça",
    "1L redondo",
    "1L oval",
    "1L agro",
    "1L dosador",
    "2L redondo",
    "2L quadrado",
    "3L",
    "5L M2",
    "5L M4",
    "5L M6",
    "5L M8",
    "20L",
    "25L",
    "Pote de soda 300g",
    "Pote de soda 500g",
    "Pote de soda 1kg",
    "Pote normal 500g",
]


def seed_produtos(db: Session) -> None:
    existentes = set(db.scalars(select(Produto.nome)).all())
    for nome in PRODUTOS_INICIAIS:
        if nome in existentes:
            continue
        db.add(
            Produto(
                nome=nome,
                categoria="Embalagem" if not nome.startswith("Pote") else "Pote",
                estoqueAtual=0,
                estoqueReservado=0,
                estoqueMinimo=0,
            )
        )
    db.commit()

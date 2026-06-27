from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (registra todos os models no metadata)
from app.db.session import Base
from app.models.cliente import Cliente
from app.models.preco_cliente import PrecoCliente
from app.models.produto import Produto
from app.services.precos import lookup_preco, upsert_preco


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_upsert_cria_e_atualiza_sem_duplicar():
    db = _make_session()
    cliente = Cliente(nome="Inter Blue", cnpj="123")
    produto = Produto(nome="5L M2")
    db.add_all([cliente, produto])
    db.commit()

    upsert_preco(db, cliente.id, produto.id, 10.5, 0.25)
    db.commit()

    achado = lookup_preco(db, cliente.id, produto.id)
    assert achado is not None
    assert float(achado.valor) == 10.5
    assert float(achado.valorTampa) == 0.25
    primeiro_id = achado.id

    # Reusar o mesmo par cliente/produto deve atualizar a linha, não criar outra.
    upsert_preco(db, cliente.id, produto.id, 12.0, 0.30)
    db.commit()

    atualizado = lookup_preco(db, cliente.id, produto.id)
    assert atualizado.id == primeiro_id
    assert float(atualizado.valor) == 12.0
    total = db.scalar(select(func.count()).select_from(PrecoCliente))
    assert total == 1


def test_lookup_inexistente_retorna_none():
    db = _make_session()
    assert lookup_preco(db, 999, 999) is None

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.db.session import Base
from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate
from app.services.seed import backfill_produto_atributos, derivar_atributos


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_deriva_litros_e_modelo():
    a = derivar_atributos("5L M2")
    assert a["capacidade"] == "5L"
    assert a["modelo"] == "M2"
    assert a["alca"] == "nao"


def test_deriva_sem_alca():
    a = derivar_atributos("1L sem alça")
    assert a["capacidade"] == "1L"
    assert a["alca"] == "nao"
    assert a["modelo"] == ""


def test_deriva_com_alca():
    a = derivar_atributos("2L redondo com alça")
    assert a["alca"] == "sim"
    assert a["capacidade"] == "2L"
    assert a["modelo"] == "redondo"


def test_deriva_pote_peso():
    a = derivar_atributos("Pote de soda 300g")
    assert a["peso"] == "300g"
    assert a["modelo"] == "soda"
    assert a["capacidade"] == ""


def test_backfill_nao_rebaixa_alca_manual():
    # Produto com alça setada à mão mas nome que não indica alça e sem estruturação.
    db = _make_session()
    produto = Produto(nome="5L balde", alca="sim")
    db.add(produto)
    db.commit()

    backfill_produto_atributos(db)

    db.refresh(produto)
    assert produto.capacidade == "5L"  # derivou o que faltava
    assert produto.modelo == "balde"
    assert produto.alca == "sim"  # e NÃO rebaixou a alça manual


def test_schema_produto_rejeita_alca_invalida():
    with pytest.raises(ValidationError):
        ProdutoCreate(nome="X", alca="talvez")

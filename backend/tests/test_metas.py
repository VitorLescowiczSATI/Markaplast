from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.db.session import Base
from app.models.meta import Meta
from app.services.metas import upsert_meta


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_upsert_meta_cria_e_atualiza_sem_duplicar():
    db = _make_session()
    upsert_meta(db, "empresa", "", "mensal", 100000)
    db.commit()
    upsert_meta(db, "empresa", "", "mensal", 120000)
    db.commit()

    metas = db.scalars(select(Meta)).all()
    assert len(metas) == 1
    assert float(metas[0].valor) == 120000


def test_meta_empresa_ignora_vendedor():
    db = _make_session()
    # escopo empresa deve zerar vendedor no upsert
    upsert_meta(db, "empresa", "Arthur", "diaria", 5000)
    db.commit()
    meta = db.scalar(select(Meta))
    assert meta.vendedor == ""
    total = db.scalar(select(func.count()).select_from(Meta))
    assert total == 1

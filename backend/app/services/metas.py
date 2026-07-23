from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.meta import Meta

PERIODOS_VALIDOS = {"diaria", "mensal", "trimestral"}
ESCOPOS_VALIDOS = {"empresa", "vendedor"}


def _lookup_meta(db: Session, escopo: str, vendedor: str, periodo: str) -> Meta | None:
    return db.scalars(
        select(Meta).where(Meta.escopo == escopo, Meta.vendedor == vendedor, Meta.periodo == periodo)
    ).first()


def upsert_meta(db: Session, escopo: str, vendedor: str, periodo: str, valor) -> Meta:
    vendedor = vendedor if escopo == "vendedor" else ""
    meta = _lookup_meta(db, escopo, vendedor, periodo)
    if not meta:
        meta = Meta(escopo=escopo, vendedor=vendedor, periodo=periodo)
        db.add(meta)
        try:
            db.flush()
        except IntegrityError:
            # Corrida no primeiro insert do mesmo (escopo, vendedor, periodo): atualiza a existente.
            db.rollback()
            meta = _lookup_meta(db, escopo, vendedor, periodo)
    meta.valor = valor
    return meta

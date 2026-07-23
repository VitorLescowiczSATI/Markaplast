from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.meta import Meta

PERIODOS_VALIDOS = {"diaria", "mensal", "trimestral"}
ESCOPOS_VALIDOS = {"empresa", "vendedor"}


def upsert_meta(db: Session, escopo: str, vendedor: str, periodo: str, valor) -> Meta:
    vendedor = vendedor if escopo == "vendedor" else ""
    meta = db.scalars(
        select(Meta).where(Meta.escopo == escopo, Meta.vendedor == vendedor, Meta.periodo == periodo)
    ).first()
    if not meta:
        meta = Meta(escopo=escopo, vendedor=vendedor, periodo=periodo)
        db.add(meta)
    meta.valor = valor
    return meta

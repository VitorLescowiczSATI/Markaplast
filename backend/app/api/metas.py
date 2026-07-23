from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.meta import Meta
from app.schemas.meta import MetaRead, MetaUpsert
from app.services.metas import ESCOPOS_VALIDOS, PERIODOS_VALIDOS, upsert_meta

router = APIRouter(prefix="/metas", tags=["metas"])


@router.get("", response_model=list[MetaRead])
def listar_metas(db: Session = Depends(get_db)):
    return db.scalars(select(Meta).order_by(Meta.escopo, Meta.vendedor, Meta.periodo)).all()


@router.post("", response_model=MetaRead, status_code=status.HTTP_201_CREATED)
def salvar_meta(payload: MetaUpsert, db: Session = Depends(get_db)):
    if payload.escopo not in ESCOPOS_VALIDOS:
        raise HTTPException(status_code=422, detail="Escopo invalido")
    if payload.periodo not in PERIODOS_VALIDOS:
        raise HTTPException(status_code=422, detail="Periodo invalido")
    if payload.escopo == "vendedor" and not payload.vendedor.strip():
        raise HTTPException(status_code=422, detail="Vendedor obrigatorio para meta por vendedor")
    meta = upsert_meta(db, payload.escopo, payload.vendedor, payload.periodo, payload.valor)
    db.commit()
    db.refresh(meta)
    return meta


@router.delete("/{meta_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_meta(meta_id: int, db: Session = Depends(get_db)):
    meta = db.get(Meta, meta_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Meta nao encontrada")
    db.delete(meta)
    db.commit()

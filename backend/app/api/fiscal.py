from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import get_settings
from app.models.nota_fiscal import NotaFiscalDraft
from app.models.pedido import Pedido
from app.schemas.fiscal import NotaFiscalRead, NotaFiscalUpdate
from app.services.fiscal import enviar_focus_nfe, montar_payload_nfe
from app.services.historico import registrar_historico
from app.services.regras import pode_transicionar_status

router = APIRouter(prefix="/fiscal", tags=["fiscal"])


@router.get("/notas", response_model=list[NotaFiscalRead])
def listar_notas(db: Session = Depends(get_db)):
    return db.scalars(select(NotaFiscalDraft).order_by(NotaFiscalDraft.id.desc())).all()


@router.post("/pedidos/{pedido_id}/preparar-nfe", response_model=NotaFiscalRead, status_code=status.HTTP_201_CREATED)
def preparar_nfe(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    referencia = f"PED-{pedido.id}"
    nota = db.scalars(select(NotaFiscalDraft).where(NotaFiscalDraft.referencia == referencia)).first()
    payload = montar_payload_nfe(pedido)
    if not nota:
        nota = NotaFiscalDraft(pedidoId=pedido.id, referencia=referencia, payload=payload)
        db.add(nota)
    else:
        nota.payload = payload

    nota.status = "Rascunho fiscal pronto"
    registrar_historico(
        db,
        pedido.id,
        "Fiscal",
        para_valor=nota.status,
        observacao="Pre-NF-e preparada para provedor fiscal.",
    )
    db.commit()
    db.refresh(nota)
    return nota


@router.patch("/notas/{nota_id}", response_model=NotaFiscalRead)
def atualizar_nota(nota_id: int, payload: NotaFiscalUpdate, db: Session = Depends(get_db)):
    nota = db.get(NotaFiscalDraft, nota_id)
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal nao encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(nota, key, value)
    db.commit()
    db.refresh(nota)
    return nota


@router.post("/notas/{nota_id}/marcar-emitida", response_model=NotaFiscalRead)
def marcar_emitida(nota_id: int, db: Session = Depends(get_db)):
    nota = db.get(NotaFiscalDraft, nota_id)
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal nao encontrada")
    pedido = db.get(Pedido, nota.pedidoId)
    nota.status = "Emitida manualmente"
    if pedido and pedido.status != "Nota emitida":
        if not pode_transicionar_status(pedido.status, "Nota emitida"):
            raise HTTPException(status_code=400, detail=f"Pedido em etapa invalida para emissao: {pedido.status}")
        anterior = pedido.status
        pedido.status = "Nota emitida"
        registrar_historico(db, pedido.id, "Status", anterior, pedido.status, observacao="Nota marcada como emitida no modulo fiscal.")
    db.commit()
    db.refresh(nota)
    return nota


@router.post("/notas/{nota_id}/enviar-homologacao", response_model=NotaFiscalRead)
async def enviar_homologacao(nota_id: int, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.fiscal_emit_enabled:
        raise HTTPException(
            status_code=400,
            detail="Envio fiscal desabilitado. Configure FISCAL_EMIT_ENABLED=true e FOCUS_NFE_TOKEN para usar homologacao.",
        )

    nota = db.get(NotaFiscalDraft, nota_id)
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal nao encontrada")
    try:
        retorno = await enviar_focus_nfe(settings.focus_nfe_base_url, settings.focus_nfe_token, nota.referencia, nota.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    nota.status = retorno.get("status", "Enviada para homologacao")
    nota.numero = str(retorno.get("numero", nota.numero or ""))
    nota.serie = str(retorno.get("serie", nota.serie or ""))
    nota.chaveAcesso = retorno.get("chave_nfe", nota.chaveAcesso or "")
    nota.xmlUrl = retorno.get("caminho_xml_nota_fiscal", nota.xmlUrl or "")
    nota.danfeUrl = retorno.get("caminho_danfe", nota.danfeUrl or "")
    db.commit()
    db.refresh(nota)
    return nota

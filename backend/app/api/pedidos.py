from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pedido import Pedido
from app.models.nota_fiscal import NotaFiscalDraft
from app.models.pedido_historico import PedidoHistorico
from app.schemas.pedido import (
    PedidoCreate,
    PedidoFinanceiroUpdate,
    PedidoRead,
    PedidoStatusUpdate,
    PedidoUpdate,
    ResumoRead,
)
from app.services.clientes import upsert_cliente_do_pedido
from app.services.estoque import baixar_reserva_do_pedido, liberar_reserva_do_pedido, reservar_estoque_para_pedido
from app.services.historico import registrar_historico
from app.services.regras import calcular_resumo, pedido_bate_busca, pode_ver_pedido_por_perfil

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.get("", response_model=list[PedidoRead])
def listar_pedidos(
    busca: str = "",
    status_filtro: str = Query("Todos", alias="status"),
    vendedor: str = "Todos",
    perfil: str = "Gestor",
    financeiro: str = "Todos",
    db: Session = Depends(get_db),
):
    pedidos = db.scalars(select(Pedido).order_by(Pedido.id.desc())).all()
    return [
        pedido
        for pedido in pedidos
        if pedido_bate_busca(pedido, busca)
        and (status_filtro == "Todos" or pedido.status == status_filtro)
        and (vendedor == "Todos" or pedido.vendedor == vendedor)
        and (financeiro == "Todos" or pedido.statusFinanceiro == financeiro)
        and pode_ver_pedido_por_perfil(perfil, pedido.status)
    ]


@router.get("/resumo", response_model=ResumoRead)
def resumo_pedidos(db: Session = Depends(get_db)):
    pedidos = db.scalars(select(Pedido)).all()
    return calcular_resumo(list(pedidos))


@router.post("", response_model=PedidoRead, status_code=status.HTTP_201_CREATED)
def criar_pedido(payload: PedidoCreate, db: Session = Depends(get_db)):
    upsert_cliente_do_pedido(db, payload)
    pedido = Pedido(
        **payload.model_dump(),
        status="Novo pedido",
        statusFinanceiro="Aguardando pagamento",
    )
    db.add(pedido)
    db.flush()
    reservar_estoque_para_pedido(db, pedido)
    registrar_historico(
        db,
        pedido.id,
        "Criacao",
        para_valor="Novo pedido",
        observacao="Pedido cadastrado pelo Comercial.",
    )
    db.commit()
    db.refresh(pedido)
    return pedido


@router.get("/{pedido_id}", response_model=PedidoRead)
def obter_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido


@router.patch("/{pedido_id}", response_model=PedidoRead)
def atualizar_pedido(pedido_id: int, payload: PedidoUpdate, db: Session = Depends(get_db)):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    dados = payload.model_dump(exclude_unset=True)
    for key, value in dados.items():
        setattr(pedido, key, value)

    if {"cliente", "cnpj", "cidade", "pagamento"} & set(dados.keys()):
        upsert_cliente_do_pedido(db, pedido)
    registrar_historico(db, pedido.id, "Edicao", observacao="Pedido atualizado.")
    db.commit()
    db.refresh(pedido)
    return pedido


@router.patch("/{pedido_id}/status", response_model=PedidoRead)
def atualizar_status(pedido_id: int, payload: PedidoStatusUpdate, db: Session = Depends(get_db)):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    status_anterior = pedido.status
    pedido.status = payload.status
    registrar_historico(db, pedido.id, "Status", status_anterior, payload.status)
    if payload.status == "Finalizado" and status_anterior != "Finalizado":
        baixar_reserva_do_pedido(db, pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


@router.patch("/{pedido_id}/financeiro", response_model=PedidoRead)
def atualizar_financeiro(pedido_id: int, payload: PedidoFinanceiroUpdate, db: Session = Depends(get_db)):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    status_anterior = pedido.statusFinanceiro
    pedido.statusFinanceiro = payload.statusFinanceiro
    registrar_historico(db, pedido.id, "Financeiro", status_anterior, payload.statusFinanceiro)
    db.commit()
    db.refresh(pedido)
    return pedido


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    liberar_reserva_do_pedido(db, pedido)
    db.execute(delete(NotaFiscalDraft).where(NotaFiscalDraft.pedidoId == pedido.id))
    db.execute(delete(PedidoHistorico).where(PedidoHistorico.pedidoId == pedido.id))
    db.delete(pedido)
    db.commit()

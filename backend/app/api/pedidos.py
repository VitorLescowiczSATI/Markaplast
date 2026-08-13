from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_profiles
from app.db.session import get_db
from app.models.pedido import Pedido, PedidoItem, hoje_brasil
from app.models.usuario import Usuario
from app.schemas.pedido import (
    PedidoCreate,
    PedidoFinanceiroUpdate,
    PedidoRead,
    PedidoStatusUpdate,
    PedidoUpdate,
    ResumoRead,
)
from app.services.clientes import upsert_cliente_do_pedido
from app.services.estoque import (
    baixar_reserva_do_pedido,
    quantidades_por_produto,
    liberar_reserva_do_pedido,
    recalcular_reservas_do_pedido,
    reservar_estoque_para_pedido,
)
from app.services.fiscal import excluir_nota_do_pedido, reverter_baixa_da_emissao
from app.services.historico import registrar_historico
from app.services.regras import (
    STATUS_CANCELADO,
    STATUS_COM_RESERVA,
    STATUS_FATURADO,
    STATUS_FINANCEIRO_VALIDOS,
    calcular_resumo,
    pedido_bate_busca,
    pode_transicionar_status,
    pode_ver_pedido_por_perfil,
)

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.get("", response_model=list[PedidoRead])
def listar_pedidos(
    busca: str = "",
    status_filtro: str = Query("Todos", alias="status"),
    vendedor: str = "Todos",
    financeiro: str = "Todos",
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_profiles("Inteligência", "Comercial", "PCP", "Logística", "Faturamento", "Financeiro", "Fiscal")
    ),
):
    pedidos = db.scalars(select(Pedido).options(selectinload(Pedido.itens)).order_by(Pedido.id.desc())).all()
    return [
        pedido
        for pedido in pedidos
        if pedido_bate_busca(pedido, busca)
        and (status_filtro == "Todos" or pedido.status == status_filtro)
        and (vendedor == "Todos" or pedido.vendedor == vendedor)
        and (financeiro == "Todos" or pedido.statusFinanceiro == financeiro)
        and pode_ver_pedido_por_perfil(usuario.perfil, pedido.status)
    ]


@router.get("/resumo", response_model=ResumoRead)
def resumo_pedidos(db: Session = Depends(get_db), _usuario=Depends(require_profiles("Inteligência"))):
    pedidos = db.scalars(select(Pedido).options(selectinload(Pedido.itens))).all()
    return calcular_resumo(list(pedidos))


@router.post("", response_model=PedidoRead, status_code=status.HTTP_201_CREATED)
def criar_pedido(payload: PedidoCreate, db: Session = Depends(get_db), _usuario=Depends(require_profiles("Comercial"))):
    upsert_cliente_do_pedido(db, payload)
    itens_payload = payload.itens or [
        {
            "produto": payload.produto,
            "tampa": payload.tampa,
            "cor": payload.cor,
            "quantidade": payload.quantidade,
            "valor": payload.valor,
            "valorTampa": payload.valorTampa,
        }
    ]
    itens_dados = [item.model_dump() if hasattr(item, "model_dump") else item for item in itens_payload]
    primeiro_item = itens_dados[0]
    dados_pedido = payload.model_dump(exclude={"itens"})
    dados_pedido.update(primeiro_item)
    pedido = Pedido(
        **dados_pedido,
        status="Novo pedido",
        statusFinanceiro="Aguardando pagamento",
    )
    db.add(pedido)
    db.flush()
    pedido.itens = [PedidoItem(ordem=ordem, **item) for ordem, item in enumerate(itens_dados)]
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
def obter_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_profiles("Inteligência", "Comercial", "PCP", "Logística", "Faturamento", "Financeiro", "Fiscal")
    ),
):
    pedido = db.scalar(select(Pedido).options(selectinload(Pedido.itens)).where(Pedido.id == pedido_id))
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not pode_ver_pedido_por_perfil(usuario.perfil, pedido.status):
        raise HTTPException(status_code=403, detail="Seu perfil não pode acessar este pedido")
    return pedido


@router.patch("/{pedido_id}", response_model=PedidoRead)
def atualizar_pedido(
    pedido_id: int,
    payload: PedidoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_profiles("PCP")),
):
    pedido = db.scalar(select(Pedido).options(selectinload(Pedido.itens)).where(Pedido.id == pedido_id))
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not pode_ver_pedido_por_perfil(usuario.perfil, pedido.status):
        raise HTTPException(status_code=403, detail="Seu perfil não pode alterar este pedido")

    dados = payload.model_dump(exclude_unset=True)
    quantidades_anteriores = quantidades_por_produto(pedido)
    status_anterior = pedido.status

    if "status" in dados and not pode_transicionar_status(pedido.status, dados["status"]):
        raise HTTPException(status_code=400, detail=f"Transicao de status invalida: {pedido.status} -> {dados['status']}")
    if "statusFinanceiro" in dados and dados["statusFinanceiro"] not in STATUS_FINANCEIRO_VALIDOS:
        raise HTTPException(status_code=400, detail="Status financeiro invalido")
    if pedido.status in STATUS_FATURADO | {STATUS_CANCELADO} and {"produto", "quantidade", "itens"} & set(dados):
        raise HTTPException(status_code=409, detail="Itens do pedido nao podem ser alterados nesta etapa")

    itens_novos = dados.pop("itens", None)
    if itens_novos is not None:
        if not itens_novos:
            raise HTTPException(status_code=400, detail="O pedido precisa ter pelo menos um item")
        primeiro_item = itens_novos[0]
        dados.update(primeiro_item)

    for key, value in dados.items():
        setattr(pedido, key, value)
    if itens_novos is not None:
        pedido.itens = [PedidoItem(ordem=ordem, **item) for ordem, item in enumerate(itens_novos)]
        db.flush()

    if {"cliente", "cnpj", "cidade", "pagamento"} & set(dados.keys()):
        upsert_cliente_do_pedido(db, pedido)
    if pedido.status in STATUS_COM_RESERVA and ({"produto", "quantidade"} & set(dados.keys()) or itens_novos is not None):
        recalcular_reservas_do_pedido(db, pedido, quantidades_anteriores)
    if "status" in dados and pedido.status != status_anterior:
        registrar_historico(db, pedido.id, "Status", status_anterior, pedido.status)
        if pedido.status == "Nota emitida" and not pedido.dataEmissao:
            # Faturou: estampa a emissão e dá baixa na reserva (mercadoria saiu ao faturar).
            pedido.dataEmissao = hoje_brasil()
            baixar_reserva_do_pedido(db, pedido)
        elif status_anterior == "Nota emitida":
            # Saiu da emissão: devolve a mercadoria ao saldo e recoloca a reserva.
            reverter_baixa_da_emissao(db, pedido)
        elif pedido.status == STATUS_CANCELADO and status_anterior in STATUS_COM_RESERVA:
            liberar_reserva_do_pedido(db, pedido)
    registrar_historico(db, pedido.id, "Edicao", observacao="Pedido atualizado.")
    db.commit()
    db.refresh(pedido)
    return pedido


@router.patch("/{pedido_id}/status", response_model=PedidoRead)
def atualizar_status(
    pedido_id: int,
    payload: PedidoStatusUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_profiles("PCP", "Logística", "Faturamento")),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not pode_ver_pedido_por_perfil(usuario.perfil, pedido.status):
        raise HTTPException(status_code=403, detail="Seu perfil não pode alterar este pedido")
    if not pode_transicionar_status(pedido.status, payload.status):
        raise HTTPException(status_code=400, detail=f"Transicao de status invalida: {pedido.status} -> {payload.status}")
    status_anterior = pedido.status
    if payload.status == status_anterior:
        return pedido
    pedido.status = payload.status
    registrar_historico(db, pedido.id, "Status", status_anterior, payload.status)
    if payload.status == "Nota emitida" and not pedido.dataEmissao:
        pedido.dataEmissao = hoje_brasil()
        baixar_reserva_do_pedido(db, pedido)
    elif status_anterior == "Nota emitida":
        reverter_baixa_da_emissao(db, pedido)
    elif payload.status == STATUS_CANCELADO and status_anterior in STATUS_COM_RESERVA:
        liberar_reserva_do_pedido(db, pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


@router.patch("/{pedido_id}/financeiro", response_model=PedidoRead)
def atualizar_financeiro(
    pedido_id: int,
    payload: PedidoFinanceiroUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_profiles("Financeiro")),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not pode_ver_pedido_por_perfil(usuario.perfil, pedido.status):
        raise HTTPException(status_code=403, detail="Seu perfil não pode alterar este pedido")
    if payload.statusFinanceiro not in STATUS_FINANCEIRO_VALIDOS:
        raise HTTPException(status_code=400, detail="Status financeiro invalido")
    status_anterior = pedido.statusFinanceiro
    pedido.statusFinanceiro = payload.statusFinanceiro
    registrar_historico(db, pedido.id, "Financeiro", status_anterior, payload.statusFinanceiro)
    db.commit()
    db.refresh(pedido)
    return pedido


@router.delete("/{pedido_id}/nota", status_code=status.HTTP_204_NO_CONTENT)
def excluir_nota_emitida(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_profiles("Faturamento", "Fiscal")),
):
    pedido = db.scalar(select(Pedido).options(selectinload(Pedido.itens)).where(Pedido.id == pedido_id))
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status != "Nota emitida":
        raise HTTPException(status_code=409, detail=f"Pedido não tem nota emitida para excluir (status atual: {pedido.status})")
    if not pode_ver_pedido_por_perfil(usuario.perfil, pedido.status):
        raise HTTPException(status_code=403, detail="Seu perfil não pode alterar este pedido")
    excluir_nota_do_pedido(db, pedido, "faturamento")
    db.commit()
    return None


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_profiles("Comercial", "PCP")),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if pedido.status in STATUS_FATURADO:
        raise HTTPException(status_code=409, detail="Pedido faturado ou em entrega deve ser cancelado pelo fluxo fiscal/logistico")
    if pedido.status == STATUS_CANCELADO:
        return None
    liberar_reserva_do_pedido(db, pedido)
    status_anterior = pedido.status
    pedido.status = STATUS_CANCELADO
    registrar_historico(db, pedido.id, "Cancelamento", status_anterior, STATUS_CANCELADO, observacao="Pedido cancelado pela operacao.")
    db.commit()

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.carga import Carga
from app.models.pedido import Pedido
from app.models.produto import Produto
from app.schemas.dashboard import AlertaRead, DashboardItem, DashboardRead
from app.services.regras import calcular_resumo, valor_total_pedido

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def idade_dias(created_at) -> int:
    if not created_at:
        return 0
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - created_at).days)


def montar_alertas(pedidos: list[Pedido], produtos: list[Produto], cargas: list[Carga]) -> list[AlertaRead]:
    alertas: list[AlertaRead] = []
    for produto in produtos:
        disponivel = produto.disponivel
        if disponivel <= int(produto.estoqueMinimo or 0):
            alertas.append(
                AlertaRead(
                    tipo="estoque",
                    prioridade="alta" if disponivel <= 0 else "media",
                    titulo=f"Estoque critico: {produto.nome}",
                    detalhe=f"Disponivel {disponivel} {produto.unidade}; minimo {produto.estoqueMinimo}.",
                    entidadeId=produto.id,
                )
            )

    for pedido in pedidos:
        dias = idade_dias(pedido.createdAt)
        if pedido.status == "Nota emitida" and pedido.statusFinanceiro != "Pago":
            alertas.append(
                AlertaRead(
                    tipo="financeiro",
                    prioridade="alta" if dias >= 7 else "media",
                    titulo=f"Pagamento pendente no pedido #{pedido.id}",
                    detalhe=f"{pedido.cliente} tem NF emitida e pagamento {pedido.statusFinanceiro}.",
                    entidadeId=pedido.id,
                )
            )
        if pedido.status == "Pronto para faturar" and dias >= 1:
            alertas.append(
                AlertaRead(
                    tipo="faturamento",
                    prioridade="media",
                    titulo=f"Pedido #{pedido.id} pronto para faturar",
                    detalhe=f"{pedido.cliente} esta aguardando faturamento ha {dias} dia(s).",
                    entidadeId=pedido.id,
                )
            )
        if pedido.status in {"Novo pedido", "Vai produzir", "Em produção"} and dias >= 3:
            alertas.append(
                AlertaRead(
                    tipo="pcp",
                    prioridade="media",
                    titulo=f"Pedido #{pedido.id} parado na producao",
                    detalhe=f"{pedido.cliente} esta em {pedido.status} ha {dias} dia(s).",
                    entidadeId=pedido.id,
                )
            )

    for carga in cargas:
        if not carga.motorista or not carga.placa:
            alertas.append(
                AlertaRead(
                    tipo="logistica",
                    prioridade="baixa",
                    titulo=f"Carga #{carga.id} incompleta",
                    detalhe=f"Rota {carga.regiao} sem motorista ou placa preenchidos.",
                    entidadeId=carga.id,
                )
            )

    prioridade_ordem = {"alta": 0, "media": 1, "baixa": 2}
    return sorted(alertas, key=lambda alerta: prioridade_ordem.get(alerta.prioridade, 9))[:30]


@router.get("", response_model=DashboardRead)
def dashboard(db: Session = Depends(get_db)):
    pedidos = db.scalars(select(Pedido)).all()
    produtos = db.scalars(select(Produto)).all()
    cargas = db.scalars(select(Carga)).all()

    por_status = [
        DashboardItem(label=status, valor=sum(1 for pedido in pedidos if pedido.status == status))
        for status in sorted({pedido.status for pedido in pedidos})
    ]

    vendedores = sorted({pedido.vendedor or "Nao informado" for pedido in pedidos})
    por_vendedor = [
        DashboardItem(
            label=vendedor,
            quantidade=sum(1 for pedido in pedidos if (pedido.vendedor or "Nao informado") == vendedor),
            valor=sum(valor_total_pedido(pedido) for pedido in pedidos if (pedido.vendedor or "Nao informado") == vendedor),
        )
        for vendedor in vendedores
    ]

    produtos_nomes = sorted({pedido.produto or "Nao informado" for pedido in pedidos})
    por_produto = [
        DashboardItem(
            label=produto,
            quantidade=sum(int(pedido.quantidade or 0) for pedido in pedidos if (pedido.produto or "Nao informado") == produto),
            valor=sum(valor_total_pedido(pedido) for pedido in pedidos if (pedido.produto or "Nao informado") == produto),
        )
        for produto in produtos_nomes
    ]
    por_produto.sort(key=lambda item: item.valor, reverse=True)

    estoque_critico = [
        {
            "id": produto.id,
            "nome": produto.nome,
            "estoqueAtual": produto.estoqueAtual,
            "estoqueReservado": produto.estoqueReservado,
            "disponivel": produto.disponivel,
            "estoqueMinimo": produto.estoqueMinimo,
        }
        for produto in produtos
        if produto.disponivel <= int(produto.estoqueMinimo or 0)
    ]

    return DashboardRead(
        resumo=calcular_resumo(list(pedidos)),
        porStatus=por_status,
        porVendedor=sorted(por_vendedor, key=lambda item: item.valor, reverse=True),
        porProduto=por_produto[:10],
        estoqueCritico=estoque_critico,
        alertas=montar_alertas(list(pedidos), list(produtos), list(cargas)),
    )

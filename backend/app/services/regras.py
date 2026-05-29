from app.models.pedido import Pedido


def valor_total_pedido(pedido: Pedido) -> float:
    valor = float(pedido.valor or 0)
    valor_tampa = float(pedido.valorTampa or 0)
    quantidade = int(pedido.quantidade or 0)
    return (valor + valor_tampa) * quantidade


def pode_ver_pedido_por_perfil(perfil: str, status: str) -> bool:
    if perfil in {"Gestor", "Comercial"}:
        return True
    if perfil == "Financeiro":
        return status == "Nota emitida"
    if perfil == "PCP/Logística":
        return status in {"Novo pedido", "Pago", "Vai produzir", "Em produção", "Pronto para faturar"}
    if perfil == "Faturamento":
        return status in {"Pronto para faturar", "Nota emitida"}
    if perfil == "Logística":
        return status in {"Nota emitida", "Separado para entrega", "Enviado", "Finalizado"}
    return False


def calcular_resumo(pedidos: list[Pedido]) -> dict:
    return {
        "totalPedidos": len(pedidos),
        "novos": sum(1 for p in pedidos if p.status == "Novo pedido"),
        "aguardando": sum(1 for p in pedidos if p.status == "Aguardando pagamento"),
        "vaiProduzir": sum(1 for p in pedidos if p.status == "Vai produzir"),
        "producao": sum(1 for p in pedidos if p.status == "Em produção"),
        "faturar": sum(1 for p in pedidos if p.status == "Pronto para faturar"),
        "notasEmitidas": sum(1 for p in pedidos if p.status == "Nota emitida"),
        "financeiroPago": sum(1 for p in pedidos if p.status == "Nota emitida" and p.statusFinanceiro == "Pago"),
        "financeiroPendente": sum(1 for p in pedidos if p.status == "Nota emitida" and p.statusFinanceiro != "Pago"),
        "total": sum(valor_total_pedido(p) for p in pedidos),
    }


def pedido_bate_busca(pedido: Pedido, busca: str) -> bool:
    termo = (busca or "").strip().lower()
    if not termo:
        return True
    texto = " ".join(
        str(item or "")
        for item in [
            pedido.id,
            pedido.cliente,
            pedido.cnpj,
            pedido.cep,
            pedido.logradouro,
            pedido.numero,
            pedido.bairro,
            pedido.cidade,
            pedido.uf,
            pedido.produto,
            pedido.tampa,
            pedido.cor,
            pedido.status,
            pedido.pagamento,
            pedido.statusFinanceiro,
            pedido.transporte,
            pedido.tipoFrete,
            pedido.detalheFOB,
            pedido.faturamento,
            pedido.tipoEntrega,
            pedido.pcpPrevisaoProducao,
            pedido.pcpPrevisaoPronto,
            pedido.pcpQuantidadeProduzida,
            pedido.pcpObservacoes,
        ]
    ).lower()
    return termo in texto

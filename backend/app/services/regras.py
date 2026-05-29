from app.models.pedido import Pedido


STATUS_CANCELADO = "Cancelado"
STATUS_ATIVOS = {
    "Novo pedido",
    "Aguardando pagamento",
    "Pago",
    "Vai produzir",
    "Em produção",
    "Pronto para faturar",
    "Nota emitida",
    "Separado para entrega",
    "Enviado",
    "Finalizado",
}
STATUS_VALIDOS = STATUS_ATIVOS | {STATUS_CANCELADO}
STATUS_COM_RESERVA = {
    "Novo pedido",
    "Aguardando pagamento",
    "Pago",
    "Vai produzir",
    "Em produção",
    "Pronto para faturar",
    "Nota emitida",
    "Separado para entrega",
    "Enviado",
}
STATUS_TRANSICOES = {
    "Novo pedido": {"Aguardando pagamento", "Pago", "Vai produzir", "Em produção", "Pronto para faturar", STATUS_CANCELADO},
    "Aguardando pagamento": {"Pago", "Vai produzir", STATUS_CANCELADO},
    "Pago": {"Vai produzir", STATUS_CANCELADO},
    "Vai produzir": {"Novo pedido", "Em produção", "Pronto para faturar", STATUS_CANCELADO},
    "Em produção": {"Novo pedido", "Vai produzir", "Pronto para faturar", STATUS_CANCELADO},
    "Pronto para faturar": {"Em produção", "Nota emitida", STATUS_CANCELADO},
    "Nota emitida": {"Separado para entrega"},
    "Separado para entrega": {"Nota emitida", "Enviado"},
    "Enviado": {"Separado para entrega", "Finalizado"},
    "Finalizado": set(),
    STATUS_CANCELADO: set(),
}
STATUS_FINANCEIRO_VALIDOS = {"Aguardando pagamento", "Pago"}


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


def pedido_ativo(pedido: Pedido) -> bool:
    return pedido.status != STATUS_CANCELADO


def pode_transicionar_status(status_atual: str, novo_status: str) -> bool:
    if novo_status not in STATUS_VALIDOS:
        return False
    if status_atual == novo_status:
        return True
    return novo_status in STATUS_TRANSICOES.get(status_atual, set())


def calcular_resumo(pedidos: list[Pedido]) -> dict:
    pedidos_ativos = [pedido for pedido in pedidos if pedido_ativo(pedido)]
    return {
        "totalPedidos": len(pedidos_ativos),
        "novos": sum(1 for p in pedidos_ativos if p.status == "Novo pedido"),
        "aguardando": sum(1 for p in pedidos_ativos if p.status == "Aguardando pagamento"),
        "vaiProduzir": sum(1 for p in pedidos_ativos if p.status == "Vai produzir"),
        "producao": sum(1 for p in pedidos_ativos if p.status == "Em produção"),
        "faturar": sum(1 for p in pedidos_ativos if p.status == "Pronto para faturar"),
        "notasEmitidas": sum(1 for p in pedidos_ativos if p.status == "Nota emitida"),
        "financeiroPago": sum(1 for p in pedidos_ativos if p.status == "Nota emitida" and p.statusFinanceiro == "Pago"),
        "financeiroPendente": sum(1 for p in pedidos_ativos if p.status == "Nota emitida" and p.statusFinanceiro != "Pago"),
        "cancelados": sum(1 for p in pedidos if p.status == STATUS_CANCELADO),
        "total": sum(valor_total_pedido(p) for p in pedidos_ativos),
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

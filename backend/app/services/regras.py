from app.models.pedido import Pedido
from app.services.estoque import itens_do_pedido


STATUS_CANCELADO = "Cancelado"

# Status legados aceitos por 1 release (removidos quando produção zerar as linhas antigas).
STATUS_LEGADOS = {"Vai produzir", "Pronto para faturar", "Separado para entrega", "Enviado", "Finalizado"}

STATUS_ATIVOS = {
    "Novo pedido",
    "Aguardando pagamento",
    "Pago",
    "A produzir",
    "Em produção",
    "Prontos",
    "Pronto para retirada",
    "Pronto para o envio",
    "Nota emitida",
} | STATUS_LEGADOS
STATUS_VALIDOS = STATUS_ATIVOS | {STATUS_CANCELADO}

# Pedido faturado (nota emitida) ou em trilha de entrega legada: bloqueia edição de produto/qtd e exclusão.
STATUS_FATURADO = {"Nota emitida", "Separado para entrega", "Enviado", "Finalizado"}

# A reserva de estoque fica retida até a emissão da nota; a baixa ocorre ao entrar em "Nota emitida".
STATUS_COM_RESERVA = {
    "Novo pedido",
    "Aguardando pagamento",
    "Pago",
    "A produzir",
    "Em produção",
    "Prontos",
    "Pronto para retirada",
    "Pronto para o envio",
    "Vai produzir",
    "Pronto para faturar",
}
STATUS_TRANSICOES = {
    "Novo pedido": {"Aguardando pagamento", "Pago", "A produzir", "Em produção", "Prontos", STATUS_CANCELADO},
    "Aguardando pagamento": {"Pago", "A produzir", STATUS_CANCELADO},
    "Pago": {"A produzir", STATUS_CANCELADO},
    "A produzir": {"Novo pedido", "Em produção", "Prontos", STATUS_CANCELADO},
    "Em produção": {"Novo pedido", "A produzir", "Prontos", STATUS_CANCELADO},
    "Prontos": {"Em produção", "Pronto para retirada", "Pronto para o envio", STATUS_CANCELADO},
    "Pronto para retirada": {"Prontos", "Nota emitida", STATUS_CANCELADO},
    "Pronto para o envio": {"Prontos", "Nota emitida", STATUS_CANCELADO},
    # Pos-emissao: volta para a fila de onde saiu ou cancela (a baixa de estoque e desfeita junto).
    "Nota emitida": {"Prontos", "Pronto para retirada", "Pronto para o envio", STATUS_CANCELADO},
    STATUS_CANCELADO: set(),
    # --- aliases legados aceitos por 1 release ---
    "Vai produzir": {"Novo pedido", "A produzir", "Em produção", "Prontos", STATUS_CANCELADO},
    "Pronto para faturar": {"Em produção", "Prontos", "Pronto para retirada", "Pronto para o envio", "Nota emitida", STATUS_CANCELADO},
    "Separado para entrega": {"Nota emitida"},
    "Enviado": {"Nota emitida"},
    "Finalizado": set(),
}
STATUS_FINANCEIRO_VALIDOS = {"Aguardando pagamento", "Pago"}


def valor_total_pedido(pedido: Pedido) -> float:
    return sum(
        (float(item.valor or 0) + float(item.valorTampa or 0)) * int(item.quantidade or 0)
        for item in itens_do_pedido(pedido)
    )


def pode_ver_pedido_por_perfil(perfil: str, status: str) -> bool:
    if perfil in {"Administrador", "Gestor", "Inteligência", "Comercial"}:
        return True
    if perfil == "Financeiro":
        return status == "Nota emitida"
    if perfil in {"PCP", "PCP/Logística"}:  # aceita o nome antigo do perfil por 1 release
        return status in {"Novo pedido", "Pago", "A produzir", "Em produção", "Prontos", "Vai produzir", "Pronto para faturar"}
    if perfil == "Faturamento":
        return status in {"Pronto para retirada", "Pronto para o envio", "Nota emitida", "Pronto para faturar"}
    if perfil == "Logística":
        return status in {"Prontos", "Pronto para retirada", "Pronto para o envio", "Separado para entrega", "Enviado", "Finalizado"}
    if perfil == "Fiscal":
        return status in {"Pronto para retirada", "Pronto para o envio", "Nota emitida"}
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
        "vaiProduzir": sum(1 for p in pedidos_ativos if p.status in {"A produzir", "Vai produzir"}),
        "producao": sum(1 for p in pedidos_ativos if p.status == "Em produção"),
        "faturar": sum(1 for p in pedidos_ativos if p.status in {"Pronto para retirada", "Pronto para o envio", "Pronto para faturar"}),
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
    texto_itens = " ".join(
        f"{item.produto or ''} {item.tampa or ''} {item.cor or ''} {item.quantidade or ''}"
        for item in itens_do_pedido(pedido)
    )
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
            texto_itens,
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

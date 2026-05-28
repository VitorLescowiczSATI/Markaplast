from types import SimpleNamespace

from app.services.regras import calcular_resumo, pode_ver_pedido_por_perfil, valor_total_pedido


def pedido(**kwargs):
    base = {
        "valor": 10,
        "valorTampa": 5,
        "quantidade": 2,
        "status": "Novo pedido",
        "statusFinanceiro": "Aguardando pagamento",
    }
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_valor_total_pedido_soma_embalagem_e_tampa_por_quantidade():
    assert valor_total_pedido(pedido()) == 30


def test_permissoes_por_perfil():
    assert pode_ver_pedido_por_perfil("PCP/Logística", "Novo pedido") is True
    assert pode_ver_pedido_por_perfil("PCP/Logística", "Aguardando pagamento") is False
    assert pode_ver_pedido_por_perfil("Financeiro", "Nota emitida") is True


def test_calcular_resumo():
    resumo = calcular_resumo(
        [
            pedido(status="Novo pedido"),
            pedido(status="Nota emitida", statusFinanceiro="Pago"),
            pedido(status="Nota emitida", statusFinanceiro="Aguardando pagamento"),
        ]
    )

    assert resumo["novos"] == 1
    assert resumo["notasEmitidas"] == 2
    assert resumo["financeiroPago"] == 1
    assert resumo["financeiroPendente"] == 1
    assert resumo["total"] == 90

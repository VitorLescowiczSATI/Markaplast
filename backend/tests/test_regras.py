from types import SimpleNamespace

from app.services.regras import calcular_resumo, pode_transicionar_status, pode_ver_pedido_por_perfil, valor_total_pedido


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
    assert pode_ver_pedido_por_perfil("PCP", "A produzir") is True
    assert pode_ver_pedido_por_perfil("PCP", "Aguardando pagamento") is False
    assert pode_ver_pedido_por_perfil("Financeiro", "Nota emitida") is True
    assert pode_ver_pedido_por_perfil("Logística", "Pronto para o envio") is True
    assert pode_ver_pedido_por_perfil("Faturamento", "Pronto para retirada") is True
    assert pode_ver_pedido_por_perfil("Fiscal", "Nota emitida") is True
    assert pode_ver_pedido_por_perfil("Fiscal", "Em produção") is False
    assert pode_ver_pedido_por_perfil("Inteligência", "Em produção") is True
    # nome antigo do perfil ainda aceito por 1 release
    assert pode_ver_pedido_por_perfil("PCP/Logística", "A produzir") is True


def test_calcular_resumo():
    resumo = calcular_resumo(
        [
            pedido(status="Novo pedido"),
            pedido(status="Cancelado"),
            pedido(status="Nota emitida", statusFinanceiro="Pago"),
            pedido(status="Nota emitida", statusFinanceiro="Aguardando pagamento"),
        ]
    )

    assert resumo["novos"] == 1
    assert resumo["notasEmitidas"] == 2
    assert resumo["financeiroPago"] == 1
    assert resumo["financeiroPendente"] == 1
    assert resumo["cancelados"] == 1
    assert resumo["total"] == 90


def test_transicoes_de_status_basicas():
    assert pode_transicionar_status("Novo pedido", "A produzir") is True
    assert pode_transicionar_status("Prontos", "Pronto para retirada") is True
    assert pode_transicionar_status("Prontos", "Pronto para o envio") is True
    assert pode_transicionar_status("Pronto para retirada", "Nota emitida") is True
    assert pode_transicionar_status("Pronto para o envio", "Nota emitida") is True
    assert pode_transicionar_status("Nota emitida", "Prontos") is True
    assert pode_transicionar_status("Nota emitida", "Finalizado") is False
    assert pode_transicionar_status("Cancelado", "Novo pedido") is False
    # aliases legados ainda aceitos por 1 release
    assert pode_transicionar_status("Vai produzir", "A produzir") is True
    assert pode_transicionar_status("Pronto para faturar", "Nota emitida") is True

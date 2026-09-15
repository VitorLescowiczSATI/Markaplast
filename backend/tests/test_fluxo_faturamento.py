import pytest
from sqlalchemy import select
from test_exclusao_nota import montar_app, logar, criar_pedido_faturado
from app.models.produto import Produto
from app.models.usuario import Usuario
from app.services.auth import hash_senha
from app.models.pedido_historico import PedidoHistorico


def preparar_app():
    client, sessions = montar_app()
    with sessions() as db:
        db.add(Usuario(nome="Operador Logística", username="logistica", perfil="Logística", senhaHash=hash_senha("Senha@123")))
        db.commit()
    return client, sessions


@pytest.mark.parametrize("usuario", ["pcp", "logistica"])
def test_quantidade_editavel_com_reserva_e_historico(usuario):
    client, sessions = preparar_app()
    pedido_id = criar_pedido_faturado(client)
    headers = logar(client, usuario)
    r = client.patch(f"/api/pedidos/{pedido_id}", headers=headers, json={"itens": [
        {"produto": "5L", "quantidade": 55, "valor": 3, "valorTampa": 0.5}
    ]})
    assert r.status_code == 200, r.text
    assert r.json()["itens"][0]["quantidade"] == 55
    with sessions() as db:
        assert db.scalar(select(Produto)).estoqueReservado == 55
        h = db.scalar(select(PedidoHistorico).where(PedidoHistorico.tipo == "Quantidade"))
        assert h.usuario == usuario
        assert "40" in h.deValor and "55" in h.paraValor


def test_emissao_exige_numero_persiste_baixa_uma_vez_e_bloqueia_edicao():
    client, sessions = preparar_app()
    pedido_id = criar_pedido_faturado(client)
    headers = logar(client, "faturamento")
    url = f"/api/pedidos/{pedido_id}/status"
    for numero in [None, "", "   "]:
        r = client.patch(url, headers=headers, json={"status": "Nota emitida", "numeroNota": numero})
        assert r.status_code == 400
    with sessions() as db:
        assert db.scalar(select(Produto)).estoqueAtual == 1000
    for _ in range(2):
        r = client.patch(url, headers=headers, json={"status": "Nota emitida", "numeroNota": " 000123 "})
        assert r.status_code == 200, r.text
        assert r.json()["numeroNota"] == "000123"
    with sessions() as db:
        assert db.scalar(select(Produto)).estoqueAtual == 960
        assert db.scalar(select(Produto)).estoqueReservado == 0
    logistica = logar(client, "logistica")
    assert any(p["id"] == pedido_id for p in client.get("/api/pedidos", headers=logistica).json())
    assert client.patch(f"/api/pedidos/{pedido_id}", headers=logistica, json={"quantidade": 90}).status_code == 409
    r = client.patch(url, headers=headers, json={"status": "Pronto para retirada"})
    assert r.status_code == 200
    assert r.json()["numeroNota"] == ""
    with sessions() as db:
        assert db.scalar(select(Produto)).estoqueAtual == 1000
        assert db.scalar(select(Produto)).estoqueReservado == 40


def test_edicao_nao_permite_pular_numero_da_nota():
    client, _ = montar_app()
    pedido_id = criar_pedido_faturado(client)
    r = client.patch(f"/api/pedidos/{pedido_id}", headers=logar(client, "admin"), json={"status": "Nota emitida"})
    assert r.status_code == 400

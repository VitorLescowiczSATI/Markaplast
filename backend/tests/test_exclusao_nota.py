from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth as auth_api
from app.api import fiscal as fiscal_api
from app.api import pedidos as pedidos_api
from app.db.session import Base, get_db
from app.models.nota_fiscal import NotaFiscalDraft
from app.models.pedido import Pedido
from app.models.produto import Produto
from app.services.auth import seed_usuarios


def montar_app():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSession() as db:
        db.add(Produto(nome="5L", estoqueAtual=1000))
        seed_usuarios(db, "Senha@123")
        db.commit()

    app = FastAPI()
    app.include_router(auth_api.router, prefix="/api")
    app.include_router(pedidos_api.router, prefix="/api")
    app.include_router(fiscal_api.router, prefix="/api")

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), TestingSession


def logar(client: TestClient, username: str) -> dict:
    login = client.post("/api/auth/login", json={"username": username, "senha": "Senha@123"})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['accessToken']}"}


def criar_pedido_faturado(client: TestClient) -> int:
    comercial = logar(client, "comercial")
    criado = client.post(
        "/api/pedidos",
        headers=comercial,
        json={
            "cliente": "Cliente Teste",
            "produto": "5L",
            "quantidade": 40,
            "valor": 3,
            "vendedor": "Arthur",
            "tipoEntrega": "Retirada",
        },
    )
    assert criado.status_code == 201, criado.text
    pedido_id = criado.json()["id"]

    pcp = logar(client, "pcp")
    for status_novo in ["A produzir", "Em produção", "Prontos"]:
        avanco = client.patch(f"/api/pedidos/{pedido_id}/status", headers=pcp, json={"status": status_novo})
        assert avanco.status_code == 200, avanco.text

    logistica = logar(client, "logistica")
    liberado = client.patch(f"/api/pedidos/{pedido_id}/status", headers=logistica, json={"status": "Pronto para retirada"})
    assert liberado.status_code == 200, liberado.text
    return pedido_id


def test_excluir_nota_no_fiscal_devolve_estoque_e_status_anterior():
    client, TestingSession = montar_app()
    pedido_id = criar_pedido_faturado(client)

    fiscal = logar(client, "fiscal")
    preparada = client.post(f"/api/fiscal/pedidos/{pedido_id}/preparar-nfe", headers=fiscal)
    assert preparada.status_code == 201, preparada.text
    nota_id = preparada.json()["id"]
    emitida = client.post(f"/api/fiscal/notas/{nota_id}/marcar-emitida", headers=fiscal)
    assert emitida.status_code == 200, emitida.text

    with TestingSession() as db:
        produto = db.scalars(select(Produto)).first()
        assert produto.estoqueAtual == 960
        assert produto.estoqueReservado == 0

    excluida = client.delete(f"/api/fiscal/notas/{nota_id}", headers=fiscal)
    assert excluida.status_code == 204, excluida.text

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        produto = db.scalars(select(Produto)).first()
        assert pedido.status == "Pronto para retirada"
        assert pedido.dataEmissao is None
        assert produto.estoqueAtual == 1000
        assert produto.estoqueReservado == 40
        assert db.scalars(select(NotaFiscalDraft)).all() == []

    # Nota já excluída não pode ser excluída de novo.
    assert client.delete(f"/api/fiscal/notas/{nota_id}", headers=fiscal).status_code == 404


def test_faturamento_exclui_nota_emitida_e_apaga_rascunho_fiscal():
    client, TestingSession = montar_app()
    pedido_id = criar_pedido_faturado(client)

    fiscal = logar(client, "fiscal")
    preparada = client.post(f"/api/fiscal/pedidos/{pedido_id}/preparar-nfe", headers=fiscal)
    assert preparada.status_code == 201, preparada.text

    faturamento = logar(client, "faturamento")
    emitida = client.patch(f"/api/pedidos/{pedido_id}/status", headers=faturamento, json={"status": "Nota emitida"})
    assert emitida.status_code == 200, emitida.text

    excluida = client.delete(f"/api/pedidos/{pedido_id}/nota", headers=faturamento)
    assert excluida.status_code == 204, excluida.text

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        produto = db.scalars(select(Produto)).first()
        assert pedido.status == "Pronto para retirada"
        assert pedido.dataEmissao is None
        assert produto.estoqueAtual == 1000
        assert produto.estoqueReservado == 40
        assert db.scalars(select(NotaFiscalDraft)).all() == []

    # Sem nota emitida o endpoint recusa a exclusão.
    repetida = client.delete(f"/api/pedidos/{pedido_id}/nota", headers=faturamento)
    assert repetida.status_code == 409, repetida.text


def test_reverter_status_da_emissao_devolve_estoque():
    client, TestingSession = montar_app()
    pedido_id = criar_pedido_faturado(client)

    faturamento = logar(client, "faturamento")
    emitida = client.patch(f"/api/pedidos/{pedido_id}/status", headers=faturamento, json={"status": "Nota emitida"})
    assert emitida.status_code == 200, emitida.text

    revertida = client.patch(f"/api/pedidos/{pedido_id}/status", headers=faturamento, json={"status": "Pronto para retirada"})
    assert revertida.status_code == 200, revertida.text

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        produto = db.scalars(select(Produto)).first()
        assert pedido.dataEmissao is None
        assert produto.estoqueAtual == 1000
        assert produto.estoqueReservado == 40

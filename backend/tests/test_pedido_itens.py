from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth as auth_api
from app.api import pedidos as pedidos_api
from app.db.session import Base, get_db
from app.models.pedido import Pedido
from app.models.produto import Produto
from app.services.auth import seed_usuarios
from app.services.fiscal import montar_payload_nfe
from app.services.regras import valor_total_pedido


def test_pedido_com_varios_itens_reserva_estoque_e_calcula_total():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSession() as db:
        db.add_all(
            [
                Produto(nome="5L", estoqueAtual=1000),
                Produto(nome="1L", estoqueAtual=1000),
            ]
        )
        seed_usuarios(db, "Senha@123")
        db.commit()

    app = FastAPI()
    app.include_router(auth_api.router, prefix="/api")
    app.include_router(pedidos_api.router, prefix="/api")

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    login = client.post("/api/auth/login", json={"username": "comercial", "senha": "Senha@123"})
    headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
    itens = [
        {"produto": "5L", "cor": "Azul", "tampa": "Rosca", "quantidade": 30, "valor": 2, "valorTampa": 0.5},
        {"produto": "5L", "cor": "Preto", "tampa": "Rosca", "quantidade": 30, "valor": 2, "valorTampa": 0.5},
        {"produto": "1L", "cor": "Verde", "tampa": "Lacre", "quantidade": 100, "valor": 1, "valorTampa": 0.25},
    ]
    response = client.post(
        "/api/pedidos",
        headers=headers,
        json={"cliente": "Cliente Teste", **itens[0], "vendedor": "Arthur", "itens": itens},
    )

    assert response.status_code == 201, response.text
    assert [item["cor"] for item in response.json()["itens"]] == ["Azul", "Preto", "Verde"]
    assert response.json()["produto"] == "5L"

    with TestingSession() as db:
        pedido = db.scalar(select(Pedido).where(Pedido.id == response.json()["id"]))
        produtos = {produto.nome: produto for produto in db.scalars(select(Produto)).all()}
        assert valor_total_pedido(pedido) == 275
        assert produtos["5L"].estoqueReservado == 60
        assert produtos["1L"].estoqueReservado == 100
        payload_nfe = montar_payload_nfe(pedido)
        assert len(payload_nfe["itens"]) == 3
        assert payload_nfe["itens"][2]["valor_total_bruto"] == 125

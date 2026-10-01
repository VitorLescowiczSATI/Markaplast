from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.api import auth as auth_api
from app.api import clientes as clientes_api
from app.api import dashboard as dashboard_api
from app.api import metas as metas_api
from app.api import pedidos as pedidos_api
from app.db.session import Base, get_db
from app.models.cliente import Cliente
from app.models.meta import Meta
from app.models.pedido import Pedido
from app.models.usuario import Usuario
from app.services.auth import PERFIL_ADMIN, criar_token, hash_senha
from app.core.config import get_settings


def _montar():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Sessao = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with Sessao() as db:
        db.add_all(
            [
                Usuario(id=1, nome="Admin", username="admin", senhaHash=hash_senha("x" * 8), perfil=PERFIL_ADMIN),
                Usuario(id=2, nome="Glaucia", username="glaucia", senhaHash=hash_senha("x" * 8), perfil="Vendedor", vendedor="Glaucia"),
                Usuario(id=3, nome="Sem vinculo", username="solto", senhaHash=hash_senha("x" * 8), perfil="Vendedor", vendedor=""),
                Pedido(id=10, cliente="Cliente A", cnpj="11.111.111/0001-11", vendedor="Gláucia ", status="Novo pedido", produto="5L M2", quantidade=10, valor=2),
                Pedido(id=11, cliente="Cliente B", cnpj="", vendedor="glaucia", status="Nota emitida", produto="5L M2", quantidade=10, valor=2),
                Pedido(id=12, cliente="Cliente C", cnpj="33333333000133", vendedor="Arthur", status="Novo pedido", produto="5L M2", quantidade=10, valor=2),
                Pedido(id=13, cliente="Cliente D", cnpj="44.444.444/0001-44", vendedor="Arthur", status="Novo pedido", produto="5L M2", quantidade=10, valor=2),
                Cliente(nome="Cliente A (razão nova)", cnpj="11111111000111", vendedor="Arthur"),
                Cliente(nome="Cliente B", cnpj="", vendedor="Glaucia"),
                Cliente(nome="Cliente C", cnpj="33333333000133", vendedor="Arthur"),
                Cliente(nome="Cliente D", cnpj="44444444000144", vendedor="Glaucia"),
                Meta(escopo="vendedor", vendedor="Glaucia", periodo="mensal", valor=1000),
                Meta(escopo="vendedor", vendedor="Arthur", periodo="mensal", valor=2000),
                Meta(escopo="empresa", vendedor="", periodo="mensal", valor=9000),
            ]
        )
        db.commit()

    app = FastAPI()
    for modulo in (auth_api, clientes_api, dashboard_api, metas_api, pedidos_api):
        app.include_router(modulo.router, prefix="/api")

    def override_db():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def _headers(usuario_id: int) -> dict:
    usuario = Usuario(id=usuario_id)
    return {"Authorization": f"Bearer {criar_token(usuario, get_settings().auth_secret, 10)}"}


def test_vendedor_ve_so_os_proprios_pedidos_clientes_metas_e_numeros():
    client = _montar()
    glaucia = _headers(2)

    pedidos = client.get("/api/pedidos", headers=glaucia).json()
    # 10 e 11 saíram no nome dela; 13 é do Arthur, mas o cliente D é dela.
    assert sorted(p["id"] for p in pedidos) == [10, 11, 13]
    assert client.get("/api/pedidos/10", headers=glaucia).status_code == 200
    assert client.get("/api/pedidos/12", headers=glaucia).status_code == 403

    clientes = sorted(c["nome"] for c in client.get("/api/clientes", headers=glaucia).json())
    # Cliente A tem pedido dela, mas o responsável é o Arthur.
    assert clientes == ["Cliente B", "Cliente D"]

    metas = client.get("/api/metas", headers=glaucia).json()
    assert [(m["escopo"], m["vendedor"]) for m in metas] == [("vendedor", "Glaucia")]

    painel = client.get("/api/dashboard", headers=glaucia).json()
    assert {item["label"] for item in painel["porVendedor"]} == {"Gláucia ", "glaucia", "Arthur"}
    assert painel["estoqueCritico"] == []


def test_vendedor_nao_escreve_nem_ve_o_resto():
    client = _montar()
    glaucia = _headers(2)
    assert client.post("/api/pedidos", headers=glaucia, json={"cliente": "X"}).status_code == 403
    assert client.patch("/api/pedidos/10", headers=glaucia, json={"observacoes": "x"}).status_code == 403
    assert client.post("/api/clientes", headers=glaucia, json={"nome": "X"}).status_code == 403
    assert client.post("/api/metas", headers=glaucia, json={"escopo": "vendedor", "vendedor": "Glaucia", "periodo": "mensal", "valor": 1}).status_code == 403
    assert client.get("/api/pedidos/resumo", headers=glaucia).status_code == 403
    assert client.get("/api/auth/usuarios", headers=glaucia).status_code == 403


def test_vendedor_sem_vinculo_nao_ve_nada():
    client = _montar()
    solto = _headers(3)
    assert client.get("/api/pedidos", headers=solto).json() == []
    assert client.get("/api/clientes", headers=solto).json() == []


def test_admin_segue_vendo_tudo_e_cadastro_exige_nome_do_vendedor():
    client = _montar()
    admin = _headers(1)
    assert len(client.get("/api/pedidos", headers=admin).json()) == 4
    assert len(client.get("/api/clientes", headers=admin).json()) == 4
    assert len(client.get("/api/metas", headers=admin).json()) == 3

    base = {"nome": "Nova Vendedora", "username": "nova", "senha": "Temporaria@1", "perfil": "Vendedor"}
    assert client.post("/api/auth/usuarios", headers=admin, json=base).status_code == 422
    criado = client.post("/api/auth/usuarios", headers=admin, json={**base, "vendedor": " Nova "})
    assert criado.status_code == 201
    assert criado.json()["vendedor"] == "Nova"

    novo_id = criado.json()["id"]
    assert client.patch(f"/api/auth/usuarios/{novo_id}", headers=admin, json={"vendedor": ""}).status_code == 422
    virou_pcp = client.patch(f"/api/auth/usuarios/{novo_id}", headers=admin, json={"perfil": "PCP"})
    assert virou_pcp.status_code == 200
    assert virou_pcp.json()["vendedor"] == ""


def test_cliente_criado_pelo_pedido_herda_o_vendedor_e_dono_existente_nao_muda():
    from types import SimpleNamespace

    from sqlalchemy import create_engine as criar
    from sqlalchemy.orm import Session

    from app.services.clientes import upsert_cliente_do_pedido

    engine = criar("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        novo = upsert_cliente_do_pedido(db, SimpleNamespace(cliente="Novo", cnpj="1", vendedor="Glaucia"))
        db.commit()
        assert novo.vendedor == "Glaucia"
        mesmo = upsert_cliente_do_pedido(db, SimpleNamespace(cliente="Novo", cnpj="1", vendedor="Arthur"))
        assert mesmo.vendedor == "Glaucia"

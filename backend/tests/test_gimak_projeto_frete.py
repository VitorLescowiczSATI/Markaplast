"""Frete (CIF ou FOB) e nome do contato no projeto, sem quebrar os projetos antigos."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.gimak.api import router
from app.gimak.auth import seed_gimak_admin
from app.gimak.db import GimakBase, get_gimak_db


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    GimakBase.metadata.create_all(bind=engine)
    with TestingSession() as db:
        seed_gimak_admin(db, "Senha@123")

    app = FastAPI()
    app.include_router(router, prefix="/api")

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_gimak_db] = override_db
    yield TestClient(app)
    engine.dispose()


def token(client):
    response = client.post("/api/gimak/auth/login", json={"username": "admin", "senha": "Senha@123"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def test_projeto_grava_e_edita_frete_e_contato(client):
    headers = token(client)
    criado = client.post(
        "/api/gimak/projetos",
        headers=headers,
        json={"cliente": "Krenke", "equipamento": "Envolvedora GK2100", "contato": " Marcos ", "frete": "FOB"},
    )
    assert criado.status_code == 201, criado.text
    projeto = criado.json()
    assert projeto["contato"] == "Marcos"
    assert projeto["frete"] == "FOB"

    editado = client.patch(
        f"/api/gimak/projetos/{projeto['id']}", headers=headers, json={"frete": "CIF", "contato": "Ana"}
    )
    assert editado.status_code == 200, editado.text
    assert editado.json()["frete"] == "CIF"
    assert editado.json()["contato"] == "Ana"

    limpo = client.patch(f"/api/gimak/projetos/{projeto['id']}", headers=headers, json={"frete": ""})
    assert limpo.json()["frete"] == ""

    listado = client.get("/api/gimak/projetos", headers=headers).json()
    assert listado[0]["contato"] == "Ana"


def test_projeto_sem_frete_e_aceito_e_frete_invalido_e_recusado(client):
    headers = token(client)
    sem = client.post("/api/gimak/projetos", headers=headers, json={"cliente": "Ambev", "equipamento": "Misturador"})
    assert sem.status_code == 201, sem.text
    assert sem.json()["frete"] == ""
    assert sem.json()["contato"] == ""

    invalido = client.post(
        "/api/gimak/projetos", headers=headers, json={"cliente": "Ambev", "equipamento": "Misturador", "frete": "EXW"}
    )
    assert invalido.status_code == 422


def test_ensure_columns_acrescenta_frete_e_contato_em_projeto_antigo(monkeypatch):
    """Produção tem projetos criados antes das colunas novas."""
    from app.gimak import db as gimak_db

    engine = create_engine("sqlite://", poolclass=StaticPool)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE projetos (id INTEGER PRIMARY KEY, cliente TEXT, equipamento TEXT)"))
        connection.execute(text("INSERT INTO projetos (id, cliente, equipamento) VALUES (1, 'Ambev', 'Envasadora')"))
    monkeypatch.setattr(gimak_db, "gimak_engine", engine)

    gimak_db.ensure_gimak_columns()
    gimak_db.ensure_gimak_columns()  # idempotente
    with engine.connect() as connection:
        linha = connection.execute(text("SELECT contato, frete FROM projetos WHERE id = 1")).one()
    assert tuple(linha) == ("", "")
    engine.dispose()

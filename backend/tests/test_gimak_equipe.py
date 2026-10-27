"""Mais de um técnico no mesmo atendimento, sem perder os registros de um técnico só."""

from datetime import date

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


def token(client, username="admin", senha="Senha@123"):
    response = client.post("/api/gimak/auth/login", json={"username": username, "senha": senha})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def test_atendimento_com_dois_tecnicos_aparece_na_ficha_de_cada_um(client):
    headers = token(client)
    for nome, username in (("Ulisses", "ulisses"), ("Ralf", "ralf")):
        client.post(
            "/api/gimak/usuarios",
            headers=headers,
            json={"nome": nome, "username": username, "senha": "Senha@1234", "perfil": "Fábrica"},
        )
    hoje = date.today().isoformat()
    criado = client.post(
        "/api/gimak/atendimentos",
        headers=headers,
        json={"cliente": "Krenke", "tecnicos": ["Ulisses", " Ralf ", "ulisses"], "data": hoje},
    )
    assert criado.status_code == 201, criado.text
    servico = criado.json()
    assert servico["tecnicos"] == ["Ulisses", "Ralf"]
    assert servico["tecnico"] == "Ulisses"

    for nome in ("Ulisses", "Ralf"):
        ficha = client.get(
            "/api/gimak/indicadores/pessoa", headers=headers, params={"nome": nome, "inicio": hoje, "fim": hoje}
        )
        assert ficha.status_code == 200, ficha.text
        assert ficha.json()["resumo"]["atendimentos"] == 1
        assert ficha.json()["atendimentos"][0]["tecnicos"] == ["Ulisses", "Ralf"]

    trocado = client.patch(
        f"/api/gimak/atendimentos/{servico['id']}", headers=headers, json={"tecnicos": ["Ralf", "Jean"]}
    ).json()
    assert trocado["tecnicos"] == ["Ralf", "Jean"]
    assert trocado["tecnico"] == "Ralf"

    so_a_descricao = client.patch(
        f"/api/gimak/atendimentos/{servico['id']}", headers=headers, json={"descricao": "Trocar a esteira"}
    ).json()
    assert so_a_descricao["tecnicos"] == ["Ralf", "Jean"]

    assert client.patch(
        f"/api/gimak/atendimentos/{servico['id']}", headers=headers, json={"tecnicos": []}
    ).status_code == 422
    assert client.post(
        "/api/gimak/atendimentos", headers=headers, json={"cliente": "Krenke", "data": hoje}
    ).status_code == 422


def test_quem_ainda_manda_um_tecnico_so_continua_funcionando(client):
    headers = token(client)
    hoje = date.today().isoformat()
    servico = client.post(
        "/api/gimak/atendimentos", headers=headers, json={"cliente": "Vale", "tecnico": "Alan", "data": hoje}
    ).json()
    assert servico["tecnicos"] == ["Alan"]
    editado = client.patch(
        f"/api/gimak/atendimentos/{servico['id']}", headers=headers, json={"tecnico": "Felipe"}
    ).json()
    assert editado["tecnicos"] == ["Felipe"]
    assert editado["tecnico"] == "Felipe"


def test_pendencia_leva_a_equipe_junto(client):
    headers = token(client)
    servico = client.post(
        "/api/gimak/atendimentos",
        headers=headers,
        json={"cliente": "Krenke", "tecnicos": ["Ulisses", "Ralf"], "data": date.today().isoformat()},
    ).json()
    criada = client.post(
        f"/api/gimak/atendimentos/{servico['id']}/pendencias", headers=headers, json={"descricao": "Faltou o sensor"}
    )
    assert criada.status_code == 201, criada.text
    pendencia = client.get("/api/gimak/pendencias", headers=headers).json()[0]
    assert pendencia["tecnicos"] == ["Ulisses", "Ralf"]


def test_corrigir_o_nome_troca_so_aquele_tecnico_da_equipe(client):
    headers = token(client)
    usuario = client.post(
        "/api/gimak/usuarios",
        headers=headers,
        json={"nome": "Ulises", "username": "ulisses", "senha": "Senha@1234", "perfil": "Fábrica"},
    ).json()
    servico = client.post(
        "/api/gimak/atendimentos",
        headers=headers,
        json={"cliente": "Krenke", "tecnicos": ["Ralf", "Ulises"], "data": date.today().isoformat()},
    ).json()

    client.patch(f"/api/gimak/usuarios/{usuario['id']}", headers=headers, json={"nome": "Ulisses"})

    atual = next(item for item in client.get("/api/gimak/atendimentos", headers=headers).json() if item["id"] == servico["id"])
    assert atual["tecnicos"] == ["Ralf", "Ulisses"]
    assert atual["tecnico"] == "Ralf"


def test_ensure_columns_copia_o_tecnico_antigo_para_a_equipe(monkeypatch):
    """Produção tem atendimentos com um técnico só e ainda sem a coluna tecnicos."""
    from app.gimak import db as gimak_db

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE atendimentos (id INTEGER PRIMARY KEY, cliente TEXT, tecnico TEXT)"))
        connection.execute(text("INSERT INTO atendimentos (id, cliente, tecnico) VALUES (1, 'Ambev', 'Cleyton')"))
    monkeypatch.setattr(gimak_db, "gimak_engine", engine)

    gimak_db.ensure_gimak_columns()
    with engine.begin() as connection:
        assert connection.execute(text("SELECT tecnicos FROM atendimentos WHERE id = 1")).scalar() == '["Cleyton"]'
        connection.execute(text("""UPDATE atendimentos SET tecnicos = '["Cleyton", "Ralf"]' WHERE id = 1"""))
    gimak_db.ensure_gimak_columns()  # idempotente: não volta a equipe para um só
    with engine.connect() as connection:
        assert connection.execute(text("SELECT tecnicos FROM atendimentos WHERE id = 1")).scalar() == '["Cleyton", "Ralf"]'
    engine.dispose()

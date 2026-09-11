from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.gimak.api import router
from app.gimak.auth import seed_gimak_admin
from app.gimak.db import GimakBase, build_gimak_database_url, get_gimak_db


def test_build_gimak_url_keeps_instance_and_changes_database():
    result = build_gimak_database_url(
        "postgresql://user:password@database.internal/original",
        database_name="gimak_pcp",
    )
    assert result == "postgresql+psycopg://user:password@database.internal/gimak_pcp"


def test_gimak_auth_projects_tasks_and_time_entries_are_isolated():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
    client = TestClient(app)

    login = client.post("/api/gimak/auth/login", json={"username": "admin", "senha": "Senha@123"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}

    project = client.post(
        "/api/gimak/projetos",
        headers=headers,
        json={"cliente": "Indústria Teste", "equipamento": "Envolvedora GK2100"},
    )
    assert project.status_code == 201

    task = client.post(
        "/api/gimak/tarefas",
        headers=headers,
        json={
            "titulo": "Montar painel elétrico",
            "ordem": "OP-1052",
            "responsavel": "Administrador Gimak",
            "dataPlanejada": "2026-09-10",
            "horario": "14:00",
            "prioridade": "Urgente",
            "observacao": "Conferir diagrama",
            "projetoId": project.json()["id"],
        },
    )
    assert task.status_code == 201
    task_id = task.json()["id"]

    started = client.patch(f"/api/gimak/tarefas/{task_id}/status", headers=headers, json={"status": "doing"})
    assert started.status_code == 200
    assert started.json()["startedAt"]

    started_again = client.patch(
        f"/api/gimak/tarefas/{task_id}/status", headers=headers, json={"status": "doing"}
    )
    assert started_again.status_code == 200
    assert started_again.json()["startedAt"] == started.json()["startedAt"]

    missing_reason = client.patch(
        f"/api/gimak/tarefas/{task_id}/status", headers=headers, json={"status": "paused"}
    )
    assert missing_reason.status_code == 422

    paused = client.patch(
        f"/api/gimak/tarefas/{task_id}/status",
        headers=headers,
        json={"status": "paused", "motivo": "Aguardando material"},
    )
    assert paused.status_code == 200
    assert paused.json()["motivo"] == "Aguardando material"
    assert len(paused.json()["historico"]) == 2

    created_operator = client.post(
        "/api/gimak/usuarios",
        headers=headers,
        json={
            "nome": "Operador da Fábrica",
            "username": "operador",
            "senha": "Operador@123",
            "perfil": "Fábrica",
        },
    )
    assert created_operator.status_code == 201
    operator_login = client.post(
        "/api/gimak/auth/login", json={"username": "operador", "senha": "Operador@123"}
    )
    operator_headers = {"Authorization": f"Bearer {operator_login.json()['accessToken']}"}
    assert client.post(
        "/api/gimak/projetos",
        headers=operator_headers,
        json={"cliente": "Sem permissão", "equipamento": "Teste"},
    ).status_code == 403
    assert client.patch(
        f"/api/gimak/tarefas/{task_id}/status",
        headers=operator_headers,
        json={"status": "doing"},
    ).status_code == 200

    assert client.get("/api/gimak/tarefas", headers=headers).status_code == 200
    assert client.get("/api/gimak/tarefas").status_code == 401

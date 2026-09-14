"""Projeto concluído, exclusão de atividade e a tela de assistências/instalações."""

from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, inspect, text
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


def novo_usuario(client, headers, nome, username, perfil):
    created = client.post(
        "/api/gimak/usuarios",
        headers=headers,
        json={"nome": nome, "username": username, "senha": "Senha@1234", "perfil": perfil},
    )
    assert created.status_code == 201, created.text
    return token(client, username, "Senha@1234")


def test_projeto_concluido_sai_da_lista_padrao_e_volta_pelo_filtro(client):
    headers = token(client)
    aberto = client.post(
        "/api/gimak/projetos", headers=headers, json={"cliente": "Ambev", "equipamento": "Esteira"}
    ).json()
    fechado = client.post(
        "/api/gimak/projetos", headers=headers, json={"cliente": "Vale", "equipamento": "Chassi"}
    ).json()

    concluido = client.patch(
        f"/api/gimak/projetos/{fechado['id']}", headers=headers, json={"concluido": True}
    )
    assert concluido.status_code == 200
    assert concluido.json()["concluidoEm"]

    padrao = [item["id"] for item in client.get("/api/gimak/projetos", headers=headers).json()]
    assert padrao == [aberto["id"]]

    filtrados = client.get("/api/gimak/projetos?situacao=concluidos", headers=headers).json()
    assert [item["id"] for item in filtrados] == [fechado["id"]]

    todos = client.get("/api/gimak/projetos?situacao=todos", headers=headers).json()
    assert {item["id"] for item in todos} == {aberto["id"], fechado["id"]}


def test_concluir_duas_vezes_mantem_a_data_e_reabrir_limpa(client):
    headers = token(client)
    projeto = client.post(
        "/api/gimak/projetos", headers=headers, json={"cliente": "Nestlé", "equipamento": "Mesa"}
    ).json()
    primeira = client.patch(
        f"/api/gimak/projetos/{projeto['id']}", headers=headers, json={"concluido": True}
    ).json()
    repetida = client.patch(
        f"/api/gimak/projetos/{projeto['id']}", headers=headers, json={"concluido": True}
    ).json()
    assert repetida["concluidoEm"] == primeira["concluidoEm"]

    reaberto = client.patch(
        f"/api/gimak/projetos/{projeto['id']}", headers=headers, json={"concluido": False}
    ).json()
    assert reaberto["concluidoEm"] is None
    assert [item["id"] for item in client.get("/api/gimak/projetos", headers=headers).json()] == [projeto["id"]]


def test_so_o_administrador_exclui_atividade_e_o_historico_vai_junto(client):
    headers = token(client)
    fabrica = novo_usuario(client, headers, "Carlos Souza", "carlos", "Fábrica")
    tarefa = client.post(
        "/api/gimak/tarefas",
        headers=headers,
        json={
            "titulo": "Corte de chapas",
            "responsavel": "Carlos Souza",
            "dataPlanejada": date.today().isoformat(),
            "horario": "08:00",
        },
    ).json()
    client.patch(f"/api/gimak/tarefas/{tarefa['id']}/status", headers=fabrica, json={"status": "doing"})

    assert client.delete(f"/api/gimak/tarefas/{tarefa['id']}", headers=fabrica).status_code == 403
    assert client.delete(f"/api/gimak/tarefas/{tarefa['id']}", headers=headers).status_code == 204
    assert client.get(f"/api/gimak/tarefas", headers=headers).json() == []
    assert client.delete(f"/api/gimak/tarefas/{tarefa['id']}", headers=headers).status_code == 404


def test_atendimento_e_agendado_concluido_com_relatorio_e_filtrado(client):
    headers = token(client)
    fabrica = novo_usuario(client, headers, "Marina Alves", "marina", "Fábrica")
    criado = client.post(
        "/api/gimak/atendimentos",
        headers=headers,
        json={
            "tipo": "Instalação",
            "cliente": "Ambev Jaguariúna",
            "local": "Rodovia SP-340, km 130",
            "tecnico": "Marina Alves",
            "data": date.today().isoformat(),
            "horario": "09:30",
            "descricao": "Instalar a esteira EX-200",
        },
    )
    assert criado.status_code == 201, criado.text
    servico = criado.json()
    assert servico["status"] == "agendado"
    assert servico["concluidoEm"] is None

    sem_relatorio = client.post(
        f"/api/gimak/atendimentos/{servico['id']}/concluir", headers=fabrica, json={"relatorio": " "}
    )
    assert sem_relatorio.status_code == 422

    concluido = client.post(
        f"/api/gimak/atendimentos/{servico['id']}/concluir",
        headers=fabrica,
        json={"relatorio": "Esteira instalada e testada com o cliente."},
    )
    assert concluido.status_code == 200
    assert concluido.json()["status"] == "concluido"
    assert concluido.json()["relatorio"] == "Esteira instalada e testada com o cliente."
    assert concluido.json()["concluidoEm"]

    corrigido = client.post(
        f"/api/gimak/atendimentos/{servico['id']}/concluir",
        headers=fabrica,
        json={"relatorio": "Esteira instalada, testada e treinamento entregue."},
    ).json()
    assert corrigido["relatorio"] == "Esteira instalada, testada e treinamento entregue."
    assert corrigido["concluidoEm"] == concluido.json()["concluidoEm"]

    assert [i["id"] for i in client.get("/api/gimak/atendimentos?situacao=concluidos", headers=headers).json()] == [servico["id"]]
    assert client.get("/api/gimak/atendimentos?situacao=agendados", headers=headers).json() == []

    reaberto = client.post(f"/api/gimak/atendimentos/{servico['id']}/reabrir", headers=headers).json()
    assert reaberto["status"] == "agendado"
    assert reaberto["concluidoEm"] is None
    assert reaberto["relatorio"] == "Esteira instalada, testada e treinamento entregue."


def test_atendimento_respeita_perfis(client):
    headers = token(client)
    fabrica = novo_usuario(client, headers, "Rafael Lima", "rafael", "Fábrica")
    payload = {
        "cliente": "Vale",
        "tecnico": "Rafael Lima",
        "data": date.today().isoformat(),
        "horario": "14:00",
    }
    assert client.post("/api/gimak/atendimentos", headers=fabrica, json=payload).status_code == 403
    servico = client.post("/api/gimak/atendimentos", headers=headers, json=payload).json()
    assert servico["tipo"] == "Assistência técnica"

    assert client.patch(
        f"/api/gimak/atendimentos/{servico['id']}", headers=fabrica, json={"cliente": "Outro"}
    ).status_code == 403
    assert client.delete(f"/api/gimak/atendimentos/{servico['id']}", headers=fabrica).status_code == 403
    assert client.get("/api/gimak/atendimentos", headers=fabrica).status_code == 200
    assert client.delete(f"/api/gimak/atendimentos/{servico['id']}", headers=headers).status_code == 204
    assert client.get("/api/gimak/atendimentos", headers=headers).json() == []


def test_ensure_columns_acrescenta_coluna_em_tabela_antiga(monkeypatch):
    """Produção já tem a tabela projetos sem concluido_em; create_all sozinho não resolve."""
    from app.gimak import db as gimak_db

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE projetos (id INTEGER PRIMARY KEY, cliente TEXT)"))
    monkeypatch.setattr(gimak_db, "gimak_engine", engine)

    assert "concluido_em" not in {c["name"] for c in inspect(engine).get_columns("projetos")}
    gimak_db.ensure_gimak_columns()
    assert "concluido_em" in {c["name"] for c in inspect(engine).get_columns("projetos")}
    gimak_db.ensure_gimak_columns()  # idempotente
    engine.dispose()

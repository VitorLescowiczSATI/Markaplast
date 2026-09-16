"""Saída do técnico, horários planejados e as pendências que sobram do atendimento."""

from datetime import date, timedelta

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


def tecnico(client, headers, nome="Carlos Souza", username="carlos"):
    created = client.post(
        "/api/gimak/usuarios",
        headers=headers,
        json={"nome": nome, "username": username, "senha": "Senha@1234", "perfil": "Fábrica"},
    )
    assert created.status_code == 201, created.text
    return token(client, username, "Senha@1234")


def novo_atendimento(client, headers, **extra):
    payload = {
        "cliente": "Ambev Jaguariúna",
        "tecnico": "Carlos Souza",
        "data": date.today().isoformat(),
        "horario": "10:00",
        **extra,
    }
    response = client.post("/api/gimak/atendimentos", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_administrador_define_saida_e_retorno_e_edita_depois(client):
    headers = token(client)
    servico = novo_atendimento(client, headers, horarioSaida="07:30", horarioRetorno="17:00")
    assert servico["horarioSaida"] == "07:30"
    assert servico["horarioRetorno"] == "17:00"

    editado = client.patch(
        f"/api/gimak/atendimentos/{servico['id']}",
        headers=headers,
        json={"horarioSaida": "08:15", "horarioRetorno": "", "cliente": "Ambev Guarulhos"},
    )
    assert editado.status_code == 200, editado.text
    assert editado.json()["horarioSaida"] == "08:15"
    assert editado.json()["horarioRetorno"] == ""
    assert editado.json()["cliente"] == "Ambev Guarulhos"

    invalido = client.patch(
        f"/api/gimak/atendimentos/{servico['id']}", headers=headers, json={"horarioSaida": "25:99"}
    )
    assert invalido.status_code == 422


def test_tecnico_marca_saida_e_o_atendimento_segue_em_aberto(client):
    headers = token(client)
    fabrica = tecnico(client, headers)
    servico = novo_atendimento(client, headers)

    saiu = client.post(f"/api/gimak/atendimentos/{servico['id']}/sair", headers=fabrica)
    assert saiu.status_code == 200
    assert saiu.json()["status"] == "em_rota"
    primeira_saida = saiu.json()["saidaEm"]
    assert primeira_saida

    repetido = client.post(f"/api/gimak/atendimentos/{servico['id']}/sair", headers=fabrica).json()
    assert repetido["saidaEm"] == primeira_saida

    # Em rota continua sendo um atendimento em aberto, não some da lista de agendados.
    agendados = client.get("/api/gimak/atendimentos?situacao=agendados", headers=headers).json()
    assert [item["id"] for item in agendados] == [servico["id"]]

    concluido = client.post(
        f"/api/gimak/atendimentos/{servico['id']}/concluir",
        headers=fabrica,
        json={"relatorio": "Trocado o contator e testado."},
    ).json()
    assert concluido["status"] == "concluido"
    assert concluido["saidaEm"] == primeira_saida

    assert client.post(f"/api/gimak/atendimentos/{servico['id']}/sair", headers=fabrica).status_code == 422


def test_reabrir_volta_para_em_rota_quando_ja_tinha_saido(client):
    headers = token(client)
    fabrica = tecnico(client, headers)
    servico = novo_atendimento(client, headers)
    client.post(f"/api/gimak/atendimentos/{servico['id']}/sair", headers=fabrica)
    client.post(
        f"/api/gimak/atendimentos/{servico['id']}/concluir", headers=fabrica, json={"relatorio": "Feito."}
    )
    reaberto = client.post(f"/api/gimak/atendimentos/{servico['id']}/reabrir", headers=headers).json()
    assert reaberto["status"] == "em_rota"

    outro = novo_atendimento(client, headers)
    client.post(f"/api/gimak/atendimentos/{outro['id']}/concluir", headers=fabrica, json={"relatorio": "Feito."})
    assert client.post(f"/api/gimak/atendimentos/{outro['id']}/reabrir", headers=headers).json()["status"] == "agendado"


def test_pendencia_do_atendimento_e_acompanhada_ate_resolver(client):
    headers = token(client)
    fabrica = tecnico(client, headers)
    servico = novo_atendimento(client, headers)
    client.post(
        f"/api/gimak/atendimentos/{servico['id']}/concluir",
        headers=fabrica,
        json={"relatorio": "Máquina rodando, mas faltou peça."},
    )

    curta = client.post(
        f"/api/gimak/atendimentos/{servico['id']}/pendencias", headers=fabrica, json={"descricao": "x"}
    )
    assert curta.status_code == 422

    criada = client.post(
        f"/api/gimak/atendimentos/{servico['id']}/pendencias",
        headers=fabrica,
        json={"descricao": "Faltou o sensor indutivo M12 para fechar a montagem."},
    )
    assert criada.status_code == 201, criada.text
    pendencia = criada.json()
    assert pendencia["status"] == "aberta"

    abertas = client.get("/api/gimak/pendencias", headers=headers).json()
    assert len(abertas) == 1
    assert abertas[0]["cliente"] == "Ambev Jaguariúna"
    assert abertas[0]["tecnico"] == "Carlos Souza"
    assert abertas[0]["atendimentoId"] == servico["id"]

    detalhe = client.get("/api/gimak/atendimentos", headers=headers).json()[0]
    assert [item["id"] for item in detalhe["pendencias"]] == [pendencia["id"]]

    resolvida = client.post(
        f"/api/gimak/pendencias/{pendencia['id']}/resolver",
        headers=headers,
        json={"resolucao": "Sensor comprado e instalado na visita seguinte."},
    ).json()
    assert resolvida["status"] == "resolvida"
    assert resolvida["resolvidoEm"]

    assert client.get("/api/gimak/pendencias", headers=headers).json() == []
    assert len(client.get("/api/gimak/pendencias?situacao=resolvidas", headers=headers).json()) == 1
    assert len(client.get("/api/gimak/pendencias?situacao=todas", headers=headers).json()) == 1

    reaberta = client.post(f"/api/gimak/pendencias/{pendencia['id']}/reabrir", headers=headers).json()
    assert reaberta["status"] == "aberta"
    assert reaberta["resolvidoEm"] is None


def test_pendencia_respeita_perfis_e_morre_com_o_atendimento(client):
    headers = token(client)
    fabrica = tecnico(client, headers)
    servico = novo_atendimento(client, headers)
    pendencia = client.post(
        f"/api/gimak/atendimentos/{servico['id']}/pendencias",
        headers=fabrica,
        json={"descricao": "Faltou o cabo de aço sobressalente."},
    ).json()

    assert client.patch(
        f"/api/gimak/pendencias/{pendencia['id']}", headers=fabrica, json={"descricao": "outro texto"}
    ).status_code == 403
    assert client.delete(f"/api/gimak/pendencias/{pendencia['id']}", headers=fabrica).status_code == 403
    assert client.post(f"/api/gimak/pendencias/{pendencia['id']}/reabrir", headers=fabrica).status_code == 403

    assert client.delete(f"/api/gimak/atendimentos/{servico['id']}", headers=headers).status_code == 204
    assert client.get("/api/gimak/pendencias?situacao=todas", headers=headers).json() == []


def test_ensure_columns_acrescenta_horarios_em_atendimento_antigo(monkeypatch):
    from app.gimak import db as gimak_db

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE atendimentos (id INTEGER PRIMARY KEY, cliente TEXT)"))
        connection.execute(text("INSERT INTO atendimentos (id, cliente) VALUES (1, 'Ambev')"))
    monkeypatch.setattr(gimak_db, "gimak_engine", engine)

    gimak_db.ensure_gimak_columns()
    colunas = {c["name"] for c in inspect(engine).get_columns("atendimentos")}
    assert {"horario_saida", "horario_retorno", "saida_em", "saida_por_id"} <= colunas
    with engine.connect() as connection:
        linha = connection.execute(text("SELECT horario_saida, saida_em FROM atendimentos WHERE id = 1")).one()
    assert linha == ("", None)
    engine.dispose()


def test_assistencia_de_mais_de_um_dia_tem_data_de_ida_e_de_volta(client):
    headers = token(client)
    ida = date.today()
    volta = ida + timedelta(days=2)
    servico = novo_atendimento(
        client, headers, data=ida.isoformat(), dataVolta=volta.isoformat(),
        horarioSaida="06:00", horarioRetorno="19:00",
    )
    assert servico["data"] == ida.isoformat()
    assert servico["dataVolta"] == volta.isoformat()

    de_um_dia = novo_atendimento(client, headers)
    assert de_um_dia["dataVolta"] is None

    invertido = client.post(
        "/api/gimak/atendimentos",
        headers=headers,
        json={
            "cliente": "Vale", "tecnico": "Carlos Souza",
            "data": ida.isoformat(), "dataVolta": (ida - timedelta(days=1)).isoformat(),
        },
    )
    assert invertido.status_code == 422

    editado = client.patch(
        f"/api/gimak/atendimentos/{de_um_dia['id']}",
        headers=headers,
        json={"dataVolta": volta.isoformat()},
    )
    assert editado.status_code == 200
    assert editado.json()["dataVolta"] == volta.isoformat()

    assert client.patch(
        f"/api/gimak/atendimentos/{de_um_dia['id']}",
        headers=headers,
        json={"dataVolta": (ida - timedelta(days=3)).isoformat()},
    ).status_code == 422


def test_ordem_segue_a_hora_de_sair_e_cai_no_horario_antigo(client):
    headers = token(client)
    hoje = date.today().isoformat()
    tarde = novo_atendimento(client, headers, cliente="Sai as 15h", horario="07:00", horarioSaida="15:00")
    cedo = novo_atendimento(client, headers, cliente="Sai as 06h", horario="23:00", horarioSaida="06:00")
    antigo = novo_atendimento(client, headers, cliente="Sem hora de sair", horario="09:00")

    ordem = [item["cliente"] for item in client.get("/api/gimak/atendimentos", headers=headers).json()]
    assert ordem == ["Sai as 06h", "Sem hora de sair", "Sai as 15h"], ordem
    assert tarde["data"] == cedo["data"] == antigo["data"] == hoje

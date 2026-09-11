import base64
import json
from datetime import date, datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.gimak import analytics
from app.gimak.api import router
from app.gimak.auth import PERFIL_ADMIN, PERFIL_FABRICA, PERFIL_PCP, PERFIL_TV
from app.gimak.db import GimakBase, get_gimak_db
from app.gimak.models import GimakApontamento, GimakProjeto, GimakTarefa, GimakUsuario
from app.services.auth import hash_senha


NOW = datetime(2026, 9, 11, 15, tzinfo=timezone.utc)


@pytest.fixture
def db(monkeypatch):
    monkeypatch.setattr(analytics, "utc_now", lambda: NOW)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    GimakBase.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def user(db, name, role=PERFIL_FABRICA):
    item = GimakUsuario(nome=name, username=f"user{len(db.new)}{name.replace(' ', '').lower()}",
                        senhaHash=hash_senha("TestOnly@123"), perfil=role, ativo=True)
    db.add(item)
    db.flush()
    return item


def task(db, name="Operador", planned=date(2026, 9, 11), clock="10:00", state="todo", **kwargs):
    item = GimakTarefa(titulo="Montar equipamento", responsavel=name, dataPlanejada=planned,
                      horario=clock, status=state, **kwargs)
    db.add(item)
    db.flush()
    return item


def event(db, item, actor, old, new, at):
    entry = GimakApontamento(tarefaId=item.id, usuarioId=actor.id if actor else None,
                            statusAnterior=old, statusNovo=new, createdAt=at)
    db.add(entry)
    db.flush()
    return entry


def test_empty_denominators_are_unknown_and_empty_projects_are_safe(db):
    user(db, "Operador")
    db.add(GimakProjeto(cliente="Cliente", equipamento="Equipamento"))
    db.commit()
    result = analytics.build_indicators(db)
    assert result["resumo"]["taxaConclusao"] is None
    assert result["resumo"]["taxaNoPrazo"] is None
    assert result["adesao"][0]["taxaApontamentoProprio"] is None
    assert result["adesao"][0]["ultimoApontamento"] is None
    assert result["projetos"][0]["percentualConclusao"] is None
    assert analytics.build_tv_panel(db)["resumo"]["taxaConclusaoHoje"] is None


def test_factory_timezone_controls_default_date_completion_and_activity_days(db, monkeypatch):
    now = datetime(2026, 9, 12, 1, 30, tzinfo=timezone.utc)  # still September 11 in the factory
    monkeypatch.setattr(analytics, "utc_now", lambda: now)
    operator = user(db, "Operador")
    item = task(db, state="done", clock="23:00", finishedAt=now)
    event(db, item, operator, "todo", "doing", datetime(2026, 9, 11, 23, 30, tzinfo=timezone.utc))
    event(db, item, operator, "doing", "done", datetime(2026, 9, 12, 1, tzinfo=timezone.utc))
    db.commit()
    result = analytics.build_indicators(db)
    assert result["periodo"] == {"inicio": date(2026, 9, 11), "fim": date(2026, 9, 11)}
    assert result["resumo"]["concluidasNoPrazo"] == 1
    assert result["adesao"][0]["diasAtivos"] == 1
    assert result["serieDiaria"] == [{"data": date(2026, 9, 11), "planejadas": 1, "concluidas": 1}]
    assert analytics.build_tv_panel(db)["resumo"]["concluidasHoje"] == 1


def test_deadlines_use_planned_hour_and_exclude_not_done_from_open_backlog(db):
    task(db, clock="11:59")
    task(db, clock="12:00")  # NOW is noon local: equality is not late yet
    task(db, planned=date(2026, 9, 10), state="paused")
    task(db, planned=date(2026, 9, 10), state="blocked")
    task(db, state="done", finishedAt=NOW, clock="11:00")
    db.commit()
    result = analytics.build_indicators(db)
    assert result["resumo"]["atrasadasNoPeriodo"] == 1
    assert result["resumo"]["atrasadasEmAberto"] == 2
    assert result["resumo"]["concluidasNoPrazo"] == 0
    assert result["resumo"]["taxaNoPrazo"] == 0
    assert {t["status"] for t in result["atrasadas"]} == {"paused", "todo"}


def test_actor_usage_does_not_change_the_responsible_ranking(db):
    responsible = user(db, "João Silva")
    supervisor = user(db, "Supervisor", PERFIL_ADMIN)
    item = task(db, name="  JOAO   SILVA ", state="done", finishedAt=NOW)
    event(db, item, supervisor, "todo", "doing", NOW - timedelta(minutes=20))
    event(db, item, supervisor, "doing", "done", NOW)
    db.commit()
    result = analytics.build_indicators(db)
    assert result["ranking"][0]["usuarioId"] == responsible.id
    assert result["ranking"][0]["concluidas"] == 1
    adoption = {row["usuarioId"]: row for row in result["adesao"]}
    assert adoption[responsible.id]["apontamentos"] == 0
    assert adoption[responsible.id]["taxaApontamentoProprio"] == 0
    assert adoption[supervisor.id]["apontamentos"] == 2
    assert adoption[supervisor.id]["tarefasMovimentadas"] == 1
    assert adoption[supervisor.id]["taxaApontamentoProprio"] is None


def test_ambiguous_and_unlinked_assignment_names_are_not_attributed_to_users(db):
    user(db, "João")
    user(db, "Joao")
    task(db, name="JOAO", state="done", finishedAt=NOW)
    task(db, name="Nome legado")
    db.commit()
    result = analytics.build_indicators(db)
    assert {r["vinculo"] for r in result["ranking"]} == {"ambiguo", "sem_usuario"}
    assert all(row["usuarioId"] is None for row in result["ranking"])
    assert all(row["tarefasAtribuidas"] == 0 for row in result["adesao"])


def test_duplicate_done_events_do_not_inflate_counts_or_change_completion_time(db):
    item = task(db, state="done", finishedAt=NOW, clock="11:00")
    real_completion = NOW - timedelta(hours=2)
    event(db, item, None, "doing", "done", real_completion)
    event(db, item, None, "done", "done", NOW)
    db.commit()
    result = analytics.build_indicators(db)
    assert result["resumo"]["concluidas"] == 1
    assert result["resumo"]["concluidasNoPrazo"] == 1
    assert result["serieDiaria"][0]["concluidas"] == 1
    assert analytics.build_tv_panel(db)["ultimosEventos"][0]["ocorridoEm"] == real_completion


def test_reopening_removes_old_completion_and_final_run_counts_once(db):
    item = task(db, state="doing", startedAt=NOW)
    event(db, item, None, "doing", "done", NOW - timedelta(hours=3))
    event(db, item, None, "done", "doing", NOW - timedelta(hours=2))
    db.commit()
    assert analytics.build_indicators(db)["resumo"]["concluidas"] == 0
    item.status = "done"
    item.finishedAt = NOW
    event(db, item, None, "doing", "done", NOW)
    db.commit()
    result = analytics.build_indicators(db)
    assert result["resumo"]["concluidas"] == 1
    assert result["resumo"]["concluidasNoPrazo"] == 0


def test_cohort_recorded_time_includes_prior_accumulation_and_running_segment(db):
    task(db, state="doing", elapsedSeconds=3600, startedAt=NOW - timedelta(minutes=5))
    task(db, planned=date(2026, 9, 10), elapsedSeconds=99999)
    db.commit()
    result = analytics.build_indicators(db)
    assert result["resumo"]["tempoRegistradoSegundos"] == 3900
    assert "fora do período" in result["criterios"]["tempo"]


@pytest.fixture
def api(db):
    accounts = {role: user(db, role, role) for role in (PERFIL_ADMIN, PERFIL_PCP, PERFIL_FABRICA, PERFIL_TV)}
    db.commit()
    app = FastAPI()
    app.include_router(router, prefix="/api")

    def override_db():
        yield db

    app.dependency_overrides[get_gimak_db] = override_db
    client = TestClient(app)
    headers = {}
    for role, account in accounts.items():
        response = client.post("/api/gimak/auth/login", json={"username": account.username, "senha": "TestOnly@123"})
        assert response.status_code == 200
        headers[role] = {"Authorization": "Bearer " + response.json()["accessToken"]}
    return client, headers, accounts


def test_indicators_are_admin_only_and_period_is_validated(api):
    client, headers, _ = api
    assert client.get("/api/gimak/indicadores").status_code == 401
    for role in (PERFIL_PCP, PERFIL_FABRICA, PERFIL_TV):
        assert client.get("/api/gimak/indicadores", headers=headers[role]).status_code == 403
    assert client.get("/api/gimak/indicadores", headers=headers[PERFIL_ADMIN]).status_code == 200
    for params in ({"inicio": "2026-09-12", "fim": "2026-09-11"},
                   {"inicio": "2024-01-01", "fim": "2025-01-01"}, {"inicio": "bad-date"}):
        assert client.get("/api/gimak/indicadores", headers=headers[PERFIL_ADMIN], params=params).status_code == 422


def test_tv_is_read_only_has_long_session_and_does_not_receive_private_metrics(api, db):
    client, headers, _ = api
    item = task(db, state="paused", motivo="Justificativa privada", observacao="Observação privada")
    db.commit()
    tv_headers = headers[PERFIL_TV]
    token_body = tv_headers["Authorization"].split()[1].split(".")[0]
    token_payload = json.loads(base64.urlsafe_b64decode(token_body + "=" * (-len(token_body) % 4)))
    assert token_payload["exp"] - token_payload["iat"] == 30 * 24 * 60 * 60
    assert client.get("/api/gimak/auth/me", headers=tv_headers).status_code == 200
    panel = client.get("/api/gimak/painel-tv", headers=tv_headers)
    assert panel.status_code == 200
    assert "ranking" not in panel.json() and "adesao" not in panel.json()
    assert "Justificativa privada" not in panel.text and "Observação privada" not in panel.text
    for route in ("usuarios", "projetos", "tarefas"):
        assert client.get(f"/api/gimak/{route}", headers=tv_headers).status_code == 403
    writes = [
        ("post", "usuarios", {"nome": "Outro", "username": "outro", "senha": "12345678", "perfil": "TV"}),
        ("post", "projetos", {"cliente": "Cliente", "equipamento": "Equipamento"}),
        ("post", "tarefas", {"titulo": "Teste", "responsavel": "Operador", "dataPlanejada": "2026-09-11"}),
        ("patch", f"tarefas/{item.id}", {"titulo": "Alterado"}),
        ("patch", f"tarefas/{item.id}/status", {"status": "doing"}),
        ("patch", "usuarios/1", {"nome": "Alterado"}),
        ("post", "usuarios/1/senha", {"senha": "12345678"}),
    ]
    for method, path, body in writes:
        assert getattr(client, method)(f"/api/gimak/{path}", headers=tv_headers, json=body).status_code == 403


def test_admin_can_create_tv_and_deactivation_revokes_its_session(api):
    client, headers, _ = api
    created = client.post("/api/gimak/usuarios", headers=headers[PERFIL_ADMIN], json={
        "nome": "TV Fábrica", "username": "tv-fabrica", "senha": "TestOnly@123", "perfil": "TV",
    })
    assert created.status_code == 201
    login = client.post("/api/gimak/auth/login", json={"username": "tv-fabrica", "senha": "TestOnly@123"})
    tv_headers = {"Authorization": "Bearer " + login.json()["accessToken"]}
    assert client.get("/api/gimak/painel-tv", headers=tv_headers).status_code == 200
    client.patch(f"/api/gimak/usuarios/{created.json()['id']}", headers=headers[PERFIL_ADMIN], json={"ativo": False})
    assert client.get("/api/gimak/painel-tv", headers=tv_headers).status_code == 401


def test_repeating_completion_preserves_time_and_history(api, db):
    client, headers, _ = api
    item = task(db, state="doing", startedAt=NOW)
    db.commit()
    first = client.patch(f"/api/gimak/tarefas/{item.id}/status", headers=headers[PERFIL_ADMIN], json={"status": "done"})
    second = client.patch(f"/api/gimak/tarefas/{item.id}/status", headers=headers[PERFIL_ADMIN], json={"status": "done"})
    assert first.status_code == second.status_code == 200
    assert first.json()["finishedAt"] == second.json()["finishedAt"]
    assert len(second.json()["historico"]) == 1

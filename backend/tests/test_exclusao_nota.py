from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth as auth_api
from app.api import cargas as cargas_api
from app.api import fiscal as fiscal_api
from app.api import pedidos as pedidos_api
from app.db.session import Base, get_db
from app.models.carga import Carga
from app.models.nota_fiscal import NotaFiscalDraft
from app.models.pedido import Pedido
from app.models.pedido_historico import PedidoHistorico
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
    app.include_router(cargas_api.router, prefix="/api")
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

    liberado = client.patch(f"/api/pedidos/{pedido_id}/status", headers=pcp, json={"status": "Pronto para retirada"})
    assert liberado.status_code == 200, liberado.text
    return pedido_id


def test_excluir_nota_emitida_no_fiscal_cancela_pedido_e_devolve_estoque():
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
        historico = db.scalars(
            select(PedidoHistorico).where(PedidoHistorico.pedidoId == pedido_id).order_by(PedidoHistorico.id.desc())
        ).first()
        assert pedido.status == "Cancelado"
        assert pedido.dataEmissao is None
        assert produto.estoqueAtual == 1000
        assert produto.estoqueReservado == 0
        assert db.scalars(select(NotaFiscalDraft)).all() == []
        assert historico.usuario == "fiscal"

    # Nota já excluída não pode ser excluída de novo.
    assert client.delete(f"/api/fiscal/notas/{nota_id}", headers=fiscal).status_code == 404


def test_excluir_rascunho_nao_emitido_nao_cancela_pedido():
    client, TestingSession = montar_app()
    pedido_id = criar_pedido_faturado(client)

    fiscal = logar(client, "fiscal")
    preparada = client.post(f"/api/fiscal/pedidos/{pedido_id}/preparar-nfe", headers=fiscal)
    assert preparada.status_code == 201, preparada.text

    excluida = client.delete(f"/api/fiscal/notas/{preparada.json()['id']}", headers=fiscal)
    assert excluida.status_code == 204, excluida.text

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        produto = db.scalars(select(Produto)).first()
        assert pedido.status == "Pronto para retirada"
        assert produto.estoqueAtual == 1000
        assert produto.estoqueReservado == 40
        assert db.scalars(select(NotaFiscalDraft)).all() == []


def test_faturamento_exclui_nota_emitida_cancela_pedido_e_apaga_rascunho():
    client, TestingSession = montar_app()
    pedido_id = criar_pedido_faturado(client)

    fiscal = logar(client, "fiscal")
    preparada = client.post(f"/api/fiscal/pedidos/{pedido_id}/preparar-nfe", headers=fiscal)
    assert preparada.status_code == 201, preparada.text

    faturamento = logar(client, "faturamento")
    emitida = client.patch(f"/api/pedidos/{pedido_id}/status", headers=faturamento, json={"status": "Nota emitida", "numeroNota": "000123"})
    assert emitida.status_code == 200, emitida.text

    excluida = client.delete(f"/api/pedidos/{pedido_id}/nota", headers=faturamento)
    assert excluida.status_code == 204, excluida.text

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        produto = db.scalars(select(Produto)).first()
        assert pedido.status == "Cancelado"
        assert pedido.dataEmissao is None
        assert produto.estoqueAtual == 1000
        assert produto.estoqueReservado == 0
        assert db.scalars(select(NotaFiscalDraft)).all() == []

    # Sem nota emitida o endpoint recusa a exclusão.
    repetida = client.delete(f"/api/pedidos/{pedido_id}/nota", headers=faturamento)
    assert repetida.status_code == 409, repetida.text


def test_faturamento_exclui_pedido_ainda_nao_faturado():
    client, TestingSession = montar_app()
    pedido_id = criar_pedido_faturado(client)

    faturamento = logar(client, "faturamento")
    excluido = client.delete(f"/api/pedidos/{pedido_id}", headers=faturamento)
    assert excluido.status_code == 204, excluido.text

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        produto = db.scalars(select(Produto)).first()
        assert pedido.status == "Cancelado"
        assert produto.estoqueAtual == 1000
        assert produto.estoqueReservado == 0


def test_qualquer_usuario_cancela_pedido_faturado_pelo_endpoint_de_pedido():
    client, TestingSession = montar_app()
    pedido_id = criar_pedido_faturado(client)

    faturamento = logar(client, "faturamento")
    emitida = client.patch(f"/api/pedidos/{pedido_id}/status", headers=faturamento, json={"status": "Nota emitida", "numeroNota": "000123"})
    assert emitida.status_code == 200, emitida.text

    cancelado = client.delete(f"/api/pedidos/{pedido_id}", headers=faturamento)
    assert cancelado.status_code == 204, cancelado.text

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        produto = db.scalars(select(Produto)).first()
        historico = db.scalars(
            select(PedidoHistorico).where(PedidoHistorico.pedidoId == pedido_id).order_by(PedidoHistorico.id.desc())
        ).first()
        assert pedido.status == "Cancelado"
        assert pedido.dataEmissao is None
        assert produto.estoqueAtual == 1000
        assert historico.tipo == "Cancelamento"
        assert historico.usuario == "faturamento"


def test_usuario_pode_cancelar_pedido_fora_da_etapa_do_seu_perfil():
    client, TestingSession = montar_app()
    comercial = logar(client, "comercial")
    criado = client.post(
        "/api/pedidos",
        headers=comercial,
        json={"cliente": "Cliente Novo", "produto": "5L", "quantidade": 10, "valor": 3, "vendedor": "Arthur"},
    )
    assert criado.status_code == 201, criado.text

    faturamento = logar(client, "faturamento")
    cancelado = client.delete(f"/api/pedidos/{criado.json()['id']}", headers=faturamento)
    assert cancelado.status_code == 204, cancelado.text
    assert client.delete(f"/api/pedidos/{criado.json()['id']}").status_code == 401

    with TestingSession() as db:
        pedido = db.get(Pedido, criado.json()["id"])
        historico = db.scalars(
            select(PedidoHistorico).where(PedidoHistorico.pedidoId == pedido.id).order_by(PedidoHistorico.id.desc())
        ).first()
        assert pedido.status == "Cancelado"
        assert historico.usuario == "faturamento"


def test_cancelar_pedido_montado_remove_da_carga_e_preserva_pedido():
    client, TestingSession = montar_app()
    comercial = logar(client, "comercial")
    criado = client.post(
        "/api/pedidos",
        headers=comercial,
        json={
            "cliente": "Cliente com carga",
            "produto": "5L",
            "quantidade": 10,
            "valor": 3,
            "vendedor": "Arthur",
            "tipoFrete": "CIF",
        },
    )
    assert criado.status_code == 201, criado.text
    pedido_id = criado.json()["id"]

    pcp = logar(client, "pcp")
    for status_novo in ["A produzir", "Em produção", "Prontos"]:
        avanco = client.patch(f"/api/pedidos/{pedido_id}/status", headers=pcp, json={"status": status_novo})
        assert avanco.status_code == 200, avanco.text

    carga = client.post(
        "/api/cargas",
        headers=pcp,
        json={"regiao": "Joinville", "motorista": "Eduardo", "placa": "ABC-1234", "pedidoIds": [pedido_id]},
    )
    assert carga.status_code == 201, carga.text
    assert carga.json()["pedidos"][0]["status"] == "Pronto para o envio"

    cancelado = client.delete(f"/api/pedidos/{pedido_id}", headers=pcp)
    assert cancelado.status_code == 204, cancelado.text
    assert client.get("/api/cargas", headers=pcp).json() == []

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        assert pedido is not None
        assert pedido.status == "Cancelado"
        assert pedido.cargas == []
        assert db.scalars(select(Carga)).all() == []


def test_excluir_carga_montada_devolve_pedido_para_prontos():
    client, TestingSession = montar_app()
    comercial = logar(client, "comercial")
    criado = client.post(
        "/api/pedidos",
        headers=comercial,
        json={
            "cliente": "Cliente da carga",
            "produto": "5L",
            "quantidade": 10,
            "valor": 3,
            "vendedor": "Arthur",
            "tipoFrete": "CIF",
        },
    )
    assert criado.status_code == 201, criado.text
    pedido_id = criado.json()["id"]

    pcp = logar(client, "pcp")
    for status_novo in ["A produzir", "Em produção", "Prontos"]:
        avanco = client.patch(f"/api/pedidos/{pedido_id}/status", headers=pcp, json={"status": status_novo})
        assert avanco.status_code == 200, avanco.text

    montada = client.post(
        "/api/cargas",
        headers=pcp,
        json={"regiao": "Joinville", "motorista": "Eduardo", "placa": "ABC-1234", "pedidoIds": [pedido_id]},
    )
    assert montada.status_code == 201, montada.text
    carga_id = montada.json()["id"]

    excluida = client.delete(f"/api/cargas/{carga_id}", headers=pcp)
    assert excluida.status_code == 204, excluida.text
    assert client.get("/api/cargas", headers=pcp).json() == []
    assert client.delete(f"/api/cargas/{carga_id}", headers=pcp).status_code == 404

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        produto = db.scalars(select(Produto)).first()
        historico = db.scalars(
            select(PedidoHistorico).where(PedidoHistorico.pedidoId == pedido_id).order_by(PedidoHistorico.id.desc())
        ).first()
        assert pedido is not None
        assert pedido.status == "Prontos"
        assert pedido.cargas == []
        assert produto.estoqueReservado == 10
        assert historico.deValor == "Pronto para o envio"
        assert historico.paraValor == "Prontos"
        assert historico.usuario == "pcp"


def test_reverter_status_da_emissao_devolve_estoque():
    client, TestingSession = montar_app()
    pedido_id = criar_pedido_faturado(client)

    faturamento = logar(client, "faturamento")
    emitida = client.patch(f"/api/pedidos/{pedido_id}/status", headers=faturamento, json={"status": "Nota emitida", "numeroNota": "000123"})
    assert emitida.status_code == 200, emitida.text

    revertida = client.patch(f"/api/pedidos/{pedido_id}/status", headers=faturamento, json={"status": "Pronto para retirada"})
    assert revertida.status_code == 200, revertida.text

    with TestingSession() as db:
        pedido = db.get(Pedido, pedido_id)
        produto = db.scalars(select(Produto)).first()
        assert pedido.dataEmissao is None
        assert produto.estoqueAtual == 1000
        assert produto.estoqueReservado == 40

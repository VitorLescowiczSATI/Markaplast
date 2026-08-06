from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth as auth_api
from app.api.deps import require_profiles
from app.db.session import Base, get_db
from app.models.usuario import Usuario
from app.services.auth import criar_token, hash_senha, ler_token, seed_usuarios, verificar_senha


def test_hash_de_senha_e_token_assinado():
    senha_hash = hash_senha("segredo", salt="salt-fixo")
    assert verificar_senha("segredo", senha_hash) is True
    assert verificar_senha("incorreta", senha_hash) is False

    usuario = Usuario(id=42, nome="PCP", username="pcp", senhaHash=senha_hash, perfil="PCP", ativo=True)
    token = criar_token(usuario, "segredo-do-token", 10)
    assert ler_token(token, "segredo-do-token") == 42

    corpo, assinatura = token.split(".", 1)
    token_adulterado = f"{corpo[:-1]}x.{assinatura}"
    try:
        ler_token(token_adulterado, "segredo-do-token")
        assert False, "Token adulterado deveria ser rejeitado"
    except ValueError:
        pass


def test_login_sessao_e_bloqueio_por_perfil():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSession() as db:
        seed_usuarios(db, "Senha@123")
        assert len(db.scalars(select(Usuario)).all()) == 9

    app = FastAPI()
    app.include_router(auth_api.router, prefix="/api")

    @app.get("/restrito", dependencies=[Depends(require_profiles("PCP"))])
    def restrito():
        return {"ok": True}

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)

    invalido = client.post("/api/auth/login", json={"username": "pcp", "senha": "errada"})
    assert invalido.status_code == 401

    login_pcp = client.post("/api/auth/login", json={"username": "pcp", "senha": "Senha@123"})
    assert login_pcp.status_code == 200
    token_pcp = login_pcp.json()["accessToken"]
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_pcp}"}).json()["perfil"] == "PCP"
    assert client.get("/restrito", headers={"Authorization": f"Bearer {token_pcp}"}).status_code == 200

    login_comercial = client.post("/api/auth/login", json={"username": "comercial", "senha": "Senha@123"})
    token_comercial = login_comercial.json()["accessToken"]
    assert client.get("/restrito", headers={"Authorization": f"Bearer {token_comercial}"}).status_code == 403
    assert client.get("/restrito").status_code == 401

import base64
import hashlib
import hmac
import json
import secrets
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.usuario import Usuario


PBKDF2_ITERATIONS = 210_000
PERFIS_INICIAIS = {
    "inteligencia": ("Inteligência", "Inteligência"),
    "comercial": ("Comercial", "Comercial"),
    "clientes": ("Clientes", "Clientes"),
    "estoque": ("Estoque", "Estoque"),
    "pcp": ("PCP", "PCP"),
    "logistica": ("Logística", "Logística"),
    "faturamento": ("Faturamento", "Faturamento"),
    "financeiro": ("Financeiro", "Financeiro"),
    "fiscal": ("Fiscal", "Fiscal"),
}


def hash_senha(senha: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("ascii"), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        algoritmo, iteracoes, salt, esperado = senha_hash.split("$", 3)
        if algoritmo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("ascii"), int(iteracoes))
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(digest.hex(), esperado)


def _b64encode(conteudo: bytes) -> str:
    return base64.urlsafe_b64encode(conteudo).rstrip(b"=").decode("ascii")


def _b64decode(conteudo: str) -> bytes:
    return base64.urlsafe_b64decode(conteudo + "=" * (-len(conteudo) % 4))


def criar_token(usuario: Usuario, segredo: str, duracao_minutos: int) -> str:
    agora = int(time.time())
    payload = {
        "sub": str(usuario.id),
        "iat": agora,
        "exp": agora + max(1, duracao_minutos) * 60,
    }
    corpo = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    assinatura = hmac.new(segredo.encode("utf-8"), corpo.encode("ascii"), hashlib.sha256).digest()
    return f"{corpo}.{_b64encode(assinatura)}"


def ler_token(token: str, segredo: str) -> int:
    try:
        corpo, assinatura_recebida = token.split(".", 1)
        assinatura = hmac.new(segredo.encode("utf-8"), corpo.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(assinatura, _b64decode(assinatura_recebida)):
            raise ValueError("Assinatura inválida")
        payload = json.loads(_b64decode(corpo))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("Sessão expirada")
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Sessão inválida ou expirada") from exc


def seed_usuarios(db: Session, senha_inicial: str) -> None:
    existentes = {usuario.username: usuario for usuario in db.scalars(select(Usuario)).all()}
    faltantes = set(PERFIS_INICIAIS) - set(existentes)
    if faltantes and not senha_inicial:
        raise RuntimeError("AUTH_INITIAL_PASSWORD precisa ser configurada para criar os acessos iniciais")

    alterou = False
    for username, (nome, perfil) in PERFIS_INICIAIS.items():
        usuario = existentes.get(username)
        if usuario:
            if usuario.nome != nome or usuario.perfil != perfil:
                usuario.nome = nome
                usuario.perfil = perfil
                alterou = True
            continue
        db.add(
            Usuario(
                nome=nome,
                username=username,
                senhaHash=hash_senha(senha_inicial),
                perfil=perfil,
                ativo=True,
            )
        )
        alterou = True
    if alterou:
        db.commit()

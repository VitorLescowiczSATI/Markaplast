import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.produto import Produto


PRODUTOS_INICIAIS = [
    "1L sem alça",
    "1L redondo",
    "1L oval",
    "1L agro",
    "1L dosador",
    "2L redondo",
    "2L quadrado",
    "3L",
    "5L M2",
    "5L M4",
    "5L M6",
    "5L M8",
    "20L",
    "25L",
    "Pote de soda 300g",
    "Pote de soda 500g",
    "Pote de soda 1kg",
    "Pote normal 500g",
]


def derivar_atributos(nome: str) -> dict:
    """Deriva capacidade/modelo/peso/alça a partir do nome do produto.

    Heurística só para popular o catálogo inicial; o cliente refina depois.
    """
    nome = (nome or "").strip()
    low = nome.lower()
    attrs = {"capacidade": "", "modelo": "", "peso": "", "alca": "nao"}

    if re.search(r"com\s+al[çc]a", low):
        attrs["alca"] = "sim"
    elif re.search(r"sem\s+al[çc]a", low):
        attrs["alca"] = "nao"

    litros = re.match(r"^(\d+)\s*L\b", nome, re.IGNORECASE)
    if litros:
        attrs["capacidade"] = f"{litros.group(1)}L"
        resto = nome[litros.end():]
        resto = re.sub(r"(?i)\b(sem|com)\s+al[çc]a\b", "", resto).strip()
        attrs["modelo"] = resto

    peso = re.search(r"(\d+)\s*(kg|g)\b", nome, re.IGNORECASE)
    if peso:
        attrs["peso"] = f"{peso.group(1)}{peso.group(2).lower()}"

    if low.startswith("pote"):
        modelo = re.match(r"(?i)pote\s+(?:de\s+)?(\w+)", nome)
        if modelo:
            attrs["modelo"] = modelo.group(1)

    return attrs


def seed_produtos(db: Session) -> None:
    existentes = set(db.scalars(select(Produto.nome)).all())
    for nome in PRODUTOS_INICIAIS:
        if nome in existentes:
            continue
        attrs = derivar_atributos(nome)
        db.add(
            Produto(
                nome=nome,
                categoria="Embalagem" if not nome.startswith("Pote") else "Pote",
                capacidade=attrs["capacidade"],
                modelo=attrs["modelo"],
                peso=attrs["peso"],
                alca=attrs["alca"],
                estoqueAtual=0,
                estoqueReservado=0,
                estoqueMinimo=0,
            )
        )
    db.commit()
    backfill_produto_atributos(db)


def backfill_produto_atributos(db: Session) -> None:
    """Preenche atributos derivados em produtos que ainda não foram estruturados.

    Só toca linhas onde capacidade/modelo/peso estão todos vazios, pra não
    sobrescrever ajustes manuais feitos pelo cliente.
    """
    nao_estruturados = db.scalars(
        select(Produto).where(
            Produto.capacidade == "",
            Produto.modelo == "",
            Produto.peso == "",
        )
    ).all()
    alterou = False
    for produto in nao_estruturados:
        attrs = derivar_atributos(produto.nome)
        if not any(attrs[campo] for campo in ("capacidade", "modelo", "peso")):
            continue
        produto.capacidade = attrs["capacidade"]
        produto.modelo = attrs["modelo"]
        produto.peso = attrs["peso"]
        # Nunca rebaixa uma alça setada à mão: só promove p/ "sim" quando o nome indica alça.
        if attrs["alca"] == "sim":
            produto.alca = "sim"
        alterou = True
    if alterou:
        db.commit()

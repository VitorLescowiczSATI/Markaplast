from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.produto import MovimentoEstoque, Produto
from app.schemas.produto import MovimentoEstoqueCreate, MovimentoEstoqueRead, ProdutoCreate, ProdutoRead, ProdutoUpdate
from app.services.estoque import registrar_movimento

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get("", response_model=list[ProdutoRead])
def listar_produtos(db: Session = Depends(get_db)):
    return db.scalars(select(Produto).order_by(Produto.nome)).all()


@router.post("", response_model=ProdutoRead, status_code=status.HTTP_201_CREATED)
def criar_produto(payload: ProdutoCreate, db: Session = Depends(get_db)):
    produto = Produto(**payload.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.patch("/{produto_id}", response_model=ProdutoRead)
def atualizar_produto(produto_id: int, payload: ProdutoUpdate, db: Session = Depends(get_db)):
    produto = db.get(Produto, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(produto, key, value)
    db.commit()
    db.refresh(produto)
    return produto


@router.post("/{produto_id}/movimentos", response_model=MovimentoEstoqueRead, status_code=status.HTTP_201_CREATED)
def criar_movimento(produto_id: int, payload: MovimentoEstoqueCreate, db: Session = Depends(get_db)):
    produto = db.get(Produto, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    movimento = registrar_movimento(
        db,
        produto,
        payload.tipo,
        payload.quantidade,
        observacao=payload.observacao,
    )
    db.commit()
    db.refresh(movimento)
    return movimento


@router.get("/{produto_id}/movimentos", response_model=list[MovimentoEstoqueRead])
def listar_movimentos(produto_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(MovimentoEstoque)
        .where(MovimentoEstoque.produtoId == produto_id)
        .order_by(MovimentoEstoque.id.desc())
        .limit(50)
    ).all()

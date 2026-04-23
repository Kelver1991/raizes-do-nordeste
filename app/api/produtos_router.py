from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.infrastructure.database import get_db
from app.domain.models import Produto, PerfilEnum
from app.api.auth_router import get_usuario_atual

router = APIRouter(prefix="/produtos", tags=["Produtos"])

# ==================== SCHEMAS ====================

class ProdutoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    ativo: Optional[bool] = None

# ==================== ENDPOINTS ====================

@router.post("/", status_code=201)
def criar_produto(dados: ProdutoCreate, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in [PerfilEnum.ADMIN, PerfilEnum.GERENTE]:
        raise HTTPException(status_code=403, detail="Sem permissão para criar produto")
    produto = Produto(nome=dados.nome, descricao=dados.descricao, preco=dados.preco)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto

@router.get("/")
def listar_produtos(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    offset = (page - 1) * limit
    produtos = db.query(Produto).filter(Produto.ativo == True).offset(offset).limit(limit).all()
    total = db.query(Produto).filter(Produto.ativo == True).count()
    return {"total": total, "page": page, "limit": limit, "produtos": produtos}

@router.get("/{id}")
def buscar_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.put("/{id}")
def atualizar_produto(id: int, dados: ProdutoUpdate, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in [PerfilEnum.ADMIN, PerfilEnum.GERENTE]:
        raise HTTPException(status_code=403, detail="Sem permissão para atualizar produto")
    produto = db.query(Produto).filter(Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if dados.nome: produto.nome = dados.nome
    if dados.descricao: produto.descricao = dados.descricao
    if dados.preco: produto.preco = dados.preco
    if dados.ativo is not None: produto.ativo = dados.ativo
    db.commit()
    db.refresh(produto)
    return produto

@router.delete("/{id}", status_code=204)
def deletar_produto(id: int, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in [PerfilEnum.ADMIN, PerfilEnum.GERENTE]:
        raise HTTPException(status_code=403, detail="Sem permissão para deletar produto")
    produto = db.query(Produto).filter(Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    produto.ativo = False
    db.commit()
    return None
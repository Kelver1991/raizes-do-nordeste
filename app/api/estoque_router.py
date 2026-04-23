from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.infrastructure.database import get_db
from app.domain.models import Estoque, Produto, Unidade, PerfilEnum
from app.api.auth_router import get_usuario_atual

router = APIRouter(prefix="/estoque", tags=["Estoque"])

# ==================== SCHEMAS ====================

class EstoqueMovimento(BaseModel):
    unidade_id: int
    produto_id: int
    quantidade: int

# ==================== ENDPOINTS ====================

@router.post("/entrada", status_code=201)
def entrada_estoque(dados: EstoqueMovimento, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in [PerfilEnum.ADMIN, PerfilEnum.GERENTE]:
        raise HTTPException(status_code=403, detail="Sem permissão para movimentar estoque")
    
    unidade = db.query(Unidade).filter(Unidade.id == dados.unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    
    produto = db.query(Produto).filter(Produto.id == dados.produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    estoque = db.query(Estoque).filter(
        Estoque.unidade_id == dados.unidade_id,
        Estoque.produto_id == dados.produto_id
    ).first()
    
    if estoque:
        estoque.quantidade += dados.quantidade
    else:
        estoque = Estoque(
            unidade_id=dados.unidade_id,
            produto_id=dados.produto_id,
            quantidade=dados.quantidade
        )
        db.add(estoque)
    
    db.commit()
    db.refresh(estoque)
    return {"message": "Estoque atualizado com sucesso!", "quantidade_atual": estoque.quantidade}

@router.post("/saida", status_code=200)
def saida_estoque(dados: EstoqueMovimento, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in [PerfilEnum.ADMIN, PerfilEnum.GERENTE]:
        raise HTTPException(status_code=403, detail="Sem permissão para movimentar estoque")
    
    estoque = db.query(Estoque).filter(
        Estoque.unidade_id == dados.unidade_id,
        Estoque.produto_id == dados.produto_id
    ).first()
    
    if not estoque or estoque.quantidade < dados.quantidade:
        raise HTTPException(status_code=409, detail="Estoque insuficiente")
    
    estoque.quantidade -= dados.quantidade
    db.commit()
    db.refresh(estoque)
    return {"message": "Saída registrada com sucesso!", "quantidade_atual": estoque.quantidade}

@router.get("/unidade/{unidade_id}")
def consultar_estoque_unidade(unidade_id: int, db: Session = Depends(get_db)):
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    
    estoques = db.query(Estoque).filter(Estoque.unidade_id == unidade_id).all()
    return {
        "unidade_id": unidade_id,
        "unidade_nome": unidade.nome,
        "estoques": [
            {
                "produto_id": e.produto_id,
                "produto_nome": e.produto.nome,
                "quantidade": e.quantidade
            } for e in estoques
        ]
    }
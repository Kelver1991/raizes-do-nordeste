from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.infrastructure.database import get_db
from app.domain.models import Pedido, ItemPedido, Estoque, Produto, Unidade, Pagamento, Fidelidade, CanalPedidoEnum, StatusPedidoEnum, PerfilEnum
from app.api.auth_router import get_usuario_atual

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

# ==================== SCHEMAS ====================

class ItemPedidoSchema(BaseModel):
    produto_id: int
    quantidade: int

class PedidoCreate(BaseModel):
    unidade_id: int
    canal_pedido: CanalPedidoEnum
    itens: List[ItemPedidoSchema]
    forma_pagamento: str

class StatusUpdate(BaseModel):
    status: StatusPedidoEnum

# ==================== ENDPOINTS ====================

@router.post("/", status_code=201)
def criar_pedido(dados: PedidoCreate, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    unidade = db.query(Unidade).filter(Unidade.id == dados.unidade_id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    
    total = 0.0
    itens_validados = []
    
    for item in dados.itens:
        produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto {item.produto_id} não encontrado")
        
        estoque = db.query(Estoque).filter(
            Estoque.unidade_id == dados.unidade_id,
            Estoque.produto_id == item.produto_id
        ).first()
        
        if not estoque or estoque.quantidade < item.quantidade:
            raise HTTPException(status_code=409, detail=f"Estoque insuficiente para o produto {produto.nome}")
        
        total += produto.preco * item.quantidade
        itens_validados.append((produto, item.quantidade, estoque))
    
    pedido = Pedido(
        cliente_id=usuario.id,
        unidade_id=dados.unidade_id,
        canal_pedido=dados.canal_pedido,
        total=total
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    
    for produto, quantidade, estoque in itens_validados:
        item_pedido = ItemPedido(
            pedido_id=pedido.id,
            produto_id=produto.id,
            quantidade=quantidade,
            preco_unitario=produto.preco
        )
        db.add(item_pedido)
        estoque.quantidade -= quantidade
    
    db.commit()
    
    pagamento = Pagamento(
        pedido_id=pedido.id,
        status="PENDENTE",
        forma_pagamento=dados.forma_pagamento,
        valor=total
    )
    db.add(pagamento)
    db.commit()
    
    fidelidade = db.query(Fidelidade).filter(Fidelidade.cliente_id == usuario.id).first()
    if fidelidade:
        pontos_ganhos = int(total / 10)
        fidelidade.pontos += pontos_ganhos
        db.commit()
    
    return {
        "pedido_id": pedido.id,
        "status": pedido.status,
        "canal_pedido": pedido.canal_pedido,
        "total": pedido.total,
        "itens": [{"produto_id": p.id, "quantidade": q, "preco_unitario": p.preco} for p, q, e in itens_validados],
        "pagamento_status": "PENDENTE"
    }

@router.get("/")
def listar_pedidos(canal_pedido: Optional[CanalPedidoEnum] = None, status: Optional[StatusPedidoEnum] = None, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    query = db.query(Pedido)
    if usuario.perfil == PerfilEnum.CLIENTE:
        query = query.filter(Pedido.cliente_id == usuario.id)
    if canal_pedido:
        query = query.filter(Pedido.canal_pedido == canal_pedido)
    if status:
        query = query.filter(Pedido.status == status)
    return query.all()

@router.get("/{id}")
def buscar_pedido(id: int, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if usuario.perfil == PerfilEnum.CLIENTE and pedido.cliente_id != usuario.id:
        raise HTTPException(status_code=403, detail="Sem permissão para ver este pedido")
    return pedido

@router.patch("/{id}/status")
def atualizar_status(id: int, dados: StatusUpdate, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in [PerfilEnum.ADMIN, PerfilEnum.GERENTE, PerfilEnum.COZINHA, PerfilEnum.ATENDENTE]:
        raise HTTPException(status_code=403, detail="Sem permissão para atualizar status")
    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    pedido.status = dados.status
    db.commit()
    db.refresh(pedido)
    return {"message": "Status atualizado!", "pedido_id": pedido.id, "novo_status": pedido.status}

@router.patch("/{id}/cancelar")
def cancelar_pedido(id: int, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if usuario.perfil == PerfilEnum.CLIENTE and pedido.cliente_id != usuario.id:
        raise HTTPException(status_code=403, detail="Sem permissão para cancelar este pedido")
    if pedido.status in [StatusPedidoEnum.ENTREGUE, StatusPedidoEnum.CANCELADO]:
        raise HTTPException(status_code=409, detail="Pedido não pode ser cancelado")
    pedido.status = StatusPedidoEnum.CANCELADO
    db.commit()
    return {"message": "Pedido cancelado com sucesso!", "pedido_id": pedido.id}
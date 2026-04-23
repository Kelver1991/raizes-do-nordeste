from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.infrastructure.database import get_db
from app.domain.models import Pagamento, Pedido, StatusPedidoEnum
from app.api.auth_router import get_usuario_atual
import random

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

# ==================== SCHEMAS ====================

class PagamentoRequest(BaseModel):
    pedido_id: int
    forma_pagamento: str

# ==================== ENDPOINTS ====================

@router.post("/processar")
def processar_pagamento(dados: PagamentoRequest, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    pedido = db.query(Pedido).filter(Pedido.id == dados.pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    if pedido.cliente_id != usuario.id:
        raise HTTPException(status_code=403, detail="Sem permissão para pagar este pedido")
    
    if pedido.status != StatusPedidoEnum.AGUARDANDO_PAGAMENTO:
        raise HTTPException(status_code=409, detail="Pedido não está aguardando pagamento")
    
    pagamento = db.query(Pagamento).filter(Pagamento.pedido_id == dados.pedido_id).first()
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    
    # MOCK — Simulação de pagamento (90% aprovado, 10% recusado)
    aprovado = random.random() > 0.1
    
    if aprovado:
        pagamento.status = "APROVADO"
        pedido.status = StatusPedidoEnum.EM_PREPARO
        db.commit()
        return {
            "message": "Pagamento aprovado!",
            "pedido_id": pedido.id,
            "status_pagamento": "APROVADO",
            "status_pedido": "EM_PREPARO",
            "valor": pagamento.valor
        }
    else:
        pagamento.status = "RECUSADO"
        db.commit()
        raise HTTPException(
            status_code=402,
            detail={
                "error": "PAGAMENTO_RECUSADO",
                "message": "Pagamento recusado pela operadora",
                "pedido_id": pedido.id,
                "status_pagamento": "RECUSADO"
            }
        )

@router.get("/{pedido_id}")
def consultar_pagamento(pedido_id: int, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    pagamento = db.query(Pagamento).filter(Pagamento.pedido_id == pedido_id).first()
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return {
        "pedido_id": pedido_id,
        "status": pagamento.status,
        "forma_pagamento": pagamento.forma_pagamento,
        "valor": pagamento.valor,
        "criado_em": pagamento.criado_em
    }
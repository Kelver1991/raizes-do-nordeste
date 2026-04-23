from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.infrastructure.database import get_db
from app.domain.models import Fidelidade, PerfilEnum
from app.api.auth_router import get_usuario_atual

router = APIRouter(prefix="/fidelidade", tags=["Fidelidade"])

# ==================== SCHEMAS ====================

class ResgateRequest(BaseModel):
    pontos: int

# ==================== ENDPOINTS ====================

@router.get("/saldo")
def consultar_saldo(db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    fidelidade = db.query(Fidelidade).filter(Fidelidade.cliente_id == usuario.id).first()
    if not fidelidade:
        raise HTTPException(status_code=404, detail="Programa de fidelidade não encontrado")
    return {
        "cliente_id": usuario.id,
        "nome": usuario.nome,
        "pontos": fidelidade.pontos
    }

@router.post("/resgatar")
def resgatar_pontos(dados: ResgateRequest, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    fidelidade = db.query(Fidelidade).filter(Fidelidade.cliente_id == usuario.id).first()
    if not fidelidade:
        raise HTTPException(status_code=404, detail="Programa de fidelidade não encontrado")
    if fidelidade.pontos < dados.pontos:
        raise HTTPException(status_code=409, detail="Pontos insuficientes para resgate")
    fidelidade.pontos -= dados.pontos
    db.commit()
    return {
        "message": "Pontos resgatados com sucesso!",
        "pontos_resgatados": dados.pontos,
        "saldo_atual": fidelidade.pontos
    }

@router.get("/admin/todos")
def listar_todos(db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in [PerfilEnum.ADMIN, PerfilEnum.GERENTE]:
        raise HTTPException(status_code=403, detail="Sem permissão para ver todos os programas")
    fidelidades = db.query(Fidelidade).all()
    return fidelidades
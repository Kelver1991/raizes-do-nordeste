from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.infrastructure.database import get_db
from app.domain.models import Unidade
from app.api.auth_router import get_usuario_atual
from app.domain.models import PerfilEnum

router = APIRouter(prefix="/unidades", tags=["Unidades"])

# ==================== SCHEMAS ====================

class UnidadeCreate(BaseModel):
    nome: str
    endereco: str

class UnidadeUpdate(BaseModel):
    nome: str = None
    endereco: str = None
    ativa: bool = None

# ==================== ENDPOINTS ====================

@router.post("/", status_code=201)
def criar_unidade(dados: UnidadeCreate, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in [PerfilEnum.ADMIN, PerfilEnum.GERENTE]:
        raise HTTPException(status_code=403, detail="Sem permissão para criar unidade")
    unidade = Unidade(nome=dados.nome, endereco=dados.endereco)
    db.add(unidade)
    db.commit()
    db.refresh(unidade)
    return unidade

@router.get("/")
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(Unidade).filter(Unidade.ativa == True).all()

@router.get("/{id}")
def buscar_unidade(id: int, db: Session = Depends(get_db)):
    unidade = db.query(Unidade).filter(Unidade.id == id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    return unidade

@router.put("/{id}")
def atualizar_unidade(id: int, dados: UnidadeUpdate, db: Session = Depends(get_db), usuario=Depends(get_usuario_atual)):
    if usuario.perfil not in [PerfilEnum.ADMIN, PerfilEnum.GERENTE]:
        raise HTTPException(status_code=403, detail="Sem permissão para atualizar unidade")
    unidade = db.query(Unidade).filter(Unidade.id == id).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    if dados.nome: unidade.nome = dados.nome
    if dados.endereco: unidade.endereco = dados.endereco
    if dados.ativa is not None: unidade.ativa = dados.ativa
    db.commit()
    db.refresh(unidade)
    return unidade
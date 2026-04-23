from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.infrastructure.database import get_db
from app.domain.models import Usuario, PerfilEnum, Fidelidade
from app.application.auth import verificar_senha, gerar_hash_senha, criar_token, verificar_token
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/auth", tags=["Autenticação"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ==================== SCHEMAS ====================

class UsuarioRegistro(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    perfil: PerfilEnum = PerfilEnum.CLIENTE
    consentimento_lgpd: bool

class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str

# ==================== DEPENDÊNCIA ====================

def get_usuario_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    dados = verificar_token(token)
    if not dados:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    usuario = db.query(Usuario).filter(Usuario.email == dados["email"]).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

# ==================== ENDPOINTS ====================

@router.post("/registrar", status_code=201)
def registrar(dados: UsuarioRegistro, db: Session = Depends(get_db)):
    if not dados.consentimento_lgpd:
        raise HTTPException(
            status_code=400,
            detail="É necessário aceitar os termos de uso e política de privacidade (LGPD)"
        )
    usuario_existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario_existente:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        perfil=dados.perfil,
        consentimento_lgpd=dados.consentimento_lgpd
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    fidelidade = Fidelidade(cliente_id=novo_usuario.id)
    db.add(fidelidade)
    db.commit()
    return {
        "message": "Usuário cadastrado com sucesso!",
        "id": novo_usuario.id,
        "nome": novo_usuario.nome,
        "email": novo_usuario.email,
        "perfil": novo_usuario.perfil
    }

@router.post("/login")
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos"
        )
    token = criar_token({"sub": usuario.email, "perfil": usuario.perfil})
    return {
        "accessToken": token,
        "tokenType": "Bearer",
        "expiresIn": 3600,
        "user": {
            "id": usuario.id,
            "nome": usuario.nome,
            "perfil": usuario.perfil
        }
    }

@router.get("/perfil")
def perfil(usuario_atual: Usuario = Depends(get_usuario_atual)):
    return {
        "id": usuario_atual.id,
        "nome": usuario_atual.nome,
        "email": usuario_atual.email,
        "perfil": usuario_atual.perfil
    }
from fastapi import FastAPI
from app.infrastructure.database import Base, engine
from app.domain import models
from app.api import auth_router, unidades_router, produtos_router, estoque_router, pedidos_router, pagamentos_router, fidelidade_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Raizes do Nordeste API",
    description="API do sistema de gestao da rede de restaurantes Raizes do Nordeste",
    version="1.0.0"
)

app.include_router(auth_router.router)
app.include_router(unidades_router.router)
app.include_router(produtos_router.router)
app.include_router(estoque_router.router)
app.include_router(pedidos_router.router)
app.include_router(pagamentos_router.router)
app.include_router(fidelidade_router.router)

@app.get("/")
def root():
    return {"message": "Bem-vindo a API Raizes do Nordeste!"}

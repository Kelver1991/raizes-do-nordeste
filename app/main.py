from fastapi import FastAPI
from app.infrastructure.database import Base, engine
from app.domain import models
from app.api import auth_router, unidades_router, produtos_router, estoque_router, pedidos_router, pagamentos_router, fidelidade_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Raízes do Nordeste API",
    description="API do sistema de gestão da rede de restaurantes Raízes do Nordeste",
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
    return {"message": "Bem-vindo à API Raízes do Nordeste!"}
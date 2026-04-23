from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database import Base
import enum

# ==================== ENUMS ====================

class PerfilEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    GERENTE = "GERENTE"
    CLIENTE = "CLIENTE"
    COZINHA = "COZINHA"
    ATENDENTE = "ATENDENTE"

class CanalPedidoEnum(str, enum.Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"

class StatusPedidoEnum(str, enum.Enum):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    PAGO = "PAGO"
    EM_PREPARO = "EM_PREPARO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"

# ==================== TABELAS ====================

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum(PerfilEnum), default=PerfilEnum.CLIENTE)
    ativo = Column(Boolean, default=True)
    consentimento_lgpd = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    pedidos = relationship("Pedido", back_populates="cliente")
    fidelidade = relationship("Fidelidade", back_populates="cliente", uselist=False)

class Unidade(Base):
    __tablename__ = "unidades"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    endereco = Column(String(255), nullable=False)
    ativa = Column(Boolean, default=True)
    produtos = relationship("Estoque", back_populates="unidade")
    pedidos = relationship("Pedido", back_populates="unidade")

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Float, nullable=False)
    ativo = Column(Boolean, default=True)
    estoques = relationship("Estoque", back_populates="produto")

class Estoque(Base):
    __tablename__ = "estoques"
    id = Column(Integer, primary_key=True, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, default=0)
    unidade = relationship("Unidade", back_populates="produtos")
    produto = relationship("Produto", back_populates="estoques")

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    canal_pedido = Column(Enum(CanalPedidoEnum), nullable=False)
    status = Column(Enum(StatusPedidoEnum), default=StatusPedidoEnum.AGUARDANDO_PAGAMENTO)
    total = Column(Float, default=0.0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    cliente = relationship("Usuario", back_populates="pedidos")
    unidade = relationship("Unidade", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido")
    pagamento = relationship("Pagamento", back_populates="pedido", uselist=False)

class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto")

class Pagamento(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    status = Column(String(50), default="PENDENTE")
    forma_pagamento = Column(String(50), nullable=False)
    valor = Column(Float, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    pedido = relationship("Pedido", back_populates="pagamento")

class Fidelidade(Base):
    __tablename__ = "fidelidade"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    pontos = Column(Integer, default=0)
    cliente = relationship("Usuario", back_populates="fidelidade")
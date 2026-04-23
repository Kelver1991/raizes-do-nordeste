# 🍽️ Raízes do Nordeste API

API Back-end do sistema de gestão da rede de restaurantes **Raízes do Nordeste**.

## 🚀 Tecnologias
- Python 3.14
- FastAPI
- MySQL 8.0
- SQLAlchemy
- JWT (python-jose)
- Swagger/OpenAPI

## ⚙️ Como executar

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/raizes-do-nordeste.git
cd raizes-do-nordeste
```

### 2. Crie o ambiente virtual
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instale as dependências
```bash
pip install fastapi uvicorn sqlalchemy pymysql python-jose passlib bcrypt==4.0.1 python-dotenv pydantic[email]
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
"""Aplicación FastAPI principal para la V1 de gestión de ventas."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

from app.auth.routes import router as auth_router
from app.clients import models as _client_models  # Registrar modelos ORM antes de create_all.
from app.clients.routes import router as clients_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.error_handlers import register_exception_handlers
from app.products import models as _product_models
from app.products.routes import router as products_router
from app.sales import models as _sales_models
from app.sales.routes import router as sales_router
from app.users import models as _user_models
from app.users.services import seed_bootstrap_admin


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Inicializa el esquema solo cuando AUTO_CREATE_TABLES está habilitado."""
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    if settings.bootstrap_admin_password:
        with SessionLocal() as session:
            seed_bootstrap_admin(
                session,
                full_name=settings.bootstrap_admin_name,
                email=settings.bootstrap_admin_email,
                password=settings.bootstrap_admin_password,
            )
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "MVP de gestión de ventas con clientes, productos, inventario, ventas y autenticación JWT. "
        "La lógica de negocio se organiza en servicios por dominio."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
register_exception_handlers(app)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(clients_router, prefix="/api/v1/clientes", tags=["Clientes"])
app.include_router(products_router, prefix="/api/v1/productos", tags=["Productos"])
app.include_router(sales_router, prefix="/api/v1/ventas", tags=["Ventas"])


@app.get("/", tags=["Estado"])
def root() -> dict[str, str]:
    return {"mensaje": "Sistema de gestión de ventas operativo", "version": app.version}


@app.get("/health", tags=["Estado"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["Estado"])
def database_health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}

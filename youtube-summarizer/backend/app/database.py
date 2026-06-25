"""
Configuración de la base de datos con SQLAlchemy.
Soporta SQLite (desarrollo) y PostgreSQL (producción) según DATABASE_URL.
"""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import get_settings

settings = get_settings()

# SQLite necesita este flag para funcionar bien con FastAPI (múltiples hilos)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

if settings.DATABASE_URL.startswith("sqlite:///./"):
    db_path = Path(settings.DATABASE_URL.replace("sqlite:///./", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesión de DB y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea las tablas si no existen. Se llama en el startup de la app."""
    from . import models  # noqa: F401 (registra los modelos en Base)
    Base.metadata.create_all(bind=engine)

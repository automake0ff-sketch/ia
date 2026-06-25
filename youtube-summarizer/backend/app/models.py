"""
Modelos de base de datos (SQLAlchemy ORM).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from .database import Base


class SummaryHistory(Base):
    """Historial de resúmenes generados por los usuarios."""

    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, default="anonymous")
    video_url = Column(String, nullable=False)
    video_id = Column(String, index=True)
    title = Column(String)
    channel = Column(String)
    thumbnail_url = Column(String)
    language = Column(String, default="es")
    summary_type = Column(String, default="executive")
    summary = Column(Text)
    keywords = Column(Text)  # lista en formato JSON
    tags = Column(Text)  # lista en formato JSON
    sentiment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CacheEntry(Base):
    """Tabla usada como caché de respaldo cuando Redis no está disponible."""

    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

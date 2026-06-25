"""
Sistema de caché de resultados.

Estrategia:
- Si REDIS_URL está configurado y Redis responde, se usa Redis (rápido, ideal para producción).
- Si no, se usa una tabla SQLite/PostgreSQL (CacheEntry) como respaldo, para no depender
  de infraestructura adicional en desarrollo.

TTL configurable vía CACHE_TTL_DAYS (por defecto 7 días).
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from .config import get_settings

settings = get_settings()
logger = logging.getLogger("cache")

_redis_client = None
if settings.REDIS_URL:
    try:
        import redis as redis_lib

        _redis_client = redis_lib.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        _redis_client.ping()
        logger.info("Caché: usando Redis en %s", settings.REDIS_URL)
    except Exception as exc:
        logger.warning("Caché: no se pudo conectar a Redis (%s). Usando fallback SQLite.", exc)
        _redis_client = None
else:
    logger.info("Caché: REDIS_URL no configurado. Usando fallback SQLite.")


def make_cache_key(*parts: str) -> str:
    """Genera una clave de caché determinística a partir de varias partes."""
    raw = "::".join(str(p) for p in parts)
    return "yts:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CacheManager:
    """Abstracción de caché: Redis si está disponible, si no, SQLite/PostgreSQL."""

    def __init__(self):
        self.ttl_seconds = settings.CACHE_TTL_DAYS * 24 * 3600

    def get(self, key: str, db=None) -> Optional[Any]:
        if _redis_client is not None:
            try:
                raw = _redis_client.get(key)
                return json.loads(raw) if raw else None
            except Exception as exc:
                logger.warning("Error leyendo de Redis: %s", exc)
                return None

        if db is None:
            return None

        from .models import CacheEntry

        entry = db.query(CacheEntry).filter(CacheEntry.cache_key == key).first()
        if not entry:
            return None
        if entry.expires_at < datetime.utcnow():
            db.delete(entry)
            db.commit()
            return None
        return json.loads(entry.value)

    def set(self, key: str, value: Any, db=None) -> None:
        payload = json.dumps(value, ensure_ascii=False)

        if _redis_client is not None:
            try:
                _redis_client.setex(key, self.ttl_seconds, payload)
                return
            except Exception as exc:
                logger.warning("Error escribiendo en Redis: %s", exc)
                return

        if db is None:
            return

        from .models import CacheEntry

        expires_at = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
        entry = db.query(CacheEntry).filter(CacheEntry.cache_key == key).first()
        if entry:
            entry.value = payload
            entry.expires_at = expires_at
        else:
            entry = CacheEntry(cache_key=key, value=payload, expires_at=expires_at)
            db.add(entry)
        db.commit()

    def delete(self, key: str, db=None) -> None:
        if _redis_client is not None:
            try:
                _redis_client.delete(key)
            except Exception:
                pass
            return
        if db is None:
            return
        from .models import CacheEntry

        db.query(CacheEntry).filter(CacheEntry.cache_key == key).delete()
        db.commit()


cache_manager = CacheManager()

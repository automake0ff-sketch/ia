"""
FastAPI app entrypoint.

Configura logging, CORS, routers, base de datos, y sirve el frontend
estático (HTML/CSS/JS) desde la carpeta /frontend.
"""
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import init_db
from .routers import export, history, summarize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

origins = (
    ["*"]
    if settings.ALLOWED_ORIGINS == "*"
    else [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summarize.router)
app.include_router(history.router)
app.include_router(export.router)


@app.on_event("startup")
def on_startup() -> None:
    Path("./data").mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


# --- Servir el frontend estático ---
# En Docker el frontend se copia a /frontend; en desarrollo local se busca
# en ../frontend relativo a este archivo (backend/app/main.py -> proyecto/frontend).
def _resolve_frontend_dir() -> "Path | None":
    env_dir = os.environ.get("FRONTEND_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.append(Path("/frontend"))
    candidates.append(Path(__file__).resolve().parents[2] / "frontend")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


FRONTEND_DIR = _resolve_frontend_dir()

if FRONTEND_DIR is not None:
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    logging.getLogger("main").warning("No se encontró la carpeta del frontend; solo la API estará disponible.")

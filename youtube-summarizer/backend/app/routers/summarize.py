"""
Router: /api/summarize

Endpoint principal. Flujo:
  1. Valida y extrae el video_id de la URL.
  2. Revisa la caché (Redis o SQLite, TTL configurable).
  3. Si no hay caché, invoca al Agente Orquestador.
  4. Guarda el resultado en caché y en el historial del usuario.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..agents.orchestrator import OrchestratorAgent
from ..cache import cache_manager, make_cache_key
from ..database import get_db
from ..models import SummaryHistory
from ..schemas import SummarizeRequest, SummarizeResponse
from ..skills.summarize_with_gpt import SummarizationError
from ..skills.transcribe_youtube import TranscriptionError, extract_video_id

router = APIRouter(prefix="/api", tags=["summarize"])
orchestrator = OrchestratorAgent()


@router.post("/summarize", response_model=SummarizeResponse)
def summarize_video(payload: SummarizeRequest, db: Session = Depends(get_db)):
    try:
        video_id = extract_video_id(payload.video_url)
    except TranscriptionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    cache_key = make_cache_key(
        "summary", video_id, payload.language, payload.summary_type.value, payload.provider.value
    )

    if payload.use_cache:
        cached = cache_manager.get(cache_key, db=db)
        if cached:
            cached["cached"] = True
            return cached

    try:
        result = orchestrator.run(
            video_url=payload.video_url,
            summary_type=payload.summary_type.value,
            language=payload.language,
            provider=payload.provider.value,
            extra_languages=payload.extra_languages,
        )
    except TranscriptionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except SummarizationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error interno al procesar el video: {exc}")

    response_payload = {
        "video_id": result["video_id"],
        "video_url": result["video_url"],
        "title": result["title"],
        "channel": result["channel"],
        "thumbnail_url": result["thumbnail_url"],
        "language": result["language"],
        "summary_type": result["summary_type"],
        "summary": result["summary"],
        "keywords": result["keywords"],
        "tags": result["tags"],
        "topics": result["topics"],
        "sentiment": result["sentiment"],
        "entities": result["entities"],
        "translations": result["translations"],
        "validation": result["validation"],
        "cached": False,
        "processing_time_seconds": result["processing_time_seconds"],
    }

    history_entry = SummaryHistory(
        user_id=payload.user_id or "anonymous",
        video_url=payload.video_url,
        video_id=result["video_id"],
        title=result["title"],
        channel=result["channel"],
        thumbnail_url=result["thumbnail_url"],
        language=result["language"],
        summary_type=result["summary_type"],
        summary=result["summary"],
        keywords=json.dumps(result["keywords"], ensure_ascii=False),
        tags=json.dumps(result["tags"], ensure_ascii=False),
        sentiment=result["sentiment"],
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    response_payload["history_id"] = history_entry.id

    if payload.use_cache:
        cache_manager.set(cache_key, response_payload, db=db)

    return response_payload

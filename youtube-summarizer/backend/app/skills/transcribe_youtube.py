"""
Skill: transcribe_youtube

Extrae la transcripción de un video de YouTube, con manejo de errores y una
estrategia de fallback entre subtítulos manuales, auto-generados y traducidos.
También obtiene metadatos básicos (título, canal, miniatura) vía el endpoint
público oEmbed de YouTube, sin necesitar API key.
"""
import re
from typing import List, Optional

import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


class TranscriptionError(Exception):
    """Error de negocio al intentar transcribir un video."""


_VIDEO_ID_PATTERNS = [
    r"(?:v=)([0-9A-Za-z_-]{11})",
    r"youtu\.be/([0-9A-Za-z_-]{11})",
    r"shorts/([0-9A-Za-z_-]{11})",
    r"embed/([0-9A-Za-z_-]{11})",
]


def extract_video_id(video_url: str) -> str:
    """Soporta youtube.com/watch?v=, youtu.be/, /shorts/ y /embed/."""
    video_url = video_url.strip()
    # Si ya es un ID de 11 caracteres, lo devolvemos directo.
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", video_url):
        return video_url
    for pattern in _VIDEO_ID_PATTERNS:
        match = re.search(pattern, video_url)
        if match:
            return match.group(1)
    raise TranscriptionError(f"No se pudo extraer el ID del video desde la URL: {video_url}")


def fetch_metadata(video_id: str) -> dict:
    """Obtiene título, canal y miniatura usando el endpoint público oEmbed (sin API key)."""
    try:
        resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "title": data.get("title"),
            "channel": data.get("author_name"),
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        }
    except requests.RequestException:
        return {
            "title": None,
            "channel": None,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        }


def _segment_text(segment) -> str:
    """Compatibilidad con distintas versiones de youtube-transcript-api (dict u objeto)."""
    if isinstance(segment, dict):
        return segment.get("text", "")
    return getattr(segment, "text", "")


def _segment_to_dict(segment) -> dict:
    if isinstance(segment, dict):
        return {
            "text": segment.get("text", ""),
            "start": segment.get("start", 0),
            "duration": segment.get("duration", 0),
        }
    return {
        "text": getattr(segment, "text", ""),
        "start": getattr(segment, "start", 0),
        "duration": getattr(segment, "duration", 0),
    }


def transcribe_youtube(video_url: str, preferred_languages: Optional[List[str]] = None) -> dict:
    """
    Extrae la transcripción de un video de YouTube.

    Estrategia de fallback:
      1. Subtítulos manuales en los idiomas preferidos.
      2. Subtítulos auto-generados en los idiomas preferidos.
      3. Cualquier subtítulo disponible, traducido al idioma preferido si es posible.

    Returns:
        {
            "video_id": str, "text": str, "segments": list[dict],
            "language_code": str, "is_generated": bool,
            "metadata": {"title": str, "channel": str, "thumbnail_url": str},
        }
    """
    preferred_languages = preferred_languages or ["es", "en"]
    video_id = extract_video_id(video_url)
    metadata = fetch_metadata(video_id)

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except TranscriptsDisabled:
        raise TranscriptionError("Los subtítulos están deshabilitados para este video.")
    except VideoUnavailable:
        raise TranscriptionError("El video no está disponible (privado, eliminado o bloqueado en tu región).")
    except Exception as exc:
        raise TranscriptionError(f"Error al consultar las transcripciones disponibles: {exc}")

    transcript = None
    is_generated = False

    try:
        transcript = transcript_list.find_manually_created_transcript(preferred_languages)
    except NoTranscriptFound:
        pass

    if transcript is None:
        try:
            transcript = transcript_list.find_generated_transcript(preferred_languages)
            is_generated = True
        except NoTranscriptFound:
            pass

    if transcript is None:
        try:
            available = list(transcript_list)
            if not available:
                raise TranscriptionError("No hay transcripciones disponibles para este video.")
            base = available[0]
            if base.is_translatable:
                transcript = base.translate(preferred_languages[0])
            else:
                transcript = base
            is_generated = base.is_generated
        except TranscriptionError:
            raise
        except Exception as exc:
            raise TranscriptionError(f"No se encontró ninguna transcripción usable para este video: {exc}")

    try:
        raw_segments = transcript.fetch()
    except Exception as exc:
        raise TranscriptionError(f"Error al descargar el contenido de la transcripción: {exc}")

    segments = [_segment_to_dict(s) for s in raw_segments]
    full_text = " ".join(seg["text"].strip() for seg in segments if seg["text"])
    full_text = re.sub(r"\s+", " ", full_text).strip()

    if not full_text:
        raise TranscriptionError("La transcripción obtenida está vacía.")

    return {
        "video_id": video_id,
        "text": full_text,
        "segments": segments,
        "language_code": transcript.language_code,
        "is_generated": is_generated,
        "metadata": metadata,
    }

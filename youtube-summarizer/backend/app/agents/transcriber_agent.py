"""
Agente Transcriptor

Responsabilidad única: obtener la transcripción de un video de YouTube
(con su metadata básica) y normalizarla para los siguientes agentes del
pipeline (por ejemplo, truncando transcripciones demasiado largas).
"""
from typing import List, Optional

from ..config import get_settings
from ..skills.transcribe_youtube import TranscriptionError, transcribe_youtube
from .base import BaseAgent

settings = get_settings()


class TranscriberAgent(BaseAgent):
    name = "TranscriberAgent"

    def run(self, video_url: str, preferred_languages: Optional[List[str]] = None) -> dict:
        self.log_start(video_url)
        try:
            result = transcribe_youtube(video_url, preferred_languages)
        except TranscriptionError as exc:
            self.log_error(exc)
            raise

        text = result["text"]
        if len(text) > settings.MAX_TRANSCRIPT_CHARS:
            result["text"] = text[: settings.MAX_TRANSCRIPT_CHARS]
            result["truncated"] = True
        else:
            result["truncated"] = False

        self.log_end(f"video_id={result['video_id']} chars={len(result['text'])}")
        return result

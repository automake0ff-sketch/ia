"""
Agente Orquestador

Responsabilidad única: coordinar el flujo de trabajo completo entre todos
los agentes especializados para producir el resultado final de un video
de YouTube.

Flujo:
  1. TranscriberAgent  -> obtiene transcripción + metadatos básicos
  2. SummarizerAgent   -> genera el resumen según la estrategia elegida
  3. ValidatorAgent    -> valida la calidad del resumen (con reintento)
  4. ExtractorAgent    -> extrae keywords, temas, entidades, sentimiento, tags
  5. TranslatorAgent   -> (opcional) traduce el resumen a idiomas adicionales
"""
import time
from typing import List, Optional

from .base import BaseAgent
from .extractor_agent import ExtractorAgent
from .summarizer_agent import SummarizerAgent
from .transcriber_agent import TranscriberAgent
from .translator_agent import TranslatorAgent
from .validator_agent import ValidatorAgent


class OrchestratorAgent(BaseAgent):
    name = "OrchestratorAgent"

    def __init__(self):
        super().__init__()
        self.transcriber = TranscriberAgent()
        self.summarizer = SummarizerAgent()
        self.validator = ValidatorAgent()
        self.extractor = ExtractorAgent()
        self.translator = TranslatorAgent()

    def run(
        self,
        video_url: str,
        summary_type: str = "executive",
        language: str = "es",
        provider: str = "openai",
        extra_languages: Optional[List[str]] = None,
        max_validation_retries: int = 1,
    ) -> dict:
        start = time.time()
        self.log_start(video_url)

        # 1. Transcripción
        transcription = self.transcriber.run(video_url, preferred_languages=[language, "en"])
        title = transcription["metadata"].get("title") or ""

        # 2. Resumen
        summary_result = self.summarizer.run(
            transcript=transcription["text"],
            summary_type=summary_type,
            language=language,
            title=title,
            provider=provider,
        )
        summary = summary_result["summary"]

        # 3. Validación (con reintento limitado si falla)
        validation = self.validator.run(summary, summary_type)
        retries = 0
        while not validation["is_valid"] and retries < max_validation_retries:
            self.logger.warning("Resumen no válido (intento %s), regenerando...", retries + 1)
            summary_result = self.summarizer.run(
                transcript=transcription["text"],
                summary_type=summary_type,
                language=language,
                title=title,
                provider=provider,
            )
            summary = summary_result["summary"]
            validation = self.validator.run(summary, summary_type)
            retries += 1

        # 4. Extracción de metadatos enriquecidos
        extraction = self.extractor.run(transcription["text"], language=language, provider=provider)

        # 5. Traducciones opcionales
        translations = {}
        if extra_languages:
            targets = [lang for lang in extra_languages if lang != language]
            if targets:
                translation_result = self.translator.run(summary, targets, provider=provider)
                translations = translation_result["translations"]

        elapsed = time.time() - start
        self.log_end(f"elapsed={elapsed:.2f}s retries={retries}")

        return {
            "video_id": transcription["video_id"],
            "video_url": video_url,
            "title": transcription["metadata"].get("title"),
            "channel": transcription["metadata"].get("channel"),
            "thumbnail_url": transcription["metadata"].get("thumbnail_url"),
            "language": language,
            "summary_type": summary_type,
            "summary": summary,
            "provider_used": summary_result["provider_used"],
            "keywords": extraction["keywords"],
            "topics": extraction["topics"],
            "entities": extraction["entities"],
            "sentiment": extraction["sentiment"],
            "tags": extraction["tags"],
            "validation": validation,
            "translations": translations,
            "transcript_is_generated": transcription["is_generated"],
            "transcript_truncated": transcription["truncated"],
            "processing_time_seconds": round(elapsed, 2),
        }

"""
Agente Extractor

Responsabilidad única: extraer metadatos enriquecidos del contenido del
video: palabras clave, temas principales, entidades nombradas (personas,
organizaciones, lugares), sentimiento general y tags. También detecta el
idioma real de la transcripción (independientemente del idioma elegido
para el resumen).
"""
from ..skills.detect_language import detect_language
from ..skills.extract_keywords import ExtractionError, extract_keywords
from ..skills.generate_tags import generate_tags
from .base import BaseAgent


class ExtractorAgent(BaseAgent):
    name = "ExtractorAgent"

    def run(self, text: str, language: str = "es", provider: str = "openai") -> dict:
        self.log_start(f"lang={language}")

        detected = detect_language(text)

        try:
            analysis = extract_keywords(text, language=language, provider=provider)
        except ExtractionError as exc:
            self.log_error(exc)
            analysis = {
                "keywords": [],
                "topics": [],
                "entities": {"people": [], "organizations": [], "places": []},
                "sentiment": "neutral",
                "tags": [],
            }

        tags = generate_tags(analysis=analysis, language=language, provider=provider)

        self.log_end(f"keywords={len(analysis.get('keywords', []))} tags={len(tags)}")
        return {
            "detected_language": detected,
            "keywords": analysis.get("keywords", []),
            "topics": analysis.get("topics", []),
            "entities": analysis.get("entities", {}),
            "sentiment": analysis.get("sentiment", "neutral"),
            "tags": tags,
        }

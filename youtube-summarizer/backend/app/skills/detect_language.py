"""
Skill: detect_language

Detecta el idioma de un texto usando `langdetect` (rápido, local, sin costo
de API). Se usa principalmente sobre la transcripción para decisiones internas
del pipeline (por ejemplo, elegir el idioma de origen antes de resumir).
"""
from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0  # resultados deterministas

LANGUAGE_NAMES = {
    "es": "Spanish",
    "en": "English",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
}


def detect_language(text: str) -> dict:
    """
    Detecta el idioma de un texto.

    Returns: {"code": "es", "name": "Spanish", "confidence": "high" | "low"}
    """
    if not text or len(text.strip()) < 20:
        return {"code": "unknown", "name": "Unknown", "confidence": "low"}
    try:
        code = detect(text[:5000])
        name = LANGUAGE_NAMES.get(code, code)
        return {"code": code, "name": name, "confidence": "high"}
    except LangDetectException:
        return {"code": "unknown", "name": "Unknown", "confidence": "low"}

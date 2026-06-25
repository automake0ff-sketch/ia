"""
Skill: extract_keywords

Extrae palabras clave, temas principales, entidades nombradas (personas,
organizaciones, lugares) y sentimiento general de un texto, usando el
proveedor LLM configurado. Devuelve un único análisis estructurado que
otros skills (como generate_tags) pueden reutilizar sin volver a llamar
a la API.
"""
import json
import re

from ..config import get_settings
from .prompts import build_keywords_prompt

settings = get_settings()

_DEFAULT_ANALYSIS = {
    "keywords": [],
    "topics": [],
    "entities": {"people": [], "organizations": [], "places": []},
    "sentiment": "neutral",
    "tags": [],
}


class ExtractionError(Exception):
    """Error de negocio al extraer metadatos del contenido."""


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    return raw


def extract_keywords(text: str, language: str = "es", provider: str = "openai") -> dict:
    """
    Returns:
        {
            "keywords": [...], "topics": [...],
            "entities": {"people": [...], "organizations": [...], "places": [...]},
            "sentiment": "positive" | "neutral" | "negative", "tags": [...]
        }
    """
    prompt = build_keywords_prompt(text, language)

    try:
        if provider == "anthropic":
            from anthropic import Anthropic

            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=800,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = "".join(b.text for b in response.content if b.type == "text")
        else:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
    except Exception as exc:
        raise ExtractionError(f"Error al extraer keywords/temas/entidades: {exc}")

    try:
        data = json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        return dict(_DEFAULT_ANALYSIS)

    for key, fallback in _DEFAULT_ANALYSIS.items():
        data.setdefault(key, fallback)
    return data

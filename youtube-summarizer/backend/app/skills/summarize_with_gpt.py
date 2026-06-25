"""
Skill: summarize_with_gpt

Genera resúmenes usando la API de OpenAI (GPT-4o-mini por defecto), con
prompts optimizados por estrategia de resumen e idioma.
"""
from typing import Optional

from openai import OpenAI

from ..config import get_settings
from .prompts import build_summary_prompt

settings = get_settings()


class SummarizationError(Exception):
    """Error de negocio al generar un resumen."""


def _get_client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise SummarizationError("OPENAI_API_KEY no está configurada en el entorno (.env).")
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def summarize_with_gpt(
    transcript: str,
    summary_type: str = "executive",
    language: str = "es",
    title: str = "",
    model: Optional[str] = None,
) -> str:
    """Genera un resumen del transcript usando GPT. Devuelve el texto del resumen."""
    client = _get_client()
    prompt = build_summary_prompt(transcript, summary_type, language, title)

    try:
        response = client.chat.completions.create(
            model=model or settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente experto en resumir contenido de video con precisión y claridad.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        raise SummarizationError(f"Error al generar resumen con OpenAI: {exc}")

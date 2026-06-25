"""
Skill: summarize_with_claude

Genera resúmenes usando la API de Anthropic (Claude). Sirve como motor
alternativo para redundancia, comparación de calidad y como fallback
automático si OpenAI falla (ver SummarizerAgent).
"""
from typing import Optional

from anthropic import Anthropic

from ..config import get_settings
from .prompts import build_summary_prompt

settings = get_settings()


class SummarizationError(Exception):
    """Error de negocio al generar un resumen."""


def _get_client() -> Anthropic:
    if not settings.ANTHROPIC_API_KEY:
        raise SummarizationError("ANTHROPIC_API_KEY no está configurada en el entorno (.env).")
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def summarize_with_claude(
    transcript: str,
    summary_type: str = "executive",
    language: str = "es",
    title: str = "",
    model: Optional[str] = None,
) -> str:
    """Genera un resumen del transcript usando Claude. Devuelve el texto del resumen."""
    client = _get_client()
    prompt = build_summary_prompt(transcript, summary_type, language, title)

    try:
        response = client.messages.create(
            model=model or settings.ANTHROPIC_MODEL,
            max_tokens=1500,
            temperature=0.3,
            system="Eres un asistente experto en resumir contenido de video con precisión y claridad.",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()
    except Exception as exc:
        raise SummarizationError(f"Error al generar resumen con Claude: {exc}")

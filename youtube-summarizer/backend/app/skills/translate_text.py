"""
Skill: translate_text

Traduce un texto (típicamente un resumen ya generado) a cualquiera de los
idiomas soportados, usando el proveedor LLM indicado (openai | anthropic).
"""
from ..config import get_settings
from .prompts import LANGUAGE_NAMES, build_translation_prompt

settings = get_settings()


class TranslationError(Exception):
    """Error de negocio al traducir un texto."""


def translate_text(text: str, target_language: str, provider: str = "openai") -> str:
    if target_language not in LANGUAGE_NAMES:
        raise TranslationError(f"Idioma no soportado: {target_language}")

    prompt = build_translation_prompt(text, target_language)

    try:
        if provider == "anthropic":
            from anthropic import Anthropic

            if not settings.ANTHROPIC_API_KEY:
                raise TranslationError("ANTHROPIC_API_KEY no está configurada en el entorno (.env).")
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1500,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in response.content if b.type == "text").strip()

        from openai import OpenAI

        if not settings.OPENAI_API_KEY:
            raise TranslationError("OPENAI_API_KEY no está configurada en el entorno (.env).")
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500,
        )
        return (response.choices[0].message.content or "").strip()
    except TranslationError:
        raise
    except Exception as exc:
        raise TranslationError(f"Error al traducir texto: {exc}")

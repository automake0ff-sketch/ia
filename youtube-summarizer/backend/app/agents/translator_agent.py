"""
Agente Traductor

Responsabilidad única: traducir un resumen ya generado a uno o varios
idiomas adicionales solicitados por el usuario, reportando errores por
idioma sin abortar toda la operación.
"""
from typing import List

from ..skills.translate_text import TranslationError, translate_text
from .base import BaseAgent


class TranslatorAgent(BaseAgent):
    name = "TranslatorAgent"

    def run(self, text: str, target_languages: List[str], provider: str = "openai") -> dict:
        self.log_start(f"targets={target_languages}")
        translations = {}
        errors = {}

        for lang in target_languages:
            try:
                translations[lang] = translate_text(text, lang, provider)
            except TranslationError as exc:
                self.log_error(exc)
                errors[lang] = str(exc)

        self.log_end(f"ok={list(translations.keys())} errors={list(errors.keys())}")
        return {"translations": translations, "errors": errors}

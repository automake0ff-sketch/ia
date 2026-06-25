"""
Agente Resumidor

Responsabilidad única: generar el resumen del transcript con la estrategia
solicitada (ejecutivo, detallado, bullet points), usando el proveedor LLM
indicado. Si el proveedor principal falla, intenta automáticamente con el
proveedor alternativo (redundancia OpenAI <-> Claude).
"""
from ..skills.summarize_with_claude import SummarizationError as ClaudeError
from ..skills.summarize_with_claude import summarize_with_claude
from ..skills.summarize_with_gpt import SummarizationError as GPTError
from ..skills.summarize_with_gpt import summarize_with_gpt
from .base import BaseAgent


class SummarizerAgent(BaseAgent):
    name = "SummarizerAgent"

    PROVIDERS = {
        "openai": summarize_with_gpt,
        "anthropic": summarize_with_claude,
    }

    def run(
        self,
        transcript: str,
        summary_type: str = "executive",
        language: str = "es",
        title: str = "",
        provider: str = "openai",
    ) -> dict:
        self.log_start(f"type={summary_type} lang={language} provider={provider}")

        fallback_provider = "anthropic" if provider == "openai" else "openai"
        used_provider = provider

        try:
            summary_fn = self.PROVIDERS[provider]
            summary = summary_fn(transcript, summary_type, language, title)
        except (GPTError, ClaudeError) as exc:
            self.logger.warning(
                "Proveedor '%s' falló (%s). Intentando fallback con '%s'.", provider, exc, fallback_provider
            )
            try:
                summary_fn = self.PROVIDERS[fallback_provider]
                summary = summary_fn(transcript, summary_type, language, title)
                used_provider = fallback_provider
            except (GPTError, ClaudeError) as exc2:
                self.log_error(exc2)
                raise

        self.log_end(f"provider_used={used_provider} chars={len(summary)}")
        return {"summary": summary, "provider_used": used_provider}

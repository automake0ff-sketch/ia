"""
Agente Validador

Responsabilidad única: verificar la calidad del resumen generado
(longitud, formato y señales de coherencia) y exponer el resultado para
que el Orquestador decida si regenera el resumen.
"""
from ..skills.validate_summary import validate_summary
from .base import BaseAgent


class ValidatorAgent(BaseAgent):
    name = "ValidatorAgent"

    def run(self, summary: str, summary_type: str = "executive") -> dict:
        self.log_start(f"type={summary_type}")
        result = validate_summary(summary, summary_type)
        if not result["is_valid"]:
            self.logger.warning("Resumen inválido: %s", result["issues"])
        self.log_end(f"is_valid={result['is_valid']}")
        return result

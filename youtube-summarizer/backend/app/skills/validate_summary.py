"""
Skill: validate_summary

Valida la calidad de un resumen generado:
- Longitud apropiada según el tipo de resumen.
- Formato correcto (viñetas para bullet_points, encabezados para detailed).
- Señales básicas de coherencia (ausencia de meta-comentarios no deseados).

No depende de ninguna API externa: es una validación rápida y determinista
que el ValidatorAgent usa para decidir si vale la pena regenerar un resumen.
"""
import re

LENGTH_RULES = {
    "executive": (60, 280),
    "detailed": (250, 1200),
    "bullet_points": (40, 600),
}

_META_PHRASES = [
    "como modelo de lenguaje",
    "no tengo acceso",
    "como ia",
    "esta es una transcripción",
    "as an ai language model",
]


def validate_summary(summary: str, summary_type: str = "executive") -> dict:
    """
    Returns:
        {"is_valid": bool, "word_count": int, "issues": [str], "warnings": [str]}
    """
    if not summary or not summary.strip():
        return {"is_valid": False, "word_count": 0, "issues": ["El resumen está vacío."], "warnings": []}

    issues = []
    warnings = []

    word_count = len(summary.split())
    min_words, max_words = LENGTH_RULES.get(summary_type, (50, 1000))

    if word_count < min_words:
        issues.append(f"El resumen es demasiado corto ({word_count} palabras, mínimo esperado {min_words}).")
    elif word_count > max_words:
        warnings.append(
            f"El resumen es más largo de lo esperado ({word_count} palabras, máximo recomendado {max_words})."
        )

    if summary_type == "bullet_points":
        bullet_lines = [line for line in summary.splitlines() if line.strip().startswith(("-", "•", "*"))]
        if len(bullet_lines) < 3:
            issues.append("Se esperaba un formato de viñetas, pero se encontraron muy pocas.")

    if summary_type == "detailed":
        has_headers = bool(re.search(r"^#{1,3}\s", summary, re.MULTILINE))
        if not has_headers:
            warnings.append("Se recomienda incluir subtítulos (##) en los resúmenes detallados.")

    lowered = summary.lower()
    for phrase in _META_PHRASES:
        if phrase in lowered:
            issues.append(f"El resumen contiene una frase meta no deseada: '{phrase}'.")

    return {
        "is_valid": len(issues) == 0,
        "word_count": word_count,
        "issues": issues,
        "warnings": warnings,
    }

"""
Skill: generate_tags

Genera tags relevantes para el video. Reutiliza el análisis de
`extract_keywords` si ya está disponible (para evitar una llamada
duplicada y costosa a la API); si no, lo calcula a partir del texto.
"""
from typing import List, Optional

from .extract_keywords import extract_keywords


def generate_tags(
    text: Optional[str] = None,
    analysis: Optional[dict] = None,
    language: str = "es",
    provider: str = "openai",
    max_tags: int = 8,
) -> List[str]:
    """
    Genera una lista de tags normalizada y sin duplicados.

    Si se provee `analysis` (resultado previo de extract_keywords), los
    deriva de ahí sin llamar de nuevo a la API. Si no, requiere `text`.
    """
    if analysis is None:
        if text is None:
            raise ValueError("Debes proveer 'text' o 'analysis'.")
        analysis = extract_keywords(text, language=language, provider=provider)

    tags = list(analysis.get("tags", []))
    if not tags:
        tags = list(analysis.get("topics", []))[:max_tags]

    seen = set()
    unique_tags = []
    for tag in tags:
        normalized = tag.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_tags.append(tag.strip())

    return unique_tags[:max_tags]

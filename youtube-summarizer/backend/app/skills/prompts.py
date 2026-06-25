"""
Prompts optimizados para cada estrategia de resumen, traducción y extracción
de metadatos. Centralizados aquí para poder ajustarlos sin tocar la lógica
de los skills que los usan.
"""

SUMMARY_TYPE_INSTRUCTIONS = {
    "executive": (
        "Genera un RESUMEN EJECUTIVO conciso (entre 120 y 200 palabras) que capture "
        "el mensaje central, el propósito del video y las conclusiones más importantes. "
        "Usa prosa fluida, sin listas ni encabezados."
    ),
    "detailed": (
        "Genera un RESUMEN DETALLADO (entre 400 y 700 palabras) organizado en secciones "
        "con subtítulos breves en formato markdown (## Introducción, ## Desarrollo, ## Conclusión, etc.), "
        "cubriendo los puntos relevantes, ejemplos y argumentos mencionados en el video."
    ),
    "bullet_points": (
        "Genera un resumen en formato de VIÑETAS, entre 8 y 15 puntos, cada uno comenzando "
        "con '- ' y siendo una idea independiente, clara y concisa (máximo 25 palabras por viñeta). "
        "No agregues introducción ni conclusión en prosa."
    ),
}

LANGUAGE_NAMES = {
    "es": "español",
    "en": "English",
    "fr": "français",
    "de": "Deutsch",
    "it": "italiano",
    "pt": "português",
}


def build_summary_prompt(transcript: str, summary_type: str, language: str, title: str = "") -> str:
    instruction = SUMMARY_TYPE_INSTRUCTIONS.get(summary_type, SUMMARY_TYPE_INSTRUCTIONS["executive"])
    lang_name = LANGUAGE_NAMES.get(language, language)
    title_line = f'Título del video: "{title}"\n' if title else ""

    return f"""Eres un experto analista de contenido de video. Tu tarea es resumir la transcripción de un video de YouTube.

{title_line}INSTRUCCIONES:
- {instruction}
- Escribe el resumen completamente en {lang_name}.
- No inventes información que no esté en la transcripción.
- No menciones que esto es una transcripción ni hagas meta-comentarios sobre tu propio proceso.
- No incluyas marcas de tiempo.

TRANSCRIPCIÓN:
\"\"\"
{transcript}
\"\"\"

RESUMEN:"""


def build_translation_prompt(text: str, target_language: str) -> str:
    lang_name = LANGUAGE_NAMES.get(target_language, target_language)
    return f"""Traduce el siguiente texto al idioma {lang_name}. Conserva el formato original (viñetas, \
subtítulos markdown, saltos de línea). No agregues comentarios ni notas, responde solo con la traducción.

TEXTO:
\"\"\"
{text}
\"\"\"

TRADUCCIÓN:"""


def build_keywords_prompt(text: str, language: str) -> str:
    lang_name = LANGUAGE_NAMES.get(language, language)
    return f"""Analiza el siguiente texto y devuelve EXCLUSIVAMENTE un JSON válido (sin texto adicional, \
sin markdown, sin backticks) con esta estructura exacta:

{{
  "keywords": ["palabra clave 1", "palabra clave 2"],
  "topics": ["tema principal 1", "tema principal 2"],
  "entities": {{"people": [], "organizations": [], "places": []}},
  "sentiment": "positive",
  "tags": ["tag1", "tag2"]
}}

Reglas:
- "keywords": entre 5 y 10 palabras o frases clave del contenido.
- "topics": entre 2 y 5 temas principales tratados en el video.
- "entities": personas, organizaciones y lugares mencionados explícitamente (listas vacías si no aplica).
- "sentiment": uno de "positive", "neutral" o "negative", según el tono general del contenido.
- "tags": entre 4 y 8 etiquetas cortas (1-3 palabras), en {lang_name}, útiles para categorizar el video.

TEXTO:
\"\"\"
{text}
\"\"\"

JSON:"""

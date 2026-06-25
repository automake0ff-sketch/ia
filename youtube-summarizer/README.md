# Subtexto — YouTube Video Summarizer con IA

Software completo de resumen de videos de YouTube usando IA, con una
arquitectura **multi-agente** extensible, **skills** modulares reutilizables,
caché, historial, exportación y un frontend propio (sin frameworks pesados).

---

## ✨ Funcionalidades

- Resumen de cualquier video de YouTube en 3 estrategias: **ejecutivo**,
  **detallado** y **viñetas**.
- 6 idiomas de salida: **es, en, fr, de, it, pt** — y traducción a idiomas
  adicionales en la misma operación.
- Dos motores de IA intercambiables: **OpenAI (GPT-4o-mini)** y
  **Anthropic (Claude)**, con **fallback automático** si uno falla.
- Extracción de **palabras clave, temas, entidades** (personas, organizaciones,
  lugares) y **sentimiento** del contenido.
- **Validación automática de calidad** del resumen (longitud, formato,
  coherencia), con reintento si falla.
- **Caché** de resultados (Redis si está disponible, o SQLite/Postgres como
  respaldo) con TTL de 7 días configurable.
- **Historial** persistente por usuario (anónimo, vía ID local).
- **Exportación** a PDF, Markdown y texto plano.
- Frontend propio con **modo oscuro/claro**, historial en sidebar, copiar al
  portapapeles y diseño responsive.
- **Docker Compose** listo para producción (backend + Redis + PostgreSQL).

---

## 🏗️ Arquitectura

### Sistema multi-agente

Cada agente tiene una única responsabilidad y vive en `backend/app/agents/`:

| Agente | Responsabilidad |
|---|---|
| `OrchestratorAgent` | Coordina el flujo completo y decide reintentos |
| `TranscriberAgent` | Obtiene la transcripción + metadatos del video |
| `SummarizerAgent` | Genera el resumen (con fallback de proveedor) |
| `ValidatorAgent` | Verifica calidad del resumen |
| `ExtractorAgent` | Extrae keywords, temas, entidades, sentimiento, tags |
| `TranslatorAgent` | Traduce el resumen a idiomas adicionales |

```
video_url
   │
   ▼
TranscriberAgent ──► transcripción + metadata
   │
   ▼
SummarizerAgent ──► resumen (OpenAI → fallback Claude)
   │
   ▼
ValidatorAgent ──► ¿válido? ──no──► reintenta (SummarizerAgent)
   │ sí
   ▼
ExtractorAgent ──► keywords / temas / entidades / sentimiento / tags
   │
   ▼
TranslatorAgent (opcional) ──► traducciones adicionales
   │
   ▼
respuesta final + caché + historial
```

### Skills (capacidades modulares)

Los agentes no llaman directamente a APIs externas: delegan en **skills**
puros, ubicados en `backend/app/skills/`, cada uno con una sola función:

- `transcribe_youtube` — extracción de transcripción con fallback de idiomas.
- `summarize_with_gpt` / `summarize_with_claude` — resumen con cada proveedor.
- `translate_text` — traducción a cualquier idioma soportado.
- `extract_keywords` — keywords, temas, entidades y sentimiento (un solo JSON).
- `generate_tags` — tags, reutilizando el análisis anterior sin nueva llamada.
- `validate_summary` — validación determinista (sin coste de API).
- `detect_language` — detección de idioma local (sin coste de API).

Esta separación permite, por ejemplo, añadir un nuevo proveedor de
resumen (`summarize_with_gemini.py`) sin tocar ningún agente: solo se
registra en `SummarizerAgent.PROVIDERS`.

### Estructura de carpetas

```
youtube-summarizer/
├── backend/
│   ├── app/
│   │   ├── main.py            # entrypoint FastAPI
│   │   ├── config.py          # settings (.env)
│   │   ├── database.py        # SQLAlchemy
│   │   ├── models.py          # modelos ORM (historial, caché)
│   │   ├── schemas.py         # esquemas Pydantic
│   │   ├── cache.py           # caché Redis / SQLite
│   │   ├── agents/            # sistema multi-agente
│   │   ├── skills/            # capacidades modulares
│   │   ├── routers/           # endpoints (/summarize, /history, /export)
│   │   └── utils/             # exportadores (PDF/MD/TXT)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/ (api.js, ui.js, app.js)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Cómo correrlo

### Opción A — Docker (recomendado)

```bash
cp .env.example .env
# Edita .env y agrega al menos OPENAI_API_KEY o ANTHROPIC_API_KEY

docker compose up --build
```

Abre **http://localhost:8000** — el backend sirve también el frontend.

Esto levanta 3 contenedores: `backend` (FastAPI), `redis` (caché) y
`postgres` (historial). El backend espera a que ambos estén healthy antes
de arrancar.

### Opción B — Desarrollo local sin Docker

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example ../.env
# Edita ../.env: como mínimo OPENAI_API_KEY.
# Deja DATABASE_URL=sqlite:///./data/summarizer.db y comenta REDIS_URL
# si no tienes Redis corriendo localmente (la app usa SQLite como caché).

uvicorn app.main:app --reload --port 8000
```

Abre **http://localhost:8000**.

> En este modo, `main.py` busca la carpeta `frontend/` un nivel arriba de
> `backend/` automáticamente — no necesitas configurar nada más.

---

## 🔑 Variables de entorno

Ver `.env.example` para la lista completa. Las más relevantes:

| Variable | Descripción |
|---|---|
| `OPENAI_API_KEY` | Clave de OpenAI (requerida si usas el motor `openai`) |
| `ANTHROPIC_API_KEY` | Clave de Anthropic (requerida si usas el motor `anthropic`) |
| `DATABASE_URL` | `sqlite:///./data/summarizer.db` o `postgresql://...` |
| `REDIS_URL` | Si se omite, la app usa una tabla SQLite/Postgres como caché |
| `CACHE_TTL_DAYS` | Días que vive un resumen en caché (por defecto 7) |
| `ALLOWED_ORIGINS` | CORS; `*` por defecto |

---

## 📡 API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/summarize` | Genera (o recupera de caché) el resumen de un video |
| `GET` | `/api/history?user_id=...` | Lista el historial de un usuario |
| `GET` | `/api/history/{id}` | Detalle de un ítem del historial |
| `DELETE` | `/api/history/{id}` | Elimina un ítem del historial |
| `DELETE` | `/api/history?user_id=...` | Vacía el historial completo de un usuario |
| `GET` | `/api/export/{history_id}/{pdf\|markdown\|txt}` | Descarga el resumen en el formato pedido |
| `GET` | `/api/health` | Healthcheck |

La documentación interactiva (Swagger) está siempre disponible en
**`/docs`**.

### Ejemplo: `POST /api/summarize`

```json
{
  "video_url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
  "language": "es",
  "summary_type": "executive",
  "provider": "openai",
  "user_id": "anonymous",
  "use_cache": true,
  "extra_languages": ["en", "pt"]
}
```

---

## 🧩 Extender el sistema

- **Nuevo proveedor de resumen**: crea `skills/summarize_with_<x>.py` con la
  misma firma que `summarize_with_gpt`, regístralo en
  `SummarizerAgent.PROVIDERS` y añade el valor al enum `LLMProvider` en
  `schemas.py`.
- **Nuevo formato de exportación**: agrega una función en `utils/exporters.py`
  y regístrala en el diccionario `EXPORTERS` de `routers/export.py`.
- **Nuevo idioma**: añade el código a `SUPPORTED_LANGUAGES` en `config.py` y a
  `LANGUAGE_NAMES` en `skills/prompts.py`.
- **Nuevo agente**: hereda de `agents/base.py::BaseAgent`, implementa `run()`
  y enchúfalo en `OrchestratorAgent`.

---

## ⚠️ Notas

- La extracción de transcripciones depende de que YouTube tenga subtítulos
  (manuales o automáticos) disponibles para el video; si están deshabilitados,
  la API devuelve un error 422 explicando el motivo.
- Los metadatos del video (título, canal, miniatura) se obtienen del endpoint
  público `oEmbed` de YouTube — no requiere API key de YouTube Data API.
- Este proyecto no fue ejecutado en vivo durante su generación (sandbox sin
  acceso a red); antes de desplegar a producción, prueba el flujo completo
  con una clave de API válida.

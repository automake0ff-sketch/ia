"""
Esquemas Pydantic: validación de entrada y forma de las respuestas de la API.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class SummaryType(str, Enum):
    executive = "executive"
    detailed = "detailed"
    bullet_points = "bullet_points"


class LLMProvider(str, Enum):
    openai = "openai"
    anthropic = "anthropic"


class SummarizeRequest(BaseModel):
    video_url: str = Field(..., description="URL del video de YouTube")
    language: str = Field(default="es", description="Idioma del resumen (es, en, fr, de, it, pt)")
    summary_type: SummaryType = SummaryType.executive
    provider: LLMProvider = LLMProvider.openai
    user_id: Optional[str] = "anonymous"
    use_cache: bool = True
    extra_languages: List[str] = Field(default_factory=list, description="Idiomas adicionales a traducir")


class ValidationResult(BaseModel):
    is_valid: bool
    word_count: int
    issues: List[str] = []
    warnings: List[str] = []


class SummarizeResponse(BaseModel):
    history_id: Optional[int] = None
    video_id: str
    video_url: str
    title: Optional[str] = None
    channel: Optional[str] = None
    thumbnail_url: Optional[str] = None
    language: str
    summary_type: str
    summary: str
    keywords: List[str] = []
    tags: List[str] = []
    topics: List[str] = []
    sentiment: Optional[str] = None
    entities: Dict = {}
    translations: Dict[str, str] = {}
    validation: Optional[Dict] = None
    cached: bool = False
    processing_time_seconds: Optional[float] = None


class HistoryItem(BaseModel):
    id: int
    user_id: str
    video_url: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    channel: Optional[str] = None
    thumbnail_url: Optional[str] = None
    language: str
    summary_type: str
    summary: str
    keywords: Optional[str] = None
    tags: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

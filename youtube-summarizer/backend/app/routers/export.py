"""
Router: /api/export

Exporta un resumen del historial a PDF, Markdown o texto plano.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SummaryHistory
from ..utils.exporters import export_to_markdown, export_to_pdf, export_to_txt

router = APIRouter(prefix="/api/export", tags=["export"])

EXPORTERS = {
    "pdf": (export_to_pdf, "application/pdf", "pdf"),
    "markdown": (export_to_markdown, "text/markdown", "md"),
    "txt": (export_to_txt, "text/plain", "txt"),
}


@router.get("/{history_id}/{format}")
def export_summary(history_id: int, format: str, db: Session = Depends(get_db)):
    if format not in EXPORTERS:
        raise HTTPException(status_code=400, detail="Formato no soportado. Usa: pdf, markdown o txt.")

    item = db.query(SummaryHistory).filter(SummaryHistory.id == history_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado en el historial.")

    exporter_fn, media_type, extension = EXPORTERS[format]
    buffer = exporter_fn(item)
    safe_title = "".join(c for c in (item.title or "resumen") if c.isalnum() or c in " -_").strip() or "resumen"
    filename = f"{safe_title[:50]}.{extension}"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

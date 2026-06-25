"""
Utilidades de exportación: convierten un registro de historial (SummaryHistory)
en distintos formatos de archivo descargables.
"""
import io
from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def export_to_markdown(item) -> io.BytesIO:
    lines = [
        f"# {item.title or 'Resumen de video'}",
        "",
        f"- **Canal:** {item.channel or 'N/A'}",
        f"- **URL:** {item.video_url}",
        f"- **Idioma:** {item.language}",
        f"- **Tipo de resumen:** {item.summary_type}",
        f"- **Fecha:** {item.created_at}",
        "",
        "## Resumen",
        "",
        item.summary or "",
    ]
    content = "\n".join(lines)
    return io.BytesIO(content.encode("utf-8"))


def export_to_txt(item) -> io.BytesIO:
    lines = [
        (item.title or "Resumen de video").upper(),
        "=" * 40,
        f"Canal: {item.channel or 'N/A'}",
        f"URL: {item.video_url}",
        f"Idioma: {item.language}",
        f"Tipo de resumen: {item.summary_type}",
        f"Fecha: {item.created_at}",
        "",
        "RESUMEN:",
        "-" * 40,
        item.summary or "",
    ]
    content = "\n".join(lines)
    return io.BytesIO(content.encode("utf-8"))


def export_to_pdf(item) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=item.title or "Resumen de video",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], alignment=TA_LEFT, spaceAfter=12)
    meta_style = ParagraphStyle("Meta", parent=styles["Normal"], textColor="#555555", spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=styles["BodyText"], leading=16, spaceAfter=8)

    story = [Paragraph(escape(item.title or "Resumen de video"), title_style)]

    meta_fields = [
        ("Canal", item.channel or "N/A"),
        ("URL", item.video_url),
        ("Idioma", item.language),
        ("Tipo de resumen", item.summary_type),
        ("Fecha", str(item.created_at)),
    ]
    for label, value in meta_fields:
        story.append(Paragraph(f"<b>{escape(label)}:</b> {escape(str(value))}", meta_style))

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Resumen", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))

    for paragraph in (item.summary or "").split("\n"):
        if paragraph.strip():
            story.append(Paragraph(escape(paragraph.strip()), body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

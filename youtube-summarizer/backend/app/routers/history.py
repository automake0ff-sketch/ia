"""
Router: /api/history

Gestiona el historial de resúmenes generados por los usuarios.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SummaryHistory
from ..schemas import HistoryItem

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=List[HistoryItem])
def get_history(
    user_id: str = Query(default="anonymous"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items = (
        db.query(SummaryHistory)
        .filter(SummaryHistory.user_id == user_id)
        .order_by(SummaryHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items


@router.get("/{history_id}", response_model=HistoryItem)
def get_history_item(history_id: int, db: Session = Depends(get_db)):
    item = db.query(SummaryHistory).filter(SummaryHistory.id == history_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado en el historial.")
    return item


@router.delete("/{history_id}")
def delete_history_item(history_id: int, db: Session = Depends(get_db)):
    item = db.query(SummaryHistory).filter(SummaryHistory.id == history_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado en el historial.")
    db.delete(item)
    db.commit()
    return {"detail": "Eliminado correctamente.", "id": history_id}


@router.delete("")
def clear_history(user_id: str = Query(default="anonymous"), db: Session = Depends(get_db)):
    deleted = db.query(SummaryHistory).filter(SummaryHistory.user_id == user_id).delete()
    db.commit()
    return {"detail": "Historial eliminado.", "count": deleted}

from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.db import get_session
from app.models.Transcriptions import Transcription

router = APIRouter()

@router.get("/api/stt/history")
async def get_all_transcriptions(session: Session = Depends(get_session)):
    # Fetch all records, sorted by newest first
    statement = select(Transcription).order_by(Transcription.uploaded_at.desc())
    results = session.exec(statement).all()
    return results
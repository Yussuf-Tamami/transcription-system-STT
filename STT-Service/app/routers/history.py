from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.db import get_session
from app.models.Uploads import Upload
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/api/stt/history")
async def get_all_transcriptions(session: Session = Depends(get_session)):
    # Fetch all records, sorted by newest first
    statement = select(Upload).order_by(Upload.created_at.desc())
    results = session.exec(statement).all()
    return results


@router.get("/api/stt/download/{upload_id}")
async def download_audio(upload_id: int, session: Session = Depends(get_session)):
    db_entry = session.get(Upload, upload_id)
    
    if not db_entry or not db_entry.file_path or not os.path.exists(db_entry.file_path):
        return {"error": "Audio file not found or has been deleted."}
        
    filename = os.path.basename(db_entry.file_path)
    return FileResponse(
        path=db_entry.file_path, 
        filename=filename,
        media_type="audio/wav"
    )
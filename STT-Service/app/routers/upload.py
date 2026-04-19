import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlmodel import Session

from ..db import get_session, engine
from ..models.Transcriptions import Transcription
from ..transcribe import transcribe_with_whisper
from ..config import settings

router = APIRouter()

def background_processing(transcription_id: int, file_path: str):
    """Update database record after transcription."""
    with Session(engine) as session:
        try:
            db_entry = session.get(Transcription, transcription_id)
            if db_entry:
                db_entry.transcription_text = transcribe_with_whisper(file_path)
                db_entry.status = "done"
                session.add(db_entry)
                session.commit()
        except Exception as e:
            # If it fails, at least mark it as "error" in the DB so you know!
            db_entry.status = "error"
            db_entry.transcription_text = f"Crashed: {str(e)}"
            session.commit()


@router.post("/api/stt/upload")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    unique_name = f"{uuid.uuid4()}{Path(file.filename).suffix}"
    file_path = settings.UPLOAD_DIR / unique_name

    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Register record
    db_entry = Transcription(
        filename=file.filename,
        filepath=str(file_path),
        status="processing"
    )
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)

    # Start background task for transcription (background thread so it doesn't block the response)
    background_tasks.add_task(background_processing, db_entry.id, str(file_path))
    
    return {"id": db_entry.id, "status": "processing"}

@router.get("/api/stt/status/{transcription_id}")
async def get_transcription_status(transcription_id: int, session: Session = Depends(get_session)):
    db_entry = session.get(Transcription, transcription_id)
    if not db_entry:
        return {"error": "Not found"}
    return {
        "status": db_entry.status,
        "text": db_entry.transcription_text if db_entry.status == "done" else None
    }
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlmodel import Session

from ..db import get_session, engine
from ..models.Uploads import Upload
from ..models.TranscriptionChunk import TranscriptionChunk
from ..transcribe import process_upload_hybrid
from ..config import settings

router = APIRouter()

def background_processing(upload_id: int, file_path: str):
    """Handles the heavy AI processing and multi-table saving logic."""
    with Session(engine) as session:
        try:
            db_entry = session.get(Upload, upload_id)
            if db_entry:
                speaker_count, chunks, full_text = process_upload_hybrid(file_path)
                
                db_entry.speaker_count = speaker_count
                db_entry.status = "completed"

                if speaker_count <= 1:
                    db_entry.full_text = full_text
                else:
                    # Write the glued chunks into the child table
                    for chunk in chunks:
                        db_chunk = TranscriptionChunk(
                            upload_id=db_entry.id,
                            speaker_label=chunk["speaker"],
                            start_time=chunk["start"],
                            end_time=chunk["end"],
                            text=chunk["text"]
                        )
                        session.add(db_chunk)
                        
                session.add(db_entry)
                session.commit()
        except Exception as e:
            # Roll back the failed transaction to prevent database locking
            session.rollback() 
            
            if db_entry:
                db_entry.status = "failed"
                db_entry.full_text = f"Crashed: {str(e)}"
                session.add(db_entry)
                session.commit()

@router.post("/api/stt/upload")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    # 1. Force the .wav extension because frontend normalizes everything to WAV
    unique_name = f"upload_{uuid.uuid4().hex[:8]}.wav"
    
    file_path = settings.UPLOAD_DIR / unique_name
    
    # Create directory if it doesn't exist inside the Docker container
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 2. Save the file physically to the disk
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    
    db_entry = Upload(
        source_type="file",
        status="processing",
        file_path=str(file_path) 
    )
    
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)

    # 4. Send the saved file path to the background worker
    background_tasks.add_task(background_processing, db_entry.id, str(file_path))
    
    return {"id": db_entry.id, "status": "processing"}

@router.get("/api/stt/status/{upload_id}")
async def get_transcription_status(upload_id: int, session: Session = Depends(get_session)):
    db_entry = session.get(Upload, upload_id)
    if not db_entry:
        return {"error": "Not found"}
    return {
        "status": db_entry.status,
        "speaker_count": db_entry.speaker_count,
        "full_text": db_entry.full_text,
        "chunks": db_entry.chunks # SQLModel automatically fetches the related rows!
    }
# routers/tts.py
import os
import uuid
import soundfile as sf
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from ..db import get_session
from ..models.TTSHistory import TTSHistory

router = APIRouter(tags=["TTS"])

@router.post("/api/tts/synthesize")
async def synthesize_audio(
    request: Request, 
    text: str, 
    voice: str = "af_nicole",
    session: Session = Depends(get_session)
):
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text is empty")

        kokoro = request.app.state.kokoro
        output_dir = request.app.state.output_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        filepath = output_dir / filename

        # --- AI Generation Phase ---
        samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0)
        sf.write(str(filepath), samples, sample_rate)

        # --- DATABASE INSERTION PHASE ---
        db_entry = TTSHistory(
            text_prompt=text,
            voice_model=voice,
            file_path=str(filepath)
        )
        session.add(db_entry)
        session.commit()
        session.refresh(db_entry)
        
        return {
            "status": "success",
            "id": db_entry.id,
            "filename": filename,
            "url": f"/api/tts/download/{db_entry.id}"
        }
    except Exception as e:
        session.rollback() # Prevent database locks on failure
        print(f"TTS Synthesis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/tts/history")
async def get_tts_history(session: Session = Depends(get_session)):
    """Fetches all TTS generation records, sorted by newest first."""
    statement = select(TTSHistory).order_by(TTSHistory.created_at.desc())
    results = session.exec(statement).all()
    return results

@router.get("/api/tts/download/{tts_id}")
async def download_tts(tts_id: int, session: Session = Depends(get_session)):
    """Serves the generated audio file to the UI for playback and downloading."""
    db_entry = session.get(TTSHistory, tts_id)
    
    if not db_entry or not os.path.exists(db_entry.file_path):
        raise HTTPException(status_code=404, detail="Audio file not found or has been deleted.")
    
    return FileResponse(
        path=db_entry.file_path, 
        filename=os.path.basename(db_entry.file_path),
        media_type="audio/wav"
    )
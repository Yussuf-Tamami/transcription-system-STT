from fastapi import APIRouter, HTTPException, Request, Depends
import uuid
import soundfile as sf
from sqlmodel import Session

# Import your DB session and the TTS model you created
from ..db import get_session 
from ..models.TTSHistory import TTSHistory 

router = APIRouter()

@router.post("/api/tts/synthesize")
async def synthesize_audio(
    request: Request, 
    text: str, 
    voice: str = "af_nicole",
    session: Session = Depends(get_session) # <-- 1. INJECT THE DB SESSION
):
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text is empty")

        kokoro = request.app.state.kokoro
        output_dir = request.app.state.output_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"speech_{uuid.uuid4().hex[:8]}.wav"
        filepath = output_dir / filename

        # --- AI Generation Phase ---
        samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0)
        sf.write(str(filepath), samples, sample_rate)

        # --- DATABASE INSERTION PHASE (This was missing!) ---
        db_entry = TTSHistory(
            text_prompt=text,
            voice_model=voice,
            file_path=str(filepath)
        )
        session.add(db_entry)
        session.commit()
        session.refresh(db_entry)
        # ----------------------------------------------------
        
        return {
            "status": "success",
            "id": db_entry.id,                 # Return the DB ID
            "filename": filename,
            "url": f"/api/tts/download/{db_entry.id}" # Point to your download endpoint!
        }
    except Exception as e:
        session.rollback() # Always rollback on error to prevent stuck transactions!
        print(f"TTS Synthesis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, HTTPException, Request
import uuid
import soundfile as sf
from sqlmodel import Session
from app.models.TTSHistory import TTSHistory

router = APIRouter()


@router.post("/api/tts/synthesize")
async def synthesize_audio(request: Request, text: str, voice: str = "am_fenrir"):
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text is empty")

        # GET DATA FROM APP STATE (No more circular imports!)
        kokoro = request.app.state.kokoro
        output_dir = request.app.state.output_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"speech_{uuid.uuid4().hex[:8]}.wav"
        filepath = output_dir / filename

        samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0)
        sf.write(str(filepath), samples, sample_rate)

        with Session(request.app.state.engine) as session:
            new_record = TTSHistory(
                text_input=text,
                voice_used=voice,
                audio_path=f"outputs/{filename}"
            )
            session.add(new_record)
            session.commit()
        
        return {
            "status": "success",
            "filename": filename,
            "url": f"/outputs/{filename}"
        }
    except Exception as e:
        print(f"TTS Synthesis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
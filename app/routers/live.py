import os
import json
import uuid
import tempfile
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session
from pydub import AudioSegment

from ..db import engine
from ..models import Transcription
from ..transcribe import _vosk_model, KaldiRecognizer
from ..config import settings

router = APIRouter(tags=["Live"])

@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # We'll use a temp file to store the incoming WebM data
    # This is much more stable than a bytearray in RAM for FFmpeg
    temp_webm = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    print(f"--- 🔴 Live Connection Started: {temp_webm.name} ---")

    try:
        while True:
            message = await websocket.receive()
            
            if "text" in message and message["text"] == "END_OF_STREAM":
                break
            
            if "bytes" in message:
                # Write chunk to the physical file immediately
                temp_webm.write(message["bytes"])
                temp_webm.flush() 

                # --- OPTIONAL: Live Feedback (Partial) ---
                # To avoid the 'EBML' error, we only try to decode if 
                # the file has grown enough to have a valid header + data
                if os.path.getsize(temp_webm.name) > 90000: # ~90KB
                    try:
                        # Use run_in_threadpool to prevent the 'hang'
                        partial_text = await run_in_threadpool(get_partial_transcription, temp_webm.name)
                        if partial_text:
                            await websocket.send_json({"status": "partial", "text": partial_text})
                    except:
                        pass # Ignore partial errors to keep the stream alive

        # --- STOPPED: Finalize ---
        temp_webm.close()
        print("--- 💾 Finalizing and Saving to MySQL ---")
        
        final_text = await run_in_threadpool(get_final_transcription, temp_webm.name)

        # Save to MySQL
        if final_text:
            # Move the temporary wav to your permanent uploads folder
            filename = f"live_{uuid.uuid4().hex}.wav"
            final_path = settings.UPLOAD_DIR / filename
            
            # Re-convert one last time for the permanent file
            audio = AudioSegment.from_file(temp_webm.name)
            audio.export(final_path, format="wav")

            with Session(engine) as session:
                db_entry = Transcription(
                    filename=f"Live Session {uuid.uuid4().hex[:4]}",
                    filepath=str(final_path),
                    status="done",
                    transcription_text=final_text
                )
                session.add(db_entry)
                session.commit()
                session.refresh(db_entry)

            await websocket.send_json({"status": "done", "text": final_text})

    except WebSocketDisconnect:
        print("--- ⚪ Connection Closed ---")
    finally:
        if os.path.exists(temp_webm.name):
            os.remove(temp_webm.name)

# --- Helper Functions for Threading ---

def get_partial_transcription(file_path):
    """Safely attempts to decode the current file for a 'best guess'."""
    try:
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        rec = KaldiRecognizer(_vosk_model, 16000)
        rec.AcceptWaveform(audio.raw_data)
        return json.loads(rec.PartialResult()).get("partial", "")
    except:
        return ""

def get_final_transcription(file_path):
    """Decodes the full file for the final DB save."""
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    rec = KaldiRecognizer(_vosk_model, 16000)
    rec.AcceptWaveform(audio.raw_data)
    return json.loads(rec.FinalResult()).get("text", "")
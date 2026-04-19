import os
import io
import json
import uuid

import static_ffmpeg  # Ensure FFmpeg is available for pydub
static_ffmpeg.add_paths()

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session
from pydub import AudioSegment

from ..db import engine
from ..models.Transcriptions import Transcription
from ..transcribe import _vosk_model, KaldiRecognizer
from ..config import settings

router = APIRouter(tags=["Live"])

@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # byte array in ram to hold incoming audio data (.webms or .wav) from the browser
    audio_buffer = bytearray()
    print("--- 🟢 Live Connection Started (RAM Buffer) ---")

    try:
        while True:
            message = await websocket.receive()
            
            if "text" in message and message["text"] == "END_OF_STREAM":
                break
            
            if "bytes" in message:
                # keeps adding incoming audio data to the RAM buffer
                audio_buffer.extend(message["bytes"])

               
                if len(audio_buffer) > 80000: 
                    try:
                        #sends the current buffer content to Vosk for partial transcription results
                        current_bytes = bytes(audio_buffer)
                        partial_text = await run_in_threadpool(get_partial_transcription, current_bytes)
                        
                        if partial_text:
                            await websocket.send_json({"status": "partial", "text": partial_text})
                    except Exception as e:
                        
                        pass

        # --- STOPPED: Finalize ---
        print("--- 💾 Stream Ended. Finalizing in RAM ---")
        
        final_bytes = bytes(audio_buffer)
        final_text = await run_in_threadpool(get_final_transcription, final_bytes)

        # storing the final audio and transcription in the database, but only if we got some text back (and we have audio data)
        if final_text and len(final_bytes) > 0:
            filename = f"live_{uuid.uuid4().hex}.wav"
            final_path = settings.UPLOAD_DIR / filename
            
        
            audio_stream = io.BytesIO(final_bytes)
            audio = AudioSegment.from_file(audio_stream)
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(final_path, format="wav") 

            # Create DB entry for this live transcription
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

            # Send final transcription back to client
            await websocket.send_json({"status": "done", "text": final_text})

    except WebSocketDisconnect:
        print("--- ⚪ Connection Closed by Client ---")
    finally:
        # free up RAM buffer
        del audio_buffer

# --- Helper Functions (RAM Processing) ---

def get_partial_transcription(audio_bytes: bytes):
    """ gets partial transcription results from Vosk using audio data directly from RAM (without saving to disk) """
    try:
        audio_stream = io.BytesIO(audio_bytes)
        audio = AudioSegment.from_file(audio_stream)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        rec = KaldiRecognizer(_vosk_model, 16000)
        rec.AcceptWaveform(audio.raw_data)
        return json.loads(rec.PartialResult()).get("partial", "")
    except:
        return ""

def get_final_transcription(audio_bytes: bytes):
    """ gets final transcription results from Vosk using audio data directly from RAM (without saving to disk) """
    try:
        audio_stream = io.BytesIO(audio_bytes)
        audio = AudioSegment.from_file(audio_stream)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        rec = KaldiRecognizer(_vosk_model, 16000)
        rec.AcceptWaveform(audio.raw_data)
        return json.loads(rec.FinalResult()).get("text", "")
    except:
        return ""
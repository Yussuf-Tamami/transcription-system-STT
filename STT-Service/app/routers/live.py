import io
import json
import uuid
import wave

import static_ffmpeg  
static_ffmpeg.add_paths()

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session
from pydub import AudioSegment

from ..db import get_session
from ..models.Uploads import Upload
from ..models.TranscriptionChunk import TranscriptionChunk
from ..transcribe import _vosk_model, spk_model, KaldiRecognizer
from ..clustering import cluster_fingerprints
from ..config import settings

router = APIRouter(tags=["Live"])

@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket, session: Session = Depends(get_session)):
    await websocket.accept()
    print("--- 🟢 Streaming Connection Started ---")

    # Attach the Speaker Model to the Live Recognizer
    rec = KaldiRecognizer(_vosk_model, 16000)
    rec.SetSpkModel(spk_model) 

    # Create a database record for this live session
    live_upload = Upload(source_type="live_stream", status="processing")
    session.add(live_upload)
    session.commit()
    session.refresh(live_upload)

    extracted_data = []
    fingerprints = []
    full_live_text = ""
    
    # Create an empty bytearray to catch the audio stream for saving
    live_audio_buffer = bytearray()

    try:
        while True:
            message = await websocket.receive()

            # --- CRITICAL FIX 1: The check I forgot in the last file! ---
            # If we don't catch this, Starlette loops and crashes with the "Cannot call receive" error.
            if message.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect(message.get("code", 1000))

            # --- CRITICAL FIX 2: Safely check for the end signal ---
            if message.get("text") == "END_OF_STREAM":
                break

            # Process audio chunks
            if "bytes" in message:
                audio_bytes = message["bytes"]
                live_audio_buffer.extend(audio_bytes) 

                if rec.AcceptWaveform(audio_bytes):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    spk = result.get("spk") 
                    
                    if text:
                        full_live_text += text + " "
                        start_time = result.get("result", [{}])[0].get("start", 0.0)
                        end_time = result.get("result", [{}])[-1].get("end", 0.0)

                        if spk:
                            extracted_data.append({"start": start_time, "end": end_time, "text": text})
                            fingerprints.append(spk)

                        await websocket.send_json({"status": "segment", "text": text})
                else:
                    partial = json.loads(rec.PartialResult()).get("partial", "")
                    if partial:
                        await websocket.send_json({"status": "partial", "text": partial})

        # --- STREAM ENDED (Cleanly triggered by END_OF_STREAM) ---
        await websocket.send_json({"status": "done", "text": "Processing speakers..."})
        
        # 1. Clustering
        speaker_count, chunks, final_text = cluster_fingerprints(extracted_data, fingerprints, threshold=0.85)
        
        # 2. Save WAV file
        unique_name = f"live_{live_upload.id}_{uuid.uuid4().hex[:8]}.wav"
        save_path = settings.UPLOAD_DIR / unique_name
        save_path.parent.mkdir(parents=True, exist_ok=True) 
        
        if len(live_audio_buffer) > 0:
            with wave.open(str(save_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(bytes(live_audio_buffer))
            live_upload.file_path = str(save_path) 
        
        # 3. Update DB
        live_upload.status = "completed"
        live_upload.speaker_count = speaker_count
        
        if speaker_count <= 1:
            live_upload.full_text = final_text or full_live_text.strip()
        else:
            for chunk in chunks:
                db_chunk = TranscriptionChunk(
                    upload_id=live_upload.id,
                    speaker_label=chunk["speaker"],
                    start_time=chunk["start"],
                    end_time=chunk["end"],
                    text=chunk["text"]
                )
                session.add(db_chunk)

        session.add(live_upload)
        session.commit()

        # 4. Send Final Chunks back to UI
        await websocket.send_json({
            "status": "completed",
            "speaker_count": speaker_count,
            "text": final_text or full_live_text.strip(),
            "chunks": chunks
        })

        await websocket.close()
        print("--- ⚪ Connection Closed Gracefully ---")

    except WebSocketDisconnect:
        live_upload.status = "failed"
        live_upload.full_text = "Stream disconnected unexpectedly."
        session.add(live_upload)
        session.commit()
        print("--- ⚪ Connection Closed (Disconnected by client) ---")
        
    except Exception as e:
        session.rollback()
        live_upload.status = "failed"
        live_upload.full_text = f"Internal Server Error: {str(e)}"
        session.add(live_upload)
        session.commit()
        print(f"--- ❌ Stream Crashed: {str(e)} ---")
        try:
            await websocket.close()
        except:
            pass

# --- Helper Functions (RAM Processing) ---

def get_partial_transcription(audio_bytes: bytes):
    """ gets partial transcription results from Vosk using audio data directly from RAM """
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
    """ gets final transcription results from Vosk using audio data directly from RAM """
    try:
        audio_stream = io.BytesIO(audio_bytes)
        audio = AudioSegment.from_file(audio_stream)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        rec = KaldiRecognizer(_vosk_model, 16000)
        rec.AcceptWaveform(audio.raw_data)
        return json.loads(rec.FinalResult()).get("text", "")
    except:
        return ""
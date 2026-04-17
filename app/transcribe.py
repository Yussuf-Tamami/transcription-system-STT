import os
import json
import wave
import tempfile
import static_ffmpeg
from pathlib import Path
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
from faster_whisper import WhisperModel 

# Initialize FFmpeg paths
static_ffmpeg.add_paths()

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = str(BASE_DIR / "model")

# --- ENGINE INITIALIZATION ---

# 1. Vosk (Fast - for Live Streaming)
_vosk_model = Model(MODEL_PATH)

# 2. Faster-Whisper (Accurate - for Uploaded Files)
# We use 'tiny' for speed, but you can upgrade to 'base' or 'small' for better results.
# 'int8' makes it run significantly smoother on CPU.
_whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8", cpu_threads=2)

def transcribe_with_whisper(file_path: str) -> str:
    """
    High-accuracy transcription using Faster-Whisper.
    Ideal for uploaded files where the user can wait a few seconds for quality.
    """
    try:
        # Whisper can handle many formats, but normalizing ensures stability
        segments, info = _whisper_model.transcribe(file_path, beam_size=5)
        
        # Combine segments into a single string
        final_text = " ".join([segment.text for segment in segments])
        return final_text.strip()
    
    except Exception as e:
        return f"Whisper Engine Error: {str(e)}"

def transcribe_with_vosk(file_path: str) -> str:
    """
    Fast transcription using Vosk.
    Used for live streams or quick previews.
    """
    temp_wav = None
    try:
        # Normalize audio for Vosk (16kHz, Mono, PCM 16-bit)
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            temp_wav = tmp.name
            audio.export(temp_wav, format="wav")

        wf = wave.open(temp_wav, "rb")
        rec = KaldiRecognizer(_vosk_model, wf.getframerate())
        
        final_result = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0: break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                final_result += res.get("text", "") + " "

        res = json.loads(rec.FinalResult())
        final_result += res.get("text", "")
        wf.close()
        
        return final_result.strip()

    except Exception as e:
        return f"Vosk Engine Error: {str(e)}"
    finally:
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)


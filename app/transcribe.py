import static_ffmpeg
static_ffmpeg.add_paths() 

import os
import json
import wave
import tempfile  # <--- THIS WAS MISSING
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
from pathlib import Path
from .config import settings

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = str(BASE_DIR / "model")

# Only initialize if it doesn't exist yet
_vosk_model = Model(MODEL_PATH)

def transcribe_audio(file_path: str) -> str:
    """Converts any audio format to 16kHz Mono WAV and transcribes with Vosk."""
    temp_wav = None
    try:
        # 1. CONVERT TO COMPATIBLE WAV
        # This handles .m4a, .mp3, .webm, etc.
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        # Save to a temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            temp_wav = tmp.name
            audio.export(temp_wav, format="wav")

        # 2. RUN VOSK ON THE WAV FILE
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
        return f"Transcription Error: {str(e)}"
    finally:
        # Cleanup the temporary WAV
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)


def transcribe_with_pocketsphinx(file_path: str) -> str:
    # Your existing legacy logic
    decoder = Decoder(verbose=False)
    with open(file_path, 'rb') as stream:
        decoder.start_utt()
        while True:
            chunk = stream.read(4096)
            if not chunk: break
            decoder.process_raw(chunk, False, False)
        decoder.end_utt()
    return decoder.hyp().hypstr if decoder.hyp() else ""

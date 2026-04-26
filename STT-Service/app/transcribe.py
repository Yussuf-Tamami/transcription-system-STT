# transcribe.py
import os
import json
import torch
import torchaudio
import numpy as np
from pathlib import Path
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer, SpkModel
from faster_whisper import WhisperModel
from speechbrain.inference.speaker import EncoderClassifier
import soundfile as sf
from .clustering import cluster_fingerprints

# --- PATH CONFIGURATION ---
CONTAINER_MODELS_DIR = Path("/app/models")
VOSK_MODEL_PATH = str(CONTAINER_MODELS_DIR / "vosk-model-small-en")
WHISPER_MODEL_PATH = str(CONTAINER_MODELS_DIR / "faster-whisper-tiny")
SPEECHBRAIN_MODEL_PATH = str(CONTAINER_MODELS_DIR / "speechbrain")
VOSK_SPK_MODEL_PATH = str(CONTAINER_MODELS_DIR / "vosk-model-spk-0.4")

# --- MODEL INITIALIZATION ---
_vosk_model = Model(VOSK_MODEL_PATH)
spk_model = SpkModel(VOSK_SPK_MODEL_PATH)

_whisper_model = WhisperModel(WHISPER_MODEL_PATH, device="cpu", compute_type="int8", cpu_threads=2)

_spk_classifier = EncoderClassifier.from_hparams(
    source=SPEECHBRAIN_MODEL_PATH,
    savedir=SPEECHBRAIN_MODEL_PATH, 
    run_opts={"device":"cpu"}
)


def extract_fingerprint_from_tensor(signal_tensor: torch.Tensor, sample_rate: int, start_time: float, end_time: float):
    start_frame = int(start_time * sample_rate)
    end_frame = int(end_time * sample_rate)
    
    # Slice the audio chunk from RAM
    chunk = signal_tensor[:, start_frame:end_frame]
    
    # 0.1 seconds is too short for a reliable fingerprint. 
    # Let's keep it at 1600 (0.1s) but ideally 4800 (0.3s) is better.
    if chunk.shape[1] < 1600:
        return None
        
    try:
        # Extract the raw embedding
        embeddings = _spk_classifier.encode_batch(chunk)
        raw_vector = embeddings.squeeze().numpy()
        
        # --- THE CRITICAL FIX: L2 NORMALIZATION ---
        # This makes the cosine distance in your clustering algorithm work correctly.
        norm = np.linalg.norm(raw_vector)
        if norm == 0:
            return raw_vector
        return raw_vector / norm
        
    except Exception as e:
        print(f"Fingerprint extraction error: {e}")
        return None


def process_upload_hybrid(file_path: str):
    # ... (Your existing loading code using soundfile is good) ...
    try:
        data, sample_rate = sf.read(file_path, dtype='float32')
        if data.ndim > 1: data = data.mean(axis=1)
    except Exception as e:
        return 0, [], f"File Load Error: {e}"

    # Transcribe
    segments, _ = _whisper_model.transcribe(data, beam_size=5)
    
    signal_tensor = torch.from_numpy(data).unsqueeze(0)
    extracted_data = []
    fingerprints = []
    
    # Create a safe, generic unit vector as an absolute fallback to prevent divide-by-zero
    last_good_fp = np.ones(192) / np.linalg.norm(np.ones(192))

    for segment in segments:
        text = segment.text.strip()
        if not text: continue
        
        fp = extract_fingerprint_from_tensor(signal_tensor, sample_rate, segment.start, segment.end)
        
        extracted_data.append({
            "start": segment.start, 
            "end": segment.end, 
            "text": text,
            "speaker": "UNKNOWN"
        })
        
        if fp is not None:
            fingerprints.append(fp)
            last_good_fp = fp  # Save this as the new known voice
        else:
            # INHERIT the last known voice instead of throwing a fatal zero-vector!
            fingerprints.append(last_good_fp)

    if not fingerprints:
        return 0, [], "No audible speech detected."

    return cluster_fingerprints(extracted_data, fingerprints)


# --- VOSK TRANSCRIPTION (For Live Streams) ---

def transcribe_with_vosk(file_path: str) -> str:
    try:
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        rec = KaldiRecognizer(_vosk_model, 16000)
        rec.AcceptWaveform(audio.raw_data)
        result = json.loads(rec.FinalResult())
        return result.get("text", "").strip()
    except Exception as e:
        return f"Vosk Error: {str(e)}"
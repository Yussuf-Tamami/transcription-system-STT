from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kokoro_onnx import Kokoro
from app.routers import synthesize

app = FastAPI(title="TTS Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Volume Paths
OUTPUT_DIR = Path("/app/storage/outputs")
MODELS_DIR = Path("/app/models/kokoro")

# 1. Attach the directory to the app state so routers can see it without importing main
app.state.output_dir = OUTPUT_DIR

# 2. Initialize Engine
kokoro_engine = Kokoro(
    str(MODELS_DIR / "kokoro-v1.0.int8.onnx"), 
    str(MODELS_DIR / "voices.bin")
)
app.state.kokoro = kokoro_engine

app.include_router(synthesize.router)

@app.get("/")
async def root():
    return {"status": "TTS Service Online"}
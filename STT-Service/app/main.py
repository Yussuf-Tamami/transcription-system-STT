from fastapi import FastAPI
from app.db import init_db
from app.routers import upload, history, live
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.models import Transcriptions


app = FastAPI(title="STT Service")


# Allow Gateway/Frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW VOLUME PATHS ---
# These MUST match the paths inside the Docker container
STORAGE_DIR = Path("/app/storage")
UPLOADS_DIR = STORAGE_DIR / "uploads"

# Create tables on startup
@app.on_event("startup")
def on_startup():
    import time
    for i in range(10):
        try:
            init_db()
            print("Database initialized successfully.")
            break
        except Exception as e:
            print(f"Database not ready yet (attempt {i+1}/10)...")
            time.sleep(3)

# Include our specific logic routers
app.include_router(upload.router)
app.include_router(history.router)
app.include_router(live.router)

@app.get("/")
def health_check():
    return {"status": "online"}
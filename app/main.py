from fastapi import FastAPI
from app.db import init_db
from app.routers import upload, ui, history, live
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="Transcription System")

app.mount("/static", StaticFiles(directory="static"), name="static")


# Create tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Include our specific logic routers
app.include_router(upload.router)
app.include_router(ui.router)
app.include_router(history.router)
app.include_router(live.router)

@app.get("/")
def health_check():
    return {"status": "online"}
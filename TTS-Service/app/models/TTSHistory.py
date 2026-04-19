from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class TTSHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text_input: str
    voice_used: str
    audio_path: str  # e.g., "outputs/speech_123.wav"
    created_at: datetime = Field(default_factory=datetime.utcnow)
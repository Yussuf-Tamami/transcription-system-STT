# models/TTSHistory.py
from sqlmodel import SQLModel, Field
from datetime import datetime

class TTSHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text_prompt: str = Field(max_length=5000) # The text the user typed
    voice_model: str = Field(default="default")
    file_path: str = Field(default="") # Where the generated audio is saved
    created_at: datetime = Field(default_factory=datetime.utcnow)
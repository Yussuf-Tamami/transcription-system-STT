from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Transcription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    filepath: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="processing")  # processing, done, error
    transcription_text: Optional[str] = None
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import Column, TEXT

# We need quotes around "TranscriptionChunk" to avoid circular import issues
class Upload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
   
    source_type: str = Field(default="file")  # "file" or "live_stream"
    status: str = Field(default="pending")    # "pending", "processing", "completed", "failed"
    
    speaker_count: int = Field(default=0)
    
    # Used if speaker_count == 1
    full_text: str | None = Field(default=None, sa_column=Column(TEXT)) 
    
    # Using timezone-aware UTC datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 1-to-Many Relationship: Links to the chunks table
    chunks: List["TranscriptionChunk"] = Relationship(back_populates="upload")
    file_path: str | None = Field(default=None)  
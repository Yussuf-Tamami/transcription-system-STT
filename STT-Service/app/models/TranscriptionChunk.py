from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from sqlalchemy import Column, TEXT

class TranscriptionChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Key linking back to the Upload table
    upload_id: int = Field(foreign_key="upload.id", index=True)
    
    # e.g., "SPEAKER_00", "SPEAKER_01"
    speaker_label: str 
    
    # Timestamps in seconds
    start_time: float
    end_time: float
    
    # The actual dialogue
    text: str = Field(sa_column=Column(TEXT))

    # Relationship back to the parent
    upload: Optional["Upload"] = Relationship(back_populates="chunks")
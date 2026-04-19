from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # Database and File storage
    DATABASE_URL: str
    UPLOAD_DIR: Path = Path("/app/storage/uploads")  # Directory for uploaded audio files
    USE_WHISPER: bool = True     # Toggle for backup testing
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
# Ensure upload directory exists on start
settings.UPLOAD_DIR.mkdir(exist_ok=True)
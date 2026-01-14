from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_name: str = "Poker MTT Helper"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/pokerhelper"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # CV Settings
    capture_fps: int = 2  # Frames per second to process
    jpeg_quality: int = 85  # JPEG compression quality
    
    # Model paths
    yolo_model_path: str = "models/cards_yolo.pt"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

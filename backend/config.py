"""Application configuration."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = f"sqlite+aiosqlite:///{str(DATA_DIR)}/resume_forge.db"

    # File upload
    upload_dir: Path = UPLOAD_DIR
    max_file_size: int = 20 * 1024 * 1024  # 20MB
    max_total_size: int = 100 * 1024 * 1024  # 100MB

    jwt_secret: str = "change-me-in-production"

    # CORS
    cors_origins: str = "http://localhost:5173"

    # Activation system (set to "true" to require activation codes)
    require_activation: str = ""

    # AI settings
    default_model: str = "zhipu/glm-4"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    zhipu_api_key: str = ""
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    minimax_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

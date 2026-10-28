import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PARQUET_DIR = DATA_DIR / "parquet"
MODELS_DIR = DATA_DIR / "models"
REPORTS_DIR = DATA_DIR / "reports"
DB_PATH = DATA_DIR / "datamind.db"

for directory in [DATA_DIR, UPLOAD_DIR, PARQUET_DIR, MODELS_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "DataMind-AI"
    app_version: str = "2.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = True
    
    # Server Binding
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8005"))
    cors_origins: List[str] = ["*"]
    
    # Database
    database_url: str = f"sqlite:///{DB_PATH}"
    
    # Storage & Upload Limits
    max_upload_size_mb: int = 100
    allowed_extensions: List[str] = [".csv", ".xlsx", ".xls", ".json", ".parquet"]
    
    # LLM & Agent Keys
    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    default_llm_provider: str = os.getenv("LLM_PROVIDER", "groq")

settings = Settings()

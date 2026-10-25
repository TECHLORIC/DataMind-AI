import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PARQUET_DIR = DATA_DIR / "parquet"
MODELS_DIR = DATA_DIR / "models"
REPORTS_DIR = DATA_DIR / "reports"
DB_PATH = DATA_DIR / "datamind.db"

# Ensure all directories exist
for directory in [DATA_DIR, UPLOAD_DIR, PARQUET_DIR, MODELS_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "DataMind AI"
    app_version: str = "1.0.0"
    debug: bool = True
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    default_llm_provider: str = os.getenv("LLM_PROVIDER", "groq")

settings = Settings()

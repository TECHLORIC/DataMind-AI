import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, BASE_DIR
from app.core.errors import DataMindException, datamind_exception_handler
from app.models.db.database import engine, Base, SessionLocal
from app.models.db.entities import DatasetRecord
from app.api.v1.router import api_router
from app.agents.data_prep import DataPrepAgent
from app.services.storage_service import StorageService
from app.utils.validation import validate_and_load_file

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production Multi-Agent Data Analytics & AutoML Platform"
)

# Exception handlers
app.add_exception_handler(DataMindException, datamind_exception_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount versioned API
app.include_router(api_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "orchestrator": "LangGraph Multi-Agent Architecture",
        "agents": ["DataPrepAgent", "AnalystAgent", "VisualizationAgent", "MLAgent", "SupervisorAgent"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)

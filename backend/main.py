import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings, BASE_DIR
from app.api.routes import router as api_router
from app.models.db_models import SessionLocal, DatasetRecord
from app.engine.ingestion import IngestionEngine
from app.engine.profiler import ProfilerEngine
from app.engine.dashboard_generator import DashboardGenerator
from app.engine.insights_engine import InsightsEngine

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Autonomous Business Intelligence & Data Analytics Platform"
)

# CORS configuration for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "llm_provider": settings.default_llm_provider,
        "has_groq_key": bool(settings.groq_api_key),
        "has_openai_key": bool(settings.openai_api_key)
    }

@app.on_event("startup")
def startup_event():
    """Ensure at least sample datasets are ingested on startup so user has immediate rich data to explore."""
    db = SessionLocal()
    try:
        count = db.query(DatasetRecord).count()
        if count == 0:
            samples_dir = BASE_DIR / "sample_datasets"
            sales_file = samples_dir / "sales_analytics.csv"
            if sales_file.exists():
                print("Seeding initial dataset: Global Sales & Profitability...")
                ingest_info = IngestionEngine.process_file(sales_file, "Global Sales & Profitability")
                profile = ProfilerEngine.profile_parquet(
                    Path(ingest_info["parquet_path"]),
                    ingest_info["dataset_id"],
                    "Global Sales & Profitability",
                    "sales_analytics.csv",
                    "csv"
                )
                dash = DashboardGenerator.generate_dashboard(Path(ingest_info["parquet_path"]), profile)
                insights = InsightsEngine.generate_insights(Path(ingest_info["parquet_path"]), profile)

                rec = DatasetRecord(
                    id=ingest_info["dataset_id"],
                    name="Global Sales & Profitability",
                    filename="sales_analytics.csv",
                    file_format="csv",
                    file_size_mb=ingest_info["file_size_mb"],
                    row_count=ingest_info["row_count"],
                    col_count=ingest_info["col_count"],
                    raw_path=ingest_info["raw_path"],
                    parquet_path=ingest_info["parquet_path"],
                    profile_json=profile.model_dump_json(),
                    dashboard_json=dash.model_dump_json(),
                    insights_json=insights.model_dump_json()
                )
                db.add(rec)
                db.commit()
                print("Initial dataset successfully seeded!")
    except Exception as e:
        print(f"Warning during seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

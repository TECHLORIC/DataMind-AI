import json
import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.models.db.database import get_db
from app.models.db.entities import DatasetRecord
from app.models.domain.dataset import FilterCondition, DashboardSpec, DatasetProfile
from app.services.storage_service import StorageService
from app.services.duckdb_service import DuckDBService
from app.utils.validation import validate_and_load_file
from app.agents.data_prep import DataPrepAgent
from app.core.config import BASE_DIR

router = APIRouter()

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts CSV/Excel data uploads.
    Data Prep Agent sanitizes encodings, imputes missing values,
    and returns a statistical overview for the dashboard.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    dataset_id, raw_path = StorageService.save_raw_upload(file.filename, contents)

    # Validate and clean data via DataPrepAgent
    df = validate_and_load_file(raw_path, file.filename)
    clean_df, profile, dashboard = DataPrepAgent.clean_and_profile(
        df=df,
        dataset_id=dataset_id,
        name=Path(file.filename).stem.replace("_", " ").title(),
        filename=file.filename,
        file_format=Path(file.filename).suffix.lstrip(".").lower(),
        file_size_mb=round(len(contents) / (1024 * 1024), 3)
    )

    # Save clean Parquet
    parquet_path = StorageService.save_clean_parquet(dataset_id, clean_df)

    # Persist database record
    record = DatasetRecord(
        id=dataset_id,
        name=profile.name,
        filename=file.filename,
        file_format=profile.file_format,
        file_size_mb=profile.memory_usage_mb,
        row_count=profile.total_rows,
        col_count=profile.total_columns,
        raw_path=str(parquet_path),
        parquet_path=str(parquet_path),
        profile_json=profile.model_dump_json(),
        dashboard_json=dashboard.model_dump_json(),
        cleaning_report_json=profile.cleaning_report.model_dump_json() if profile.cleaning_report else None
    )
    db.add(record)
    db.commit()

    return {
        "dataset_id": dataset_id,
        "name": profile.name,
        "profile": profile,
        "dashboard": dashboard,
        "cleaning_report": profile.cleaning_report
    }

@router.get("")
def list_datasets(db: Session = Depends(get_db)):
    records = db.query(DatasetRecord).order_by(DatasetRecord.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "filename": r.filename,
            "file_format": r.file_format,
            "file_size_mb": r.file_size_mb,
            "row_count": r.row_count,
            "col_count": r.col_count,
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]

@router.get("/{dataset_id}")
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = json.loads(record.profile_json) if record.profile_json else {}
    dashboard = json.loads(record.dashboard_json) if record.dashboard_json else {}
    cleaning_report = json.loads(record.cleaning_report_json) if record.cleaning_report_json else {}

    return {
        "id": record.id,
        "name": record.name,
        "filename": record.filename,
        "profile": profile,
        "dashboard": dashboard,
        "cleaning_report": cleaning_report
    }

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    p = Path(record.parquet_path)
    if p.exists():
        p.unlink()

    db.delete(record)
    db.commit()
    return {"success": True, "deleted_id": dataset_id}

@router.post("/{dataset_id}/dashboard/filter")
def filter_dashboard(
    dataset_id: str,
    filters: List[FilterCondition],
    db: Session = Depends(get_db)
):
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile_dict = json.loads(record.profile_json)
    profile = DatasetProfile(**profile_dict)
    parquet_path = Path(record.parquet_path)

    # Re-calculate KPIs under filters
    where_sql = DuckDBService.build_where_clause(filters)
    total_res = DuckDBService.execute_query(parquet_path, f"SELECT COUNT(*) AS value FROM dataset {where_sql}")
    filtered_rows = total_res["rows"][0]["value"] if total_res["rows"] else 0

    dashboard_dict = json.loads(record.dashboard_json)
    dashboard = DashboardSpec(**dashboard_dict)
    dashboard.applied_filters = filters
    if dashboard.kpis:
        dashboard.kpis[0].value = filtered_rows
        dashboard.kpis[0].formatted_value = f"{filtered_rows:,}"

    return dashboard

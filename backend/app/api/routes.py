import json
import shutil
import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.config import UPLOAD_DIR, PARQUET_DIR, BASE_DIR
from app.models.db_models import get_db, DatasetRecord, ChatHistoryRecord, MLExperimentRecord
from app.models.schemas import (
    DatasetProfile, DashboardSpec, QueryRequest, ChatRequest,
    ChatResponse, InsightsResponse, MLTrainRequest, MLTrainResponse,
    MLPredictRequest, MLPredictResponse, FilterCondition
)
from app.engine.ingestion import IngestionEngine
from app.engine.profiler import ProfilerEngine
from app.engine.sql_engine import SQLEngine
from app.engine.dashboard_generator import DashboardGenerator
from app.engine.insights_engine import InsightsEngine
from app.engine.ml_engine import MLEngine
from app.engine.ai_agent import AIAgent

router = APIRouter(prefix="/api/v1")

# -------------------------------------------------------------------
# DATASET MANAGEMENT
# -------------------------------------------------------------------
@router.post("/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload CSV, Excel, JSON, or Parquet file and trigger dynamic profiling & auto-dashboard."""
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".csv", ".txt", ".xlsx", ".xls", ".json", ".parquet"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {suffix}")

    # Save uploaded file
    target_path = UPLOAD_DIR / file.filename
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Ingestion
        ingest_info = IngestionEngine.process_file(
            file_path=target_path,
            dataset_name=dataset_name or Path(file.filename).stem
        )
        dataset_id = ingest_info["dataset_id"]

        # Profiling
        profile = ProfilerEngine.profile_parquet(
            parquet_path=Path(ingest_info["parquet_path"]),
            dataset_id=dataset_id,
            name=ingest_info["name"],
            filename=ingest_info["filename"],
            file_format=ingest_info["file_format"]
        )

        # Generate initial dashboard
        dashboard = DashboardGenerator.generate_dashboard(
            parquet_path=Path(ingest_info["parquet_path"]),
            profile=profile
        )

        # Generate automated insights
        insights = InsightsEngine.generate_insights(
            parquet_path=Path(ingest_info["parquet_path"]),
            profile=profile
        )

        # Save to database
        record = DatasetRecord(
            id=dataset_id,
            name=ingest_info["name"],
            filename=ingest_info["filename"],
            file_format=ingest_info["file_format"],
            file_size_mb=ingest_info["file_size_mb"],
            row_count=ingest_info["row_count"],
            col_count=ingest_info["col_count"],
            raw_path=ingest_info["raw_path"],
            parquet_path=ingest_info["parquet_path"],
            profile_json=profile.model_dump_json(),
            dashboard_json=dashboard.model_dump_json(),
            insights_json=insights.model_dump_json()
        )
        db.add(record)
        db.commit()

        return {
            "status": "success",
            "dataset_id": dataset_id,
            "name": ingest_info["name"],
            "row_count": ingest_info["row_count"],
            "col_count": ingest_info["col_count"],
            "profile": profile,
            "dashboard": dashboard,
            "insights": insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process dataset: {str(e)}")

@router.post("/datasets/load-sample/{sample_name}")
async def load_sample_dataset(sample_name: str, db: Session = Depends(get_db)):
    """Loads one of the pre-configured sample datasets (sales, education, healthcare, finance)."""
    samples_dir = BASE_DIR / "sample_datasets"
    sample_mapping = {
        "sales": ("sales_analytics.csv", "Global Sales & Profitability"),
        "education": ("student_performance.csv", "Student Academic Performance"),
        "healthcare": ("healthcare_patients.csv", "Hospital Patient Diagnostics"),
        "finance": ("financial_transactions.csv", "Corporate Financial Transactions"),
        "cfpb": ("cfpb_consumer_complaints.csv", "CFPB Consumer Financial Complaints")
    }

    if sample_name.lower() not in sample_mapping:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_name}' not found. Choose from {list(sample_mapping.keys())}")

    filename, pretty_title = sample_mapping[sample_name.lower()]
    file_path = samples_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample dataset file missing on server.")

    # Process and ingest
    ingest_info = IngestionEngine.process_file(file_path=file_path, dataset_name=pretty_title)
    dataset_id = ingest_info["dataset_id"]

    profile = ProfilerEngine.profile_parquet(
        parquet_path=Path(ingest_info["parquet_path"]),
        dataset_id=dataset_id,
        name=pretty_title,
        filename=filename,
        file_format=ingest_info["file_format"]
    )

    dashboard = DashboardGenerator.generate_dashboard(
        parquet_path=Path(ingest_info["parquet_path"]),
        profile=profile
    )

    insights = InsightsEngine.generate_insights(
        parquet_path=Path(ingest_info["parquet_path"]),
        profile=profile
    )

    record = DatasetRecord(
        id=dataset_id,
        name=pretty_title,
        filename=filename,
        file_format=ingest_info["file_format"],
        file_size_mb=ingest_info["file_size_mb"],
        row_count=ingest_info["row_count"],
        col_count=ingest_info["col_count"],
        raw_path=ingest_info["raw_path"],
        parquet_path=ingest_info["parquet_path"],
        profile_json=profile.model_dump_json(),
        dashboard_json=dashboard.model_dump_json(),
        insights_json=insights.model_dump_json()
    )
    db.add(record)
    db.commit()

    return {
        "status": "success",
        "dataset_id": dataset_id,
        "name": pretty_title,
        "profile": profile,
        "dashboard": dashboard,
        "insights": insights
    }

@router.get("/datasets")
async def list_datasets(db: Session = Depends(get_db)):
    """List all available datasets."""
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
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Deletes a dataset and its associated cache files."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        p_path = Path(record.parquet_path)
        if p_path.exists():
            p_path.unlink()
    except Exception:
        pass

    db.delete(record)
    db.commit()
    return {"status": "success", "message": f"Dataset {dataset_id} removed."}

@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Retrieve full metadata for a dataset."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = json.loads(record.profile_json) if record.profile_json else None
    dashboard = json.loads(record.dashboard_json) if record.dashboard_json else None
    insights = json.loads(record.insights_json) if record.insights_json else None

    return {
        "id": record.id,
        "name": record.name,
        "filename": record.filename,
        "file_format": record.file_format,
        "file_size_mb": record.file_size_mb,
        "row_count": record.row_count,
        "col_count": record.col_count,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "profile": profile,
        "dashboard": dashboard,
        "insights": insights
    }

@router.get("/datasets/{dataset_id}/profile")
async def get_dataset_profile(dataset_id: str, db: Session = Depends(get_db)):
    """Get dynamic profile and column schema."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not record.profile_json:
        raise HTTPException(status_code=404, detail="Profile not generated")
    return json.loads(record.profile_json)

@router.get("/datasets/{dataset_id}/dashboard")
async def get_dataset_dashboard(dataset_id: str, db: Session = Depends(get_db)):
    """Get the auto-generated dashboard."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not record.dashboard_json:
        raise HTTPException(status_code=404, detail="Dashboard not generated")
    return json.loads(record.dashboard_json)

@router.post("/datasets/{dataset_id}/dashboard/filter")
async def filter_dashboard(
    dataset_id: str,
    filters: List[FilterCondition],
    db: Session = Depends(get_db)
):
    """Recomputes KPI cards and charts dynamically based on cross-filter conditions."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = DatasetProfile(**json.loads(record.profile_json))
    filtered_dashboard = DashboardGenerator.generate_dashboard(
        parquet_path=Path(record.parquet_path),
        profile=profile,
        filters=filters
    )
    return filtered_dashboard

@router.post("/datasets/{dataset_id}/query")
async def execute_query(
    dataset_id: str,
    req: QueryRequest,
    db: Session = Depends(get_db)
):
    """Execute raw read-only SQL query against DuckDB."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    sql = req.sql or "SELECT * FROM dataset LIMIT 100"
    try:
        result = SQLEngine.execute_query(
            parquet_path=Path(record.parquet_path),
            sql=sql,
            limit=req.limit or 1000
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------------
# NATURAL LANGUAGE DATA CHAT
# -------------------------------------------------------------------
@router.post("/chat/query")
async def chat_with_data(req: ChatRequest, db: Session = Depends(get_db)):
    """Ask questions in natural language, planned with SQL and verified via DuckDB."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == req.dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = DatasetProfile(**json.loads(record.profile_json))
    response = AIAgent.answer_query(
        parquet_path=Path(record.parquet_path),
        profile=profile,
        question=req.message,
        conversation_id=req.conversation_id
    )

    # Save chat history
    chat_rec = ChatHistoryRecord(
        conversation_id=response.conversation_id,
        dataset_id=req.dataset_id,
        question=req.message,
        intent=response.intent,
        sql_query=response.sql_query,
        explanation=response.explanation
    )
    db.add(chat_rec)
    db.commit()

    return response

# -------------------------------------------------------------------
# AUTOMATED INSIGHTS
# -------------------------------------------------------------------
@router.post("/insights/generate")
async def generate_insights(dataset_id: str, db: Session = Depends(get_db)):
    """Generate statistical trends, anomalies, and correlations."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = DatasetProfile(**json.loads(record.profile_json))
    insights = InsightsEngine.generate_insights(
        parquet_path=Path(record.parquet_path),
        profile=profile
    )

    record.insights_json = insights.model_dump_json()
    db.commit()

    return insights

# -------------------------------------------------------------------
# PREDICTIVE ANALYTICS & AUTOML
# -------------------------------------------------------------------
@router.post("/ml/train")
async def train_ml_model(req: MLTrainRequest, db: Session = Depends(get_db)):
    """Trains regression, classification, forecasting, or clustering model."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == req.dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = DatasetProfile(**json.loads(record.profile_json))
    try:
        response = MLEngine.train_model(
            parquet_path=Path(record.parquet_path),
            profile=profile,
            request=req
        )

        # Save experiment
        exp = MLExperimentRecord(
            model_id=response.model_id,
            dataset_id=req.dataset_id,
            task_type=response.task_type,
            target_column=response.target_column,
            algorithm_name=response.algorithm_name,
            metrics_json=json.dumps(response.metrics),
            summary=response.summary
        )
        db.add(exp)
        db.commit()

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ML training failed: {str(e)}")

@router.post("/ml/predict")
async def predict_ml_model(req: MLPredictRequest):
    """Generates prediction from trained model on provided feature values."""
    try:
        return MLEngine.predict(model_id=req.model_id, request=req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reports/pdf/{dataset_id}", response_class=HTMLResponse)
async def generate_pdf_report(dataset_id: str, db: Session = Depends(get_db)):
    """Generates an executive print-optimized BI report with automated PDF print trigger."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = json.loads(record.profile_json) if record.profile_json else {}
    dashboard = json.loads(record.dashboard_json) if record.dashboard_json else {}
    insights = json.loads(record.insights_json) if record.insights_json else {}

    kpi_html = ""
    for k in dashboard.get("kpis", []):
        kpi_html += f"""
        <div class="kpi-card">
            <div class="kpi-title">{k.get('title')}</div>
            <div class="kpi-val">{k.get('formatted_value')}</div>
            <div class="kpi-sub">{k.get('aggregation', '').upper()} &bull; {k.get('measure_column')}</div>
        </div>
        """

    insights_html = ""
    for item in insights.get("insights", [])[:6]:
        insights_html += f"""
        <div class="insight-row">
            <span class="badge {item.get('importance')}">{item.get('category').upper()}</span>
            <strong>{item.get('title')}</strong>
            <p>{item.get('description')}</p>
        </div>
        """

    charts_html = ""
    for ch in dashboard.get("charts", [])[:4]:
        rows_html = ""
        for r in ch.get("data", [])[:6]:
            vals = list(r.values())
            c_name = vals[0] if len(vals) > 0 else ""
            c_val = vals[1] if len(vals) > 1 else ""
            rows_html += f"<tr><td>{c_name}</td><td style='text-align:right; font-weight:600;'>{c_val}</td></tr>"

        charts_html += f"""
        <div class="chart-summary">
            <h3>{ch.get('title')}</h3>
            <p class="chart-desc">{ch.get('description', '')}</p>
            <table class="data-table">
                <thead><tr><th>Category</th><th style='text-align:right;'>Value</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
            {f'<div class="insight-pill">&bull; {ch.get("insight")}</div>' if ch.get('insight') else ''}
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Executive BI Report - {record.name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #1e293b;
            background: #fff;
            margin: 0;
            padding: 30px;
            font-size: 13px;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #4f46e5;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .brand {{
            font-size: 22px;
            font-weight: 800;
            color: #4f46e5;
        }}
        .subbrand {{
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .meta {{
            text-align: right;
            font-size: 11px;
            color: #64748b;
        }}
        .section-title {{
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
            margin: 25px 0 12px 0;
            border-left: 4px solid #4f46e5;
            padding-left: 8px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }}
        .kpi-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 16px;
        }}
        .kpi-title {{
            font-size: 11px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
        }}
        .kpi-val {{
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            margin: 4px 0;
        }}
        .kpi-sub {{
            font-size: 10px;
            color: #94a3b8;
        }}
        .summary-box {{
            background: #eef2ff;
            border-left: 4px solid #6366f1;
            padding: 12px 16px;
            border-radius: 4px;
            font-size: 13px;
            color: #312e81;
            margin-bottom: 25px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 25px;
        }}
        .chart-summary {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 14px;
        }}
        .chart-summary h3 {{
            margin: 0 0 4px 0;
            font-size: 13px;
            color: #1e293b;
        }}
        .chart-desc {{
            margin: 0 0 10px 0;
            font-size: 11px;
            color: #64748b;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        }}
        .data-table th {{
            background: #e2e8f0;
            padding: 5px 8px;
            text-align: left;
            color: #475569;
        }}
        .data-table td {{
            padding: 5px 8px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .insight-pill {{
            margin-top: 10px;
            font-size: 11px;
            color: #4338ca;
            background: #e0e7ff;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        .insight-row {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 8px;
        }}
        .insight-row p {{
            margin: 4px 0 0 0;
            color: #475569;
            font-size: 12px;
        }}
        .badge {{
            font-size: 9px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            margin-right: 6px;
        }}
        .badge.high {{ background: #fee2e2; color: #dc2626; }}
        .badge.medium {{ background: #e0e7ff; color: #4338ca; }}
        .badge.info {{ background: #f1f5f9; color: #475569; }}
        .print-btn {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #4f46e5;
            color: #fff;
            padding: 10px 18px;
            border-radius: 8px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">Save as PDF</button>

    <div class="header">
        <div>
            <div class="brand">DataMind AI</div>
            <div class="subbrand">Autonomous Business Intelligence Report</div>
        </div>
        <div class="meta">
            <div><strong>Dataset:</strong> {record.name}</div>
            <div><strong>Total Records:</strong> {record.row_count:,} &bull; <strong>Columns:</strong> {record.col_count}</div>
            <div><strong>Generated:</strong> {datetime.datetime.utcnow().strftime('%B %d, %Y %H:%M UTC')}</div>
        </div>
    </div>

    <div class="summary-box">
        <strong>Executive Overview:</strong> {dashboard.get('executive_summary', 'Automated analytical summary across dataset attributes.')}
    </div>

    <div class="section-title">Key Performance Indicators</div>
    <div class="kpi-grid">
        {kpi_html}
    </div>

    <div class="section-title">Visual Breakdowns & Slices</div>
    <div class="charts-grid">
        {charts_html}
    </div>

    <div class="section-title">Automated AI Insights & Discoveries</div>
    <div>
        {insights_html}
    </div>

    <script>
        window.onload = function() {{
            setTimeout(function() {{ window.print(); }}, 600);
        }};
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

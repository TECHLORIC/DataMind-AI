import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.db.database import get_db
from app.models.db.entities import DatasetRecord, MLModelRecord
from app.models.domain.ml import MLTrainRequest, MLTrainResponse, MLPredictRequest, MLPredictResponse
from app.agents.ml_agent import MLAgent

router = APIRouter()

@router.post("/train", response_model=MLTrainResponse)
async def train_model(req: MLTrainRequest, db: Session = Depends(get_db)):
    """
    AutoML & Pattern Discovery endpoint.
    Builds Scikit-learn and XGBoost pipelines, auto-selects target variables,
    clusters data for hidden patterns, and outputs accuracy, confidence, and feature importance.
    """
    record = db.query(DatasetRecord).filter(DatasetRecord.id == req.dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        response = MLAgent.train(parquet_path=Path(record.parquet_path), request=req)
        
        # Save model record
        m_rec = MLModelRecord(
            model_id=response.model_id,
            dataset_id=req.dataset_id,
            task_type=response.task_type,
            target_column=response.target_column,
            algorithm_name=response.algorithm_name,
            metrics_json=json.dumps(response.metrics),
            summary=response.summary
        )
        db.add(m_rec)
        db.commit()

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AutoML training failed: {str(e)}")

@router.post("/predict", response_model=MLPredictResponse)
async def predict_model(req: MLPredictRequest):
    """Generates What-If inference predictions from trained models."""
    try:
        return MLAgent.predict(model_id=req.model_id, request=req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")

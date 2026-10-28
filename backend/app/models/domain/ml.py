from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MLTrainRequest(BaseModel):
    dataset_id: str
    task_type: Optional[str] = "auto"  # 'auto', 'regression', 'classification', 'clustering'
    target_column: Optional[str] = None
    feature_columns: Optional[List[str]] = None
    n_clusters: Optional[int] = 3

class MLTrainResponse(BaseModel):
    model_id: str
    dataset_id: str
    task_type: str
    target_column: Optional[str] = None
    features_used: List[str] = []
    algorithm_name: str
    metrics: Dict[str, Any] = {}
    feature_importance: List[Dict[str, Any]] = []
    model_leaderboard: List[Dict[str, Any]] = []
    actual_vs_predicted: Optional[List[Dict[str, Any]]] = None
    confusion_matrix: Optional[Dict[str, Any]] = None
    cluster_profiles: Optional[Dict[str, Any]] = None
    cluster_scatter_data: Optional[List[Dict[str, Any]]] = None
    plotly_spec: Optional[Dict[str, Any]] = None
    feature_meta: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.95
    created_at: str
    summary: str

class MLPredictRequest(BaseModel):
    model_id: str
    features: Dict[str, Any]

class MLPredictResponse(BaseModel):
    model_id: str
    predicted_value: Any
    confidence_score: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    task_type: str

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class ColumnMeta(BaseModel):
    name: str
    data_type: str  # 'int', 'float', 'string', 'datetime', 'boolean'
    semantic_type: str  # 'measure', 'dimension', 'time', 'identifier', 'target_candidate'
    nullable: bool = False
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    cardinality_ratio: float = 0.0
    sample_values: List[Any] = []
    min_val: Optional[Union[float, int, str]] = None
    max_val: Optional[Union[float, int, str]] = None
    mean_val: Optional[float] = None
    median_val: Optional[float] = None
    std_val: Optional[float] = None

class DatasetProfile(BaseModel):
    dataset_id: str
    name: str
    filename: str
    file_format: str
    total_rows: int
    total_columns: int
    completeness: float
    duplicate_rows: int
    memory_usage_mb: float
    columns: List[ColumnMeta]
    primary_measures: List[str] = []
    primary_dimensions: List[str] = []
    primary_time_column: Optional[str] = None
    primary_id_column: Optional[str] = None
    created_at: str

class FilterCondition(BaseModel):
    column: str
    operator: str  # 'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'in', 'between'
    value: Any

class QueryRequest(BaseModel):
    dataset_id: str
    sql: Optional[str] = None
    filters: Optional[List[FilterCondition]] = None
    limit: Optional[int] = 1000

class ChartSpec(BaseModel):
    id: str
    chart_type: str  # 'kpi', 'bar', 'line', 'area', 'pie', 'scatter', 'donut', 'histogram', 'table'
    title: str
    description: Optional[str] = ""
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    group_by: Optional[str] = None
    aggregation: Optional[str] = "sum"  # 'sum', 'avg', 'count', 'min', 'max'
    data: List[Dict[str, Any]] = []
    insight: Optional[str] = None
    echarts_option: Optional[Dict[str, Any]] = None

class KPICard(BaseModel):
    id: str
    title: str
    value: Union[float, int, str]
    formatted_value: str
    aggregation: str
    measure_column: str
    change_percentage: Optional[float] = None
    trend_direction: Optional[str] = None  # 'up', 'down', 'neutral'
    sparkline_data: Optional[List[float]] = None

class DashboardSpec(BaseModel):
    dataset_id: str
    title: str
    generated_at: str
    kpis: List[KPICard]
    charts: List[ChartSpec]
    executive_summary: str
    applied_filters: Optional[List[FilterCondition]] = None

class ChatRequest(BaseModel):
    dataset_id: str
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    dataset_id: str
    question: str
    intent: str
    explanation: str
    sql_query: Optional[str] = None
    table_data: Optional[List[Dict[str, Any]]] = None
    chart: Optional[ChartSpec] = None
    confidence: float = 1.0

class InsightItem(BaseModel):
    id: str
    category: str  # 'trend', 'anomaly', 'correlation', 'segmentation', 'distribution'
    importance: str  # 'high', 'medium', 'info'
    title: str
    description: str
    metric: Optional[str] = None
    score: Optional[float] = None
    evidence: Dict[str, Any] = {}
    chart: Optional[ChartSpec] = None

class InsightsResponse(BaseModel):
    dataset_id: str
    generated_at: str
    total_insights: int
    insights: List[InsightItem]
    executive_takeaways: List[str]

class MLTrainRequest(BaseModel):
    dataset_id: str
    task_type: Optional[str] = "auto"  # 'auto', 'regression', 'classification', 'forecasting', 'clustering'
    target_column: Optional[str] = None
    feature_columns: Optional[List[str]] = None
    time_column: Optional[str] = None
    forecast_horizon: Optional[int] = 12

class MLTrainResponse(BaseModel):
    model_id: str
    dataset_id: str
    task_type: str
    target_column: Optional[str]
    features_used: List[str]
    algorithm_name: str
    metrics: Dict[str, Any]
    feature_importance: List[Dict[str, Any]] = []
    model_leaderboard: List[Dict[str, Any]] = []
    target_distribution: Optional[Dict[str, Any]] = None
    actual_vs_predicted: Optional[List[Dict[str, Any]]] = None
    residuals: Optional[List[Dict[str, Any]]] = None
    confusion_matrix: Optional[Dict[str, Any]] = None
    forecast_data: Optional[List[Dict[str, Any]]] = None
    cluster_centers: Optional[List[Dict[str, Any]]] = None
    feature_meta: Optional[Dict[str, Any]] = None
    created_at: str
    summary: str

class MLPredictRequest(BaseModel):
    model_id: str
    features: Dict[str, Any]

class MLPredictResponse(BaseModel):
    model_id: str
    prediction: Union[float, str, int]
    probabilities: Optional[Dict[str, float]] = None
    confidence: Optional[float] = None
    explanation: str

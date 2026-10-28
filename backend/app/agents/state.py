from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel

class AgentState(TypedDict, total=False):
    # Core Context
    dataset_id: str
    parquet_path: str
    schema_info: Dict[str, Any]
    user_query: str
    conversation_id: str
    
    # Flow Control
    next_step: Optional[str]           # 'analyst', 'visualization', 'ml', 'final'
    route_history: List[str]           # History of agent invocations
    
    # Data Prep Artifacts
    cleaning_report: Optional[Dict[str, Any]]
    data_summary: Optional[Dict[str, Any]]
    
    # Analyst Artifacts
    analyst_text: Optional[str]
    sql_executed: Optional[str]
    table_data: Optional[List[Dict[str, Any]]]
    intent: Optional[str]
    
    # Visualization Artifacts
    plotly_spec: Optional[Dict[str, Any]]
    echarts_spec: Optional[Dict[str, Any]]
    chart_spec: Optional[Dict[str, Any]]
    
    # ML Artifacts
    ml_task: Optional[str]
    model_metrics: Optional[Dict[str, Any]]
    feature_importance: Optional[List[Dict[str, Any]]]
    cluster_profiles: Optional[Dict[str, Any]]
    ml_summary: Optional[str]
    
    # Confidence & Error Handling
    confidence_score: float
    error_message: Optional[str]

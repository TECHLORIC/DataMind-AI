from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.domain.dataset import ChartSpec

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
    plotly_spec: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    routed_agents: List[str] = []

import json
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.db.database import get_db
from app.models.db.entities import DatasetRecord, ChatHistoryRecord
from app.models.domain.chat import ChatRequest, ChatResponse
from app.models.domain.dataset import ChartSpec
from app.agents.graph import analytics_graph

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def chat_with_data(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Conversational Analytics Q&A endpoint.
    LangGraph Supervisor Agent routes queries to Analyst and Visualization agents,
    generating verified DuckDB text insights and dynamic Plotly JSON graphs.
    """
    record = db.query(DatasetRecord).filter(DatasetRecord.id == req.dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile_dict = json.loads(record.profile_json) if record.profile_json else {}
    conv_id = req.conversation_id or f"conv_{uuid.uuid4().hex[:8]}"

    # Fetch recent conversation context for follow-up support
    recent_history = db.query(ChatHistoryRecord).filter(
        ChatHistoryRecord.conversation_id == conv_id
    ).order_by(ChatHistoryRecord.id.desc()).limit(5).all()
    chat_history_list = [{"question": h.question, "intent": h.intent} for h in reversed(recent_history)]

    # Execute LangGraph Multi-Agent Workflow
    initial_state = {
        "dataset_id": req.dataset_id,
        "parquet_path": record.parquet_path,
        "schema_info": profile_dict,
        "user_query": req.message,
        "conversation_id": conv_id,
        "chat_history": chat_history_list,
        "route_history": []
    }

    final_state = analytics_graph.invoke(initial_state)

    chart_spec = None
    if final_state.get("chart_spec"):
        chart_spec = ChartSpec(**final_state["chart_spec"])

    # Persist in chat history
    history = ChatHistoryRecord(
        conversation_id=conv_id,
        dataset_id=req.dataset_id,
        question=req.message,
        intent=final_state.get("intent", "analytical_query"),
        sql_query=final_state.get("sql_executed"),
        explanation=final_state.get("analyst_text", ""),
        plotly_spec_json=json.dumps(final_state.get("plotly_spec")) if final_state.get("plotly_spec") else None
    )
    db.add(history)
    db.commit()

    return ChatResponse(
        conversation_id=conv_id,
        dataset_id=req.dataset_id,
        question=req.message,
        intent=final_state.get("intent", "analytical_query"),
        explanation=final_state.get("analyst_text", "Analysis complete."),
        sql_query=final_state.get("sql_executed"),
        table_data=final_state.get("table_data"),
        chart=chart_spec,
        plotly_spec=final_state.get("plotly_spec"),
        confidence=final_state.get("confidence_score", 0.95),
        routed_agents=final_state.get("route_history", [])
    )

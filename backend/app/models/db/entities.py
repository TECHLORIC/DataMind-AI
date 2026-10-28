import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from app.models.db.database import Base

class DatasetRecord(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    filename = Column(String)
    file_format = Column(String)
    file_size_mb = Column(Float)
    row_count = Column(Integer)
    col_count = Column(Integer)
    raw_path = Column(String, nullable=True)
    parquet_path = Column(String)
    profile_json = Column(Text)
    dashboard_json = Column(Text, nullable=True)
    cleaning_report_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChatHistoryRecord(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, index=True)
    dataset_id = Column(String, index=True)
    question = Column(Text)
    intent = Column(String)
    sql_query = Column(Text, nullable=True)
    explanation = Column(Text)
    plotly_spec_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MLModelRecord(Base):
    __tablename__ = "ml_models"

    model_id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, index=True)
    task_type = Column(String)
    target_column = Column(String, nullable=True)
    algorithm_name = Column(String)
    metrics_json = Column(Text)
    summary = Column(Text)
    model_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

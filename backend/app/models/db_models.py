import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DB_PATH

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DatasetRecord(Base):
    __tablename__ = "datasets"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_format = Column(String(32), nullable=False)
    file_size_mb = Column(Float, default=0.0)
    row_count = Column(Integer, default=0)
    col_count = Column(Integer, default=0)
    raw_path = Column(Text, nullable=False)
    parquet_path = Column(Text, nullable=False)
    profile_json = Column(Text, nullable=True)
    dashboard_json = Column(Text, nullable=True)
    insights_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChatHistoryRecord(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), index=True)
    dataset_id = Column(String(64), index=True)
    question = Column(Text, nullable=False)
    intent = Column(String(64))
    sql_query = Column(Text, nullable=True)
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MLExperimentRecord(Base):
    __tablename__ = "ml_experiments"

    model_id = Column(String(64), primary_key=True, index=True)
    dataset_id = Column(String(64), index=True)
    task_type = Column(String(64))
    target_column = Column(String(255), nullable=True)
    algorithm_name = Column(String(255))
    metrics_json = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

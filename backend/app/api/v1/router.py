from fastapi import APIRouter
from app.api.v1.endpoints import datasets, chat, ml, reports

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets & Data Prep"])
api_router.include_router(chat.router, prefix="/chat", tags=["Conversational Analytics Q&A"])
api_router.include_router(ml.router, prefix="/ml", tags=["AutoML & Clustering"])
api_router.include_router(reports.router, prefix="/reports", tags=["Executive Reports"])

from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("datamind.errors")

class DataMindException(Exception):
    """Base exception for all DataMind-AI errors."""
    def __init__(self, message: str, code: str = "DATAMIND_ERROR", details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class CorruptedDataError(DataMindException):
    """Raised when an uploaded file is empty, truncated, or unparseable."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="CORRUPTED_DATA_ERROR", details=details)

class EncodingDetectionError(DataMindException):
    """Raised when file character encoding cannot be detected or decoded."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="ENCODING_ERROR", details=details)

class UnsupportedFormatError(DataMindException):
    """Raised when uploaded file format is not supported."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="UNSUPPORTED_FORMAT_ERROR", details=details)

class AgentExecutionError(DataMindException):
    """Raised when a LangGraph agent fails during execution."""
    def __init__(self, message: str, agent_name: str, details: dict = None):
        merged = details or {}
        merged["agent"] = agent_name
        super().__init__(message, code="AGENT_EXECUTION_ERROR", details=merged)

class QuerySecurityError(DataMindException):
    """Raised when an analytical query violates read-only safety rules."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="QUERY_SECURITY_ERROR", details=details)

async def datamind_exception_handler(request: Request, exc: DataMindException):
    logger.error(f"[{exc.code}] {exc.message} | Details: {exc.details}")
    status_map = {
        "CORRUPTED_DATA_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "ENCODING_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "UNSUPPORTED_FORMAT_ERROR": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "AGENT_EXECUTION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "QUERY_SECURITY_ERROR": status.HTTP_400_BAD_REQUEST,
        "DATAMIND_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    http_status = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(
        status_code=http_status,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

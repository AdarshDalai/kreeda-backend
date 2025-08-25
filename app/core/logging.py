"""
Structured logging configuration for Kreeda Backend
"""
import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "match_id"):
            log_entry["match_id"] = getattr(record, "match_id")
        if hasattr(record, "user_id"):
            log_entry["user_id"] = getattr(record, "user_id")
        if hasattr(record, "request_id"):
            log_entry["request_id"] = getattr(record, "request_id")
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


def setup_logging():
    """Configure logging for the application"""
    # Remove default handlers
    logging.getLogger().handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.DEBUG:
        # Human-readable format for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        log_level = logging.DEBUG
    else:
        # Structured logging for production
        formatter = StructuredFormatter()
        console_handler.setFormatter(formatter)
        log_level = logging.INFO
    
    # Configure root logger
    logging.getLogger().setLevel(log_level)
    logging.getLogger().addHandler(console_handler)
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if not settings.DEBUG else logging.INFO)
    
    return logging.getLogger("kreeda")


# Create logger instance
logger = setup_logging()

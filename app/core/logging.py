"""
Logging Configuration for Kreeda Backend
Structured logging with proper formatting and levels
"""
import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        extra_fields = getattr(record, 'extra_fields', None)
        if extra_fields:
            log_entry.update(extra_fields)

        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Text formatter for development"""

    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def get_log_level() -> int:
    """Get logging level from environment or settings"""
    level_str = os.environ.get('LOG_LEVEL', settings.LOG_LEVEL).upper()
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return level_map.get(level_str, logging.INFO)


def get_formatter() -> logging.Formatter:
    """Get appropriate formatter based on settings"""
    format_type = os.environ.get('LOG_FORMAT', settings.LOG_FORMAT).lower()

    if format_type == 'json':
        return JSONFormatter()
    else:
        return TextFormatter()


def setup_logging() -> logging.Logger:
    """Setup logging configuration"""
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(get_log_level())

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(get_log_level())
    console_handler.setFormatter(get_formatter())
    logger.addHandler(console_handler)

    # Create logger for this module
    app_logger = logging.getLogger('kreeda_backend')
    app_logger.setLevel(get_log_level())

    return app_logger


def get_request_logger() -> logging.Logger:
    """Get logger for request logging"""
    return logging.getLogger('kreeda_backend.requests')


def log_request(logger: logging.Logger, request_id: str, method: str, path: str, status_code: int, duration: float):
    """Log HTTP request details"""
    extra_fields = {
        'request_id': request_id,
        'method': method,
        'path': path,
        'status_code': status_code,
        'duration_ms': round(duration * 1000, 2)
    }

    if status_code >= 400:
        logger.warning(f"Request failed: {method} {path}", extra={'extra_fields': extra_fields})
    else:
        logger.info(f"Request completed: {method} {path}", extra={'extra_fields': extra_fields})


def log_error(logger: logging.Logger, error: Exception, request_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
    """Log error with context"""
    extra_fields = {
        'error_type': type(error).__name__,
        'error_message': str(error),
    }

    if request_id:
        extra_fields['request_id'] = request_id

    if context:
        extra_fields.update(context)

    logger.error(f"Error occurred: {type(error).__name__}", extra={'extra_fields': extra_fields})


# Global logger instance
logger = setup_logging()

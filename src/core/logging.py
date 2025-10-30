"""
Structured Logging Configuration for Kreeda Backend
Production-grade logging with JSON formatting and contextual information
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from src.config.settings import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    
    Outputs logs in JSON format with consistent structure:
    {
        "timestamp": "ISO8601",
        "level": "INFO|WARNING|ERROR|CRITICAL",
        "message": "Log message",
        "module": "module.name",
        "function": "function_name",
        "line": 123,
        "request_id": "uuid" (if available),
        "user_id": "uuid" (if available),
        "extra": {...}  (any additional context)
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields (request_id, user_id, etc.)
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        
        if hasattr(record, "method"):
            log_data["method"] = record.method
        
        # Add any other extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "request_id", "user_id", "duration_ms", "endpoint", "method"
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logging():
    """
    Setup logging configuration
    
    Configures:
    - JSON formatting for production
    - Different log levels based on environment
    - Console and file handlers
    - Filters to exclude sensitive data
    """
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("kreeda")
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use JSON formatter in production, simple format in development
    if settings.app_env == "production":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for errors (optional, can be disabled)
    # error_handler = logging.FileHandler("logs/error.log")
    # error_handler.setLevel(logging.ERROR)
    # error_handler.setFormatter(JSONFormatter())
    # logger.addHandler(error_handler)
    
    return logger


# Create default logger
logger = setup_logging()


def get_logger(name: str = "kreeda") -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (default: "kreeda")
    
    Returns:
        Logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("User created", extra={"user_id": str(user.id)})
    """
    return logging.getLogger(name)


class SensitiveDataFilter(logging.Filter):
    """
    Filter to prevent logging sensitive data
    
    Redacts fields like: password, token, secret, api_key
    """
    SENSITIVE_FIELDS = {
        "password", "token", "secret", "api_key", "jwt", 
        "access_token", "refresh_token", "authorization"
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out sensitive data from log records"""
        # Check message
        message_lower = record.getMessage().lower()
        for field in self.SENSITIVE_FIELDS:
            if field in message_lower:
                # Redact the sensitive data
                record.msg = record.msg.replace(
                    field, 
                    f"{field[:2]}***{field[-2:]}"
                )
        
        return True


# Apply sensitive data filter
logger.addFilter(SensitiveDataFilter())


# Utility functions for common logging patterns

def log_request(request_id: str, method: str, endpoint: str, user_id: str = None):
    """Log incoming HTTP request"""
    logger.info(
        f"{method} {endpoint}",
        extra={
            "request_id": request_id,
            "method": method,
            "endpoint": endpoint,
            "user_id": user_id,
            "event_type": "request_received"
        }
    )


def log_response(request_id: str, status_code: int, duration_ms: float):
    """Log outgoing HTTP response"""
    logger.info(
        f"Response {status_code}",
        extra={
            "request_id": request_id,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "event_type": "response_sent"
        }
    )


def log_db_query(query: str, params: Dict[str, Any] = None, duration_ms: float = None):
    """Log database query (only in DEBUG mode)"""
    if logger.level == logging.DEBUG:
        logger.debug(
            f"Database query",
            extra={
                "query": query[:200],  # Limit query length
                "params": params,
                "duration_ms": round(duration_ms, 2) if duration_ms else None,
                "event_type": "db_query"
            }
        )


def log_error(error: Exception, request_id: str = None, user_id: str = None, context: Dict[str, Any] = None):
    """Log error with full context"""
    logger.error(
        f"Error: {str(error)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "error_type": error.__class__.__name__,
            "context": context or {},
            "event_type": "error_occurred"
        }
    )

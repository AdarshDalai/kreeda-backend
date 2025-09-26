"""
Kreeda Backend Logging Utilities

Centralized logging configuration
"""

import logging
import sys
from typing import Any, Dict

from app.core.config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Configure handler
        handler = logging.StreamHandler(sys.stdout)
        
        # Set log level based on environment
        if settings.DEBUG:
            logger.setLevel(logging.DEBUG)
            handler.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            handler.setLevel(logging.INFO)
        
        # Configure formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Prevent duplicate logs
        logger.propagate = False
    
    return logger


def log_api_call(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str = None,
    **kwargs: Any
) -> None:
    """
    Log API call information
    
    Args:
        method: HTTP method
        path: Request path  
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user ID
        **kwargs: Additional context
    """
    logger = get_logger("api")
    
    context = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "user_id": user_id,
        **kwargs
    }
    
    # Choose log level based on status code
    if status_code >= 500:
        logger.error(f"API Error: {method} {path}", extra=context)
    elif status_code >= 400:
        logger.warning(f"API Warning: {method} {path}", extra=context)
    else:
        logger.info(f"API Success: {method} {path}", extra=context)
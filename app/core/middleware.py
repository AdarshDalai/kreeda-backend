"""
Input validation and security middleware for Kreeda Backend
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging
from typing import Dict, Any
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all API requests with timing information"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # Generate request ID for tracking
        request_id = f"{int(start_time * 1000000)}"
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url}",
            extra={"request_id": request_id, "method": request.method, "url": str(request.url)}
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {response.status_code} in {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_seconds": duration
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {str(e)} in {duration:.3f}s",
                extra={"request_id": request_id, "error": str(e), "duration_seconds": duration},
                exc_info=True
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting - use Redis in production"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.clients: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries for this client
        if client_ip in self.clients:
            self.clients[client_ip] = [
                timestamp for timestamp in self.clients[client_ip]
                if current_time - timestamp < 60  # Keep last minute
            ]
        else:
            self.clients[client_ip] = []
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls_per_minute:
            logger.warning(
                f"Rate limit exceeded for client {client_ip}",
                extra={"client_ip": client_ip, "calls_count": len(self.clients[client_ip])}
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down."
            )
        
        # Record this request
        self.clients[client_ip].append(current_time)
        
        return await call_next(request)


def validate_json_size(request_body: bytes, max_size_mb: int = 1) -> None:
    """Validate JSON request size"""
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if len(request_body) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Request body too large. Maximum size is {max_size_mb}MB"
        )


def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Basic input sanitization"""
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Remove potential XSS characters
            sanitized[key] = value.replace("<", "&lt;").replace(">", "&gt;").strip()
        elif isinstance(value, dict):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_input(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized

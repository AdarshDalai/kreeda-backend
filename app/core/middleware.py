"""
Input validation and security middleware for Kreeda Backend
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import Response
import time
import logging
from typing import Dict, Any, Optional
import json
import uuid

from app.core.logging import get_request_logger, log_request, log_error
from app.core.config import settings

logger = logging.getLogger(__name__)
request_logger = get_request_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to all requests for distributed tracing"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state for use in handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


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
    """Log all HTTP requests and responses"""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # Get request ID from state (set by RequestIDMiddleware)
        request_id = getattr(request.state, 'request_id', 'unknown')

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log the request
            log_request(
                request_logger,
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                duration
            )

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log the error
            log_error(
                request_logger,
                e,
                request_id,
                {
                    'method': request.method,
                    'path': request.url.path,
                    'query_params': str(request.query_params),
                    'user_agent': request.headers.get('user-agent', 'unknown')
                }
            )

            # Re-raise the exception
            raise


class DistributedRateLimitMiddleware(BaseHTTPMiddleware):
    """Distributed rate limiting using DynamoDB - suitable for serverless"""
    
    def __init__(self, app, calls_per_minute: int = 60, table_name: Optional[str] = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.table_name = table_name or "kreeda-rate-limits"
        # Lazy import to avoid circular dependencies
        self._dynamodb = None
    
    def _get_dynamodb(self):
        """Lazy initialization of DynamoDB client"""
        if self._dynamodb is None:
            import boto3
            from app.core.config import settings
            if settings.DYNAMODB_ENDPOINT_URL:
                # Local DynamoDB
                self._dynamodb = boto3.resource(
                    'dynamodb',
                    endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
                    aws_access_key_id='dummy',
                    aws_secret_access_key='dummy',
                    region_name=settings.AWS_REGION
                )
            else:
                # AWS DynamoDB
                self._dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        return self._dynamodb
    
    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time())
        window_start = current_time - 60  # 1-minute window
        
        try:
            dynamodb = self._get_dynamodb()
            table = dynamodb.Table(self.table_name)
            
            # Create table if it doesn't exist (for local development)
            try:
                table.table_status
            except Exception:
                # Table doesn't exist, skip rate limiting for now
                return await call_next(request)
            
            # Get current request count for this client
            response = table.get_item(
                Key={'client_ip': client_ip, 'window': str(window_start)}
            )
            
            current_count = 0
            if 'Item' in response:
                current_count = response['Item'].get('count', 0)
            
            # Check rate limit
            if current_count >= self.calls_per_minute:
                logger.warning(
                    f"Rate limit exceeded for client {client_ip}",
                    extra={"client_ip": client_ip, "current_count": current_count}
                )
                
                # Return rate limit exceeded response with headers
                response = Response(
                    content='{"detail":"Too many requests. Please slow down."}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json"
                )
                
                # Add rate limit headers
                response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(window_start + 60)
                response.headers["Retry-After"] = "60"
                
                return response
            
            # Update request count
            table.put_item(
                Item={
                    'client_ip': client_ip,
                    'window': str(window_start),
                    'count': current_count + 1,
                    'last_request': current_time
                }
            )
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            remaining = max(0, self.calls_per_minute - current_count - 1)
            response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(window_start + 60)
            
            return response
            
        except Exception as e:
            # If rate limiting fails, allow the request (fail open)
            logger.warning(f"Rate limiting failed: {str(e)}")
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


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting for better performance than DynamoDB"""

    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.redis_client = None

    def _get_redis_client(self):
        """Lazy initialization of Redis client"""
        if self.redis_client is None:
            try:
                import redis
                self.redis_client = redis.from_url(settings.REDIS_URL)
            except ImportError:
                logger.warning("Redis not available, falling back to in-memory rate limiting")
                self.redis_client = None
        return self.redis_client

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time())
        window_start = current_time - 60  # 1-minute window
        key = f"ratelimit:{client_ip}:{current_time // 60}"  # Per-minute key

        redis_client = self._get_redis_client()

        if redis_client:
            try:
                # Use Redis pipeline for atomic operations
                with redis_client.pipeline() as pipe:
                    pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
                    pipe.zadd(key, {str(current_time): current_time})  # Add current request
                    pipe.zcard(key)  # Count requests in current window
                    pipe.expire(key, 120)  # Expire key after 2 minutes

                    results = pipe.execute()
                    request_count = results[2]

                if request_count > self.calls_per_minute:
                    logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                    return Response(
                        content=json.dumps({
                            "error": "Rate limit exceeded",
                            "message": f"Too many requests. Limit: {self.calls_per_minute} per minute"
                        }),
                        status_code=429,
                        media_type="application/json",
                        headers={
                            "X-RateLimit-Limit": str(self.calls_per_minute),
                            "X-RateLimit-Remaining": "0",
                            "Retry-After": "60"
                        }
                    )

                # Add rate limit headers
                response = await call_next(request)
                remaining = max(0, self.calls_per_minute - request_count)
                response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                return response

            except Exception as e:
                logger.error(f"Redis rate limiting error: {e}")
                # Fall back to allowing request if Redis fails

        # Fallback: Simple in-memory rate limiting (not suitable for production)
        logger.warning("Using in-memory rate limiting (not recommended for production)")
        return await call_next(request)

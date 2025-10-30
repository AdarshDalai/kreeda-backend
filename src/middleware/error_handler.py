"""
Global Error Handler Middleware
Catches all uncaught exceptions and formats them as JSON responses

Features:
- Catches KreedaException and returns structured error response
- Logs all errors with full context
- Returns 500 for unexpected exceptions
- Includes request_id for error tracking
- Development mode shows stack traces
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uuid
import traceback

from src.core.exceptions import KreedaException
from src.core.logging import logger, log_error
from src.config.settings import settings


async def kreeda_exception_handler(request: Request, exc: KreedaException) -> JSONResponse:
    """
    Handle custom Kreeda exceptions
    
    Returns structured error response with:
    - code: Error code (machine-readable)
    - message: Error message (human-readable)
    - details: Additional error context
    - request_id: Unique ID for error tracking
    """
    request_id = str(uuid.uuid4())
    
    # Log the error with full context
    log_error(
        exc,
        request_id=request_id,
        context={
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
            "error_code": exc.error_code,
            "error_details": exc.details
        }
    )
    
    error_response = {
        **exc.to_dict(),
        "request_id": request_id
    }
    
    return JSONResponse(
        status_code=exc.http_status,
        content=error_response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI/Pydantic validation errors
    
    Returns 422 with detailed field errors
    """
    request_id = str(uuid.uuid4())
    
    # Extract field-level errors
    field_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        field_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "field_errors": field_errors,
            "error_count": len(field_errors)
        }
    )
    
    error_response = {
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "details": {
            "errors": field_errors
        },
        "request_id": request_id
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions (FastAPI HTTPException)
    
    Converts standard HTTPException to our error format
    """
    request_id = str(uuid.uuid4())
    
    logger.warning(
        f"HTTP {exc.status_code} on {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )
    
    # If detail is already a dict (from router exception handlers), use it directly
    if isinstance(exc.detail, dict):
        error_response = {
            **exc.detail,
            "request_id": request_id
        }
    else:
        # Otherwise create standard error response
        error_response = {
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail or "An error occurred",
            "details": {},
            "request_id": request_id
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions
    
    Returns 500 and logs full stack trace
    In production, hides sensitive error details
    """
    request_id = str(uuid.uuid4())
    
    # Log full exception with stack trace
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    )
    
    # In development, show detailed error
    if settings.app_env == "development":
        error_response = {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc().split("\n")
            },
            "request_id": request_id
        }
    else:
        # In production, hide implementation details
        error_response = {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please contact support with the request ID.",
            "details": {},
            "request_id": request_id
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app
    
    Order matters: Most specific → Least specific
    1. KreedaException (our custom exceptions)
    2. RequestValidationError (Pydantic validation)
    3. StarletteHTTPException (FastAPI HTTPException)
    4. Exception (catch-all)
    
    Usage:
        from src.middleware.error_handler import register_exception_handlers
        app = FastAPI()
        register_exception_handlers(app)
    """
    app.add_exception_handler(KreedaException, kreeda_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Registered global exception handlers")

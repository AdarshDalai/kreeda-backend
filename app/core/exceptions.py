from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class KreedaException(Exception):
    """Base exception for Kreeda application."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(KreedaException):
    """Authentication related errors."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)


class AuthorizationError(KreedaException):
    """Authorization related errors."""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)


class NotFoundError(KreedaException):
    """Resource not found errors."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)


class ValidationError(KreedaException):
    """Data validation errors."""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, 422)


class ConflictError(KreedaException):
    """Resource conflict errors."""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, 409)


def setup_exception_handlers(app: FastAPI):
    """Setup custom exception handlers for the application."""
    
    @app.exception_handler(KreedaException)
    async def kreeda_exception_handler(request: Request, exc: KreedaException):
        """Handle custom Kreeda exceptions."""
        logger.error(f"Kreeda exception: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.message,
                "type": exc.__class__.__name__
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        logger.error(f"HTTP exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.detail,
                "type": "HTTPException"
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "message": "Validation failed",
                "details": exc.errors(),
                "type": "ValidationError"
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions."""
        logger.error(f"Starlette exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.detail,
                "type": "StarletteHTTPException"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.exception("Unexpected exception occurred")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "Internal server error",
                "type": "InternalServerError"
            }
        )

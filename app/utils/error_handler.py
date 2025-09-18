"""
Error handling utilities for consistent API responses
"""
import logging
import uuid
from typing import Dict, Optional

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class APIError(HTTPException):
    """Custom API error class for structured error responses"""
    
    def __init__(
        self, 
        code: str, 
        message: str, 
        status_code: int = 400, 
        details: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ):
        self.code = code
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        
        # Log error with correlation ID for debugging
        logger.error(
            f"API Error [{self.correlation_id}]: {code} - {message}",
            extra={"correlation_id": self.correlation_id, "details": self.details}
        )
        
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": self.details,
                    "correlation_id": self.correlation_id
                }
            }
        )


# Common error classes for better organization
class TeamNotFoundError(APIError):
    def __init__(self, team_id: Optional[str] = None):
        super().__init__(
            "TEAM_NOT_FOUND", 
            "The specified team does not exist",
            status.HTTP_404_NOT_FOUND,
            {"team_id": team_id} if team_id else None
        )


class MatchNotFoundError(APIError):
    def __init__(self, match_id: Optional[str] = None):
        super().__init__(
            "MATCH_NOT_FOUND",
            "The specified match does not exist", 
            status.HTTP_404_NOT_FOUND,
            {"match_id": match_id} if match_id else None
        )


class PermissionDeniedError(APIError):
    def __init__(self, action: str = "perform this action"):
        super().__init__(
            "PERMISSION_DENIED",
            f"You don't have permission to {action}",
            status.HTTP_403_FORBIDDEN
        )


class AlreadyExistsError(APIError):
    def __init__(self, resource: str, identifier: Optional[str] = None):
        super().__init__(
            "ALREADY_EXISTS",
            f"{resource} already exists",
            status.HTTP_400_BAD_REQUEST,
            {"resource": resource, "identifier": identifier} if identifier else {"resource": resource}
        )


class ValidationError(APIError):
    def __init__(self, field: str, message: str):
        super().__init__(
            "VALIDATION_ERROR",
            f"Invalid {field}: {message}",
            status.HTTP_400_BAD_REQUEST,
            {"field": field}
        )


class InternalServerError(APIError):
    def __init__(self, operation: str = "operation"):
        super().__init__(
            "INTERNAL_ERROR", 
            f"An internal error occurred during {operation}",
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def handle_database_error(e: Exception, operation: str = "database operation") -> APIError:
    """Convert database exceptions to appropriate API errors"""
    logger.error(f"Database error during {operation}: {str(e)}")
    return InternalServerError(operation)
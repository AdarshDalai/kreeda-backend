"""
Custom Exception Classes for Kreeda Backend
Production-grade error handling with HTTP status codes
"""
from typing import Optional, Dict, Any


class KreedaException(Exception):
    """
    Base exception for all Kreeda errors
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (defaults to class name in UPPER_CASE)
        details: Additional error context (field names, values, etc.)
        http_status: HTTP status code to return
    """
    http_status = 500  # Default to internal server error
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__.replace("Error", "").upper()
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            "code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(KreedaException):
    """
    400 Bad Request - Invalid input data
    
    Used when request body/params fail validation
    Examples: Missing required fields, invalid enum values, format errors
    """
    http_status = 400


class UnauthorizedError(KreedaException):
    """
    401 Unauthorized - Missing or invalid authentication
    
    Used when JWT token is missing, expired, or invalid
    Examples: No auth header, expired token, invalid signature
    """
    http_status = 401


class ForbiddenError(KreedaException):
    """
    403 Forbidden - Insufficient permissions
    
    Used when authenticated user lacks permission for the action
    Examples: Not team owner, not match creator, not assigned scorer
    """
    http_status = 403


class NotFoundError(KreedaException):
    """
    404 Not Found - Resource doesn't exist
    
    Used when requested resource is not in database
    Examples: Profile ID not found, Match ID doesn't exist, User not found
    """
    http_status = 404


class ConflictError(KreedaException):
    """
    409 Conflict - Resource already exists or state conflict
    
    Used when operation conflicts with current state
    Examples: Duplicate sport profile, match already started, email already registered
    """
    http_status = 409


class UnprocessableEntityError(KreedaException):
    """
    422 Unprocessable Entity - Business logic violation
    
    Used when request is valid but violates business rules
    Examples: Can't score ball for completed match, can't add 12th player to team
    """
    http_status = 422


class InternalServerError(KreedaException):
    """
    500 Internal Server Error - Unexpected server error
    
    Used when something goes wrong server-side
    Examples: Database connection failed, unexpected exception, service unavailable
    """
    http_status = 500


# Specific domain exceptions (inherit from base types above)

class DuplicateSportProfileError(ConflictError):
    """User already has a profile for this sport"""
    def __init__(self, sport_type: str):
        super().__init__(
            message=f"User already has a {sport_type} profile",
            error_code="DUPLICATE_SPORT_PROFILE",
            details={"sport_type": sport_type}
        )


class SportProfileNotFoundError(NotFoundError):
    """Sport profile not found"""
    def __init__(self, profile_id: str):
        super().__init__(
            message=f"Sport profile not found",
            error_code="SPORT_PROFILE_NOT_FOUND",
            details={"profile_id": profile_id}
        )


class CricketProfileNotFoundError(NotFoundError):
    """Cricket player profile not found"""
    def __init__(self, profile_id: str):
        super().__init__(
            message=f"Cricket profile not found",
            error_code="CRICKET_PROFILE_NOT_FOUND",
            details={"profile_id": profile_id}
        )


class DuplicateCricketProfileError(ConflictError):
    """Sport profile already has a cricket profile"""
    def __init__(self, sport_profile_id: str):
        super().__init__(
            message=f"Sport profile already has a cricket profile",
            error_code="DUPLICATE_CRICKET_PROFILE",
            details={"sport_profile_id": sport_profile_id}
        )


class InvalidSportTypeError(ValidationError):
    """Sport type must be CRICKET for cricket profiles"""
    def __init__(self, actual_sport_type: str):
        super().__init__(
            message=f"Invalid sport type for cricket profile. Expected CRICKET, got {actual_sport_type}",
            error_code="INVALID_SPORT_TYPE",
            details={"expected": "CRICKET", "actual": actual_sport_type}
        )

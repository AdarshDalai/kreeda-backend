"""
Input validation and sanitization utilities
Security-focused validation for all user inputs
"""
import re
import html
from typing import Any, Dict, List, Union, Optional
from fastapi import HTTPException


class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    NAME_PATTERN = re.compile(r'^[a-zA-Z\s\'-]{1,100}$')
    TEAM_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\'-]{1,100}$')
    VENUE_PATTERN = re.compile(r'^[a-zA-Z0-9\s,\.\-\(\)]{1,200}$')
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """Sanitize text input by removing HTML and limiting length"""
        if not isinstance(text, str):
            raise HTTPException(status_code=400, detail="Input must be a string")
        
        # Basic HTML tag removal (simple approach without external dependencies)
        import re
        # Remove HTML tags
        sanitized = re.sub(r'<[^>]+>', '', text)
        # Escape special characters
        sanitized = html.escape(sanitized, quote=True)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email address"""
        if not email or not isinstance(email, str):
            raise HTTPException(status_code=400, detail="Email is required")
        
        email = email.strip().lower()
        
        if not InputValidator.EMAIL_PATTERN.match(email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        if len(email) > 254:  # RFC 5321 limit
            raise HTTPException(status_code=400, detail="Email too long")
        
        return email
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate username"""
        if not username or not isinstance(username, str):
            raise HTTPException(status_code=400, detail="Username is required")
        
        username = username.strip()
        
        if not InputValidator.USERNAME_PATTERN.match(username):
            raise HTTPException(status_code=400, detail="Username must be 3-30 characters, alphanumeric with underscores and hyphens only")
        
        return username
    
    @staticmethod
    def validate_name(name: str) -> str:
        """Validate and sanitize name"""
        if not name or not isinstance(name, str):
            raise HTTPException(status_code=400, detail="Name is required")
        
        name = InputValidator.sanitize_text(name, 100)
        
        if not InputValidator.NAME_PATTERN.match(name):
            raise HTTPException(status_code=400, detail="Name contains invalid characters")
        
        return name
    
    @staticmethod
    def validate_team_name(name: str) -> str:
        """Validate team name"""
        if not name or not isinstance(name, str):
            raise HTTPException(status_code=400, detail="Team name is required")
        
        name = InputValidator.sanitize_text(name, 100)
        
        if not InputValidator.TEAM_NAME_PATTERN.match(name):
            raise HTTPException(status_code=400, detail="Team name contains invalid characters")
        
        return name
    
    @staticmethod
    def validate_venue(venue: str) -> str:
        """Validate venue name"""
        if not venue or not isinstance(venue, str):
            raise HTTPException(status_code=400, detail="Venue is required")
        
        venue = InputValidator.sanitize_text(venue, 200)
        
        if not InputValidator.VENUE_PATTERN.match(venue):
            raise HTTPException(status_code=400, detail="Venue name contains invalid characters")
        
        return venue
    
    @staticmethod
    def validate_positive_integer(value: Any, field_name: str, max_value: Optional[int] = None) -> int:
        """Validate positive integer"""
        try:
            int_value = int(value)
            if int_value <= 0:
                raise ValueError()
            if max_value and int_value > max_value:
                raise HTTPException(status_code=400, detail=f"{field_name} cannot exceed {max_value}")
            return int_value
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"{field_name} must be a positive integer")
    
    @staticmethod
    def validate_runs(runs: Any) -> int:
        """Validate cricket runs (0-6)"""
        try:
            runs_int = int(runs)
            if runs_int < 0 or runs_int > 6:
                raise HTTPException(status_code=400, detail="Runs must be between 0 and 6")
            return runs_int
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Runs must be a valid integer")
    
    @staticmethod
    def validate_uuid(uuid_str: str, field_name: str = "ID") -> str:
        """Validate UUID format"""
        import uuid
        try:
            uuid.UUID(uuid_str)
            return uuid_str
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid {field_name} format")
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize all string values in a dictionary"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = InputValidator.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = InputValidator.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    InputValidator.sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized


# Global validator instance
validator = InputValidator()

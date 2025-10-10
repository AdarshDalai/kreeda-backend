import re
from typing import List, Tuple

class PasswordValidator:
    """Password strength validation utility"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check length
        if len(password) < PasswordValidator.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long")
        
        if len(password) > PasswordValidator.MAX_LENGTH:
            errors.append(f"Password must not exceed {PasswordValidator.MAX_LENGTH} characters")
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = ['password', '12345678', 'qwerty', 'abc123', 'password123']
        if password.lower() in weak_passwords:
            errors.append("Password is too common. Please choose a stronger password")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_password_strength(password: str) -> str:
        """
        Get password strength level
        
        Returns:
            'weak', 'medium', or 'strong'
        """
        score = 0
        
        # Length score
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        
        # Complexity score
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        if score <= 3:
            return "weak"
        elif score <= 5:
            return "medium"
        else:
            return "strong"

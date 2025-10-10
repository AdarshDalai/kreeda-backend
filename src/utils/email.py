from typing import Optional
from datetime import datetime, timedelta
from src.core.security import create_access_token
from src.utils.logger import logger

class EmailService:
    """Email service for sending verification and notification emails"""
    
    @staticmethod
    async def send_verification_email(email: str, verification_token: str):
        """Send email verification link"""
        # In production, use actual email service (SendGrid, AWS SES, etc.)
        verification_link = f"http://localhost:8000/auth/verify-email?token={verification_token}"
        
        logger.info(f"Sending verification email to {email}")
        logger.info(f"Verification link: {verification_link}")
        
        # TODO: Implement actual email sending
        print(f"""
        ===== EMAIL VERIFICATION =====
        To: {email}
        Subject: Verify your email address
        
        Please click the link below to verify your email:
        {verification_link}
        
        This link will expire in 24 hours.
        ==============================
        """)
        
        return {"message": "Verification email sent"}
    
    @staticmethod
    async def send_password_reset_email(email: str, reset_token: str):
        """Send password reset email"""
        reset_link = f"http://localhost:8000/auth/reset-password?token={reset_token}"
        
        logger.info(f"Sending password reset email to {email}")
        logger.info(f"Reset link: {reset_link}")
        
        # TODO: Implement actual email sending
        print(f"""
        ===== PASSWORD RESET =====
        To: {email}
        Subject: Reset your password
        
        Click the link below to reset your password:
        {reset_link}
        
        This link will expire in 1 hour.
        If you didn't request this, please ignore this email.
        ==========================
        """)
        
        return {"message": "Password reset email sent"}
    
    @staticmethod
    async def send_welcome_email(email: str, name: Optional[str] = None):
        """Send welcome email after successful registration"""
        display_name = name or "User"
        
        logger.info(f"Sending welcome email to {email}")
        
        # TODO: Implement actual email sending
        print(f"""
        ===== WELCOME EMAIL =====
        To: {email}
        Subject: Welcome to Kreeda!
        
        Hello {display_name},
        
        Welcome to Kreeda! We're excited to have you on board.
        
        Get started by completing your profile and exploring the app.
        
        Best regards,
        The Kreeda Team
        =========================
        """)
        
        return {"message": "Welcome email sent"}

    @staticmethod
    def generate_verification_token(user_id: str) -> str:
        """Generate email verification token"""
        return create_access_token(
            {"sub": user_id, "type": "email_verification"},
            expires_delta=timedelta(hours=24)
        )

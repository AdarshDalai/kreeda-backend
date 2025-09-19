"""
Notification system models for real-time user notifications.

This module provides comprehensive notification management including:
- Real-time notifications via WebSocket
- Email and push notification support
- Notification preferences and settings
- Notification history and read status
"""

import uuid
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.utils.database import Base


class NotificationType(Base):
    """
    Notification type definitions for categorizing notifications.
    
    This allows for flexible notification categorization and user preferences
    for different types of notifications (match updates, social interactions, etc.)
    """
    __tablename__ = "notification_types"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True)  # 'match_update', 'team_invitation', etc.
    display_name: Mapped[str] = mapped_column(String(100))  # User-friendly name
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(50))  # Icon identifier for UI
    color: Mapped[Optional[str]] = mapped_column(String(20))  # Color code for UI
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="notification_type")
    user_preferences: Mapped[List["NotificationPreference"]] = relationship("NotificationPreference", back_populates="notification_type")


class Notification(Base):
    """
    Individual notification records for users.
    
    Stores notification content, delivery status, and metadata for tracking
    user notifications across different channels (in-app, email, push).
    """
    __tablename__ = "notifications"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    notification_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notification_types.id"))
    
    # Content
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    action_url: Mapped[Optional[str]] = mapped_column(String(500))  # Deep link or URL for notification action
    
    # Related entities (optional references)
    related_match_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("cricket_matches.id"))
    related_team_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"))
    related_tournament_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tournaments.id"))
    related_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))  # For social notifications
    
    # Status and delivery
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Delivery channels
    sent_in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    sent_email: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_push: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Priority and scheduling
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # 'low', 'normal', 'high', 'urgent'
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # For scheduled notifications
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # When notification becomes irrelevant
    
    # Metadata for additional context
    notification_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # Additional context data
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    notification_type: Mapped["NotificationType"] = relationship("NotificationType", back_populates="notifications")
    

class NotificationPreference(Base):
    """
    User preferences for different types of notifications.
    
    Allows users to control which notifications they receive and through
    which channels (in-app, email, push notifications).
    """
    __tablename__ = "notification_preferences"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    notification_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notification_types.id"))
    
    # Channel preferences
    enabled_in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled_email: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled_push: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timing preferences
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5))  # "22:00" format
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5))  # "08:00" format
    timezone: Mapped[Optional[str]] = mapped_column(String(50))  # User timezone
    
    # Frequency control
    frequency: Mapped[str] = mapped_column(String(20), default="immediate")  # 'immediate', 'hourly', 'daily', 'weekly'
    last_sent: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    notification_type: Mapped["NotificationType"] = relationship("NotificationPreference", back_populates="user_preferences")


class NotificationTemplate(Base):
    """
    Templates for generating notifications with dynamic content.
    
    Allows for consistent notification formatting and easy internationalization.
    Templates support variable substitution for personalized notifications.
    """
    __tablename__ = "notification_templates"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notification_types.id"))
    
    # Template content
    name: Mapped[str] = mapped_column(String(100))  # Template identifier
    title_template: Mapped[str] = mapped_column(String(200))  # Title with variables: "Match Update: {match_name}"
    message_template: Mapped[str] = mapped_column(Text)  # Message with variables
    
    # Channel-specific templates
    email_subject_template: Mapped[Optional[str]] = mapped_column(String(200))
    email_body_template: Mapped[Optional[str]] = mapped_column(Text)
    push_title_template: Mapped[Optional[str]] = mapped_column(String(100))
    push_body_template: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Localization
    language: Mapped[str] = mapped_column(String(10), default="en")  # Language code
    
    # Template metadata
    variables: Mapped[Optional[dict]] = mapped_column(JSON)  # Expected variable schema
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NotificationQueue(Base):
    """
    Queue for processing notifications asynchronously.
    
    Handles scheduling, batching, and retry logic for notification delivery
    across different channels.
    """
    __tablename__ = "notification_queue"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notifications.id"))
    
    # Queue management
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending', 'processing', 'sent', 'failed'
    channel: Mapped[str] = mapped_column(String(20))  # 'in_app', 'email', 'push', 'websocket'
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1 (highest) to 10 (lowest)
    
    # Scheduling
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Retry logic
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    last_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_retry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Processing results
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    processing_logs: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserDeviceToken(Base):
    """
    Device tokens for push notifications.
    
    Manages user device registrations for push notifications across
    different platforms (iOS, Android, Web).
    """
    __tablename__ = "user_device_tokens"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Device information
    device_token: Mapped[str] = mapped_column(String(500), unique=True)  # FCM/APNS token
    platform: Mapped[str] = mapped_column(String(20))  # 'ios', 'android', 'web'
    device_id: Mapped[Optional[str]] = mapped_column(String(100))  # Unique device identifier
    device_name: Mapped[Optional[str]] = mapped_column(String(100))  # User-friendly device name
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # App information
    app_version: Mapped[Optional[str]] = mapped_column(String(20))
    os_version: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# Add indexes for performance
from sqlalchemy import Index

# Notification indexes
Index("idx_notifications_user_unread", Notification.user_id, Notification.is_read)
Index("idx_notifications_type_created", Notification.notification_type_id, Notification.created_at)
Index("idx_notifications_scheduled", Notification.scheduled_for)
Index("idx_notifications_expires", Notification.expires_at)

# Queue indexes
Index("idx_queue_status_priority", NotificationQueue.status, NotificationQueue.priority, NotificationQueue.scheduled_for)
Index("idx_queue_channel_status", NotificationQueue.channel, NotificationQueue.status)
Index("idx_queue_retry", NotificationQueue.next_retry, NotificationQueue.retry_count)

# Device token indexes
Index("idx_device_tokens_user", UserDeviceToken.user_id, UserDeviceToken.is_active)
Index("idx_device_tokens_platform", UserDeviceToken.platform, UserDeviceToken.is_active)
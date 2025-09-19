"""
Notification system Pydantic schemas for API requests and responses.

This module provides comprehensive data models for the notification system
including notification creation, user preferences, and real-time updates.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, Enum):
    """Available notification delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    WEBSOCKET = "websocket"


class NotificationStatus(str, Enum):
    """Notification processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"


class NotificationFrequency(str, Enum):
    """Notification frequency options."""
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class DevicePlatform(str, Enum):
    """Supported device platforms for push notifications."""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


# Base schemas
class NotificationTypeBase(BaseModel):
    """Base schema for notification types."""
    name: str = Field(..., max_length=50)
    display_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    is_active: bool = True


class NotificationTypeCreate(NotificationTypeBase):
    """Schema for creating notification types."""
    pass


class NotificationTypeResponse(NotificationTypeBase):
    """Schema for notification type responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# Notification schemas
class NotificationBase(BaseModel):
    """Base schema for notifications."""
    title: str = Field(..., max_length=200)
    message: str
    action_url: Optional[str] = Field(None, max_length=500)
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notification_metadata: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    """Schema for creating notifications."""
    user_id: uuid.UUID
    notification_type_id: uuid.UUID
    related_match_id: Optional[uuid.UUID] = None
    related_team_id: Optional[uuid.UUID] = None
    related_tournament_id: Optional[uuid.UUID] = None
    related_user_id: Optional[uuid.UUID] = None
    
    # Channel preferences for this specific notification
    send_in_app: bool = True
    send_email: bool = False
    send_push: bool = False


class NotificationUpdate(BaseModel):
    """Schema for updating notifications."""
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None


class NotificationResponse(NotificationBase):
    """Schema for notification responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type_id: uuid.UUID
    
    # Related entities
    related_match_id: Optional[uuid.UUID] = None
    related_team_id: Optional[uuid.UUID] = None
    related_tournament_id: Optional[uuid.UUID] = None
    related_user_id: Optional[uuid.UUID] = None
    
    # Status
    is_read: bool
    read_at: Optional[datetime] = None
    is_delivered: bool
    delivered_at: Optional[datetime] = None
    
    # Delivery channels
    sent_in_app: bool
    sent_email: bool
    sent_push: bool
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Related data (populated in service layer)
    notification_type: Optional[NotificationTypeResponse] = None


class NotificationSummary(BaseModel):
    """Summary schema for notification counts and status."""
    total_notifications: int
    unread_count: int
    unread_urgent: int
    unread_high: int
    last_notification_at: Optional[datetime] = None


# Notification preferences schemas
class NotificationPreferenceBase(BaseModel):
    """Base schema for notification preferences."""
    enabled_in_app: bool = True
    enabled_email: bool = True
    enabled_push: bool = True
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: Optional[str] = None
    frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating notification preferences."""
    user_id: uuid.UUID
    notification_type_id: uuid.UUID


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""
    enabled_in_app: Optional[bool] = None
    enabled_email: Optional[bool] = None
    enabled_push: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    timezone: Optional[str] = None
    frequency: Optional[NotificationFrequency] = None


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Schema for notification preference responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type_id: uuid.UUID
    last_sent: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    notification_type: Optional[NotificationTypeResponse] = None


# Device token schemas
class DeviceTokenBase(BaseModel):
    """Base schema for device tokens."""
    device_token: str = Field(..., max_length=500)
    platform: DevicePlatform
    device_id: Optional[str] = Field(None, max_length=100)
    device_name: Optional[str] = Field(None, max_length=100)
    app_version: Optional[str] = Field(None, max_length=20)
    os_version: Optional[str] = Field(None, max_length=20)


class DeviceTokenCreate(DeviceTokenBase):
    """Schema for registering device tokens."""
    user_id: uuid.UUID


class DeviceTokenUpdate(BaseModel):
    """Schema for updating device tokens."""
    device_name: Optional[str] = Field(None, max_length=100)
    app_version: Optional[str] = Field(None, max_length=20)
    os_version: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class DeviceTokenResponse(DeviceTokenBase):
    """Schema for device token responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# WebSocket message schemas
class WebSocketNotification(BaseModel):
    """Schema for real-time WebSocket notifications."""
    type: str = "notification"
    notification: NotificationResponse
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketConnectionInfo(BaseModel):
    """Schema for WebSocket connection information."""
    user_id: uuid.UUID
    connection_id: str
    connected_at: datetime = Field(default_factory=datetime.utcnow)


# Bulk operations schemas
class BulkNotificationCreate(BaseModel):
    """Schema for creating bulk notifications."""
    user_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=1000)
    notification_type_id: uuid.UUID
    title: str = Field(..., max_length=200)
    message: str
    action_url: Optional[str] = Field(None, max_length=500)
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notification_metadata: Optional[Dict[str, Any]] = None
    
    # Channel preferences
    send_in_app: bool = True
    send_email: bool = False
    send_push: bool = False


class BulkNotificationResponse(BaseModel):
    """Schema for bulk notification creation response."""
    notifications_created: int
    failed_users: List[uuid.UUID] = []
    batch_id: Optional[uuid.UUID] = None


class NotificationMarkAllReadRequest(BaseModel):
    """Schema for marking all notifications as read."""
    notification_type_id: Optional[uuid.UUID] = None  # Optional filter by type


# Query and filter schemas
class NotificationFilter(BaseModel):
    """Schema for filtering notifications."""
    notification_type_id: Optional[uuid.UUID] = None
    is_read: Optional[bool] = None
    priority: Optional[NotificationPriority] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    related_match_id: Optional[uuid.UUID] = None
    related_team_id: Optional[uuid.UUID] = None
    related_tournament_id: Optional[uuid.UUID] = None


class NotificationListRequest(BaseModel):
    """Schema for listing notifications with pagination."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    filter: Optional[NotificationFilter] = None
    order_by: str = Field("created_at", pattern=r"^(created_at|updated_at|priority)$")
    order_direction: str = Field("desc", pattern=r"^(asc|desc)$")


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list response."""
    notifications: List[NotificationResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


# Template schemas (for future expansion)
class NotificationTemplateBase(BaseModel):
    """Base schema for notification templates."""
    name: str = Field(..., max_length=100)
    title_template: str = Field(..., max_length=200)
    message_template: str
    language: str = Field("en", max_length=10)
    variables: Optional[Dict[str, Any]] = None


class NotificationTemplateCreate(NotificationTemplateBase):
    """Schema for creating notification templates."""
    notification_type_id: uuid.UUID
    email_subject_template: Optional[str] = Field(None, max_length=200)
    email_body_template: Optional[str] = None
    push_title_template: Optional[str] = Field(None, max_length=100)
    push_body_template: Optional[str] = Field(None, max_length=200)


class NotificationTemplateResponse(NotificationTemplateBase):
    """Schema for notification template responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    notification_type_id: uuid.UUID
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    push_title_template: Optional[str] = None
    push_body_template: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
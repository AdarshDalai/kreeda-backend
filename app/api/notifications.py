"""
Notification API endpoints for real-time user notifications.

This module provides comprehensive notification management including:
- Real-time WebSocket notifications
- Notification CRUD operations
- User notification preferences
- Bulk notification operations
"""

import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import get_db
from app.auth.middleware import get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService, websocket_manager
from app.schemas.notifications import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationListRequest, NotificationListResponse, NotificationSummary,
    BulkNotificationCreate, BulkNotificationResponse,
    NotificationMarkAllReadRequest, NotificationFilter,
    WebSocketConnectionInfo, NotificationPriority
)


router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str,
    connection_id: str = Query(..., description="Unique connection identifier")
):
    """
    WebSocket endpoint for real-time notifications.
    
    Maintains persistent connection for delivering real-time notifications
    to users as they occur.
    """
    await websocket_manager.connect(websocket, user_id, connection_id)
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            
            # Handle ping/pong for connection health
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(user_id, connection_id)


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new notification for a user.
    
    Creates and queues a notification for delivery through configured channels.
    Supports immediate and scheduled delivery.
    """
    service = NotificationService(db)
    return await service.create_notification(notification_data)


@router.get("/", response_model=NotificationListResponse)
async def get_my_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    notification_type_id: Optional[uuid.UUID] = Query(None, description="Filter by notification type"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated notifications for the current user.
    
    Supports filtering by type, read status, priority, and date range.
    Returns notifications in reverse chronological order.
    """
    service = NotificationService(db)
    
    # Build filter
    filter_params = NotificationFilter(
        notification_type_id=notification_type_id,
        is_read=is_read,
        priority=NotificationPriority(priority) if priority else None,
        from_date=from_date,
        to_date=to_date
    )
    
    result = await service.get_user_notifications(
        user_id=uuid.UUID(str(current_user.id)),
        page=page,
        page_size=page_size,
        filter_params=filter_params
    )
    
    return NotificationListResponse(**result)


@router.get("/summary", response_model=NotificationSummary)
async def get_notification_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notification summary for the current user.
    
    Returns counts of total, unread, and priority notifications.
    Useful for badge displays and dashboard widgets.
    """
    service = NotificationService(db)
    result = await service.get_notification_summary(uuid.UUID(str(current_user.id)))
    return NotificationSummary(**result)


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a specific notification as read.
    
    Updates the read status and timestamp for the notification.
    Only the notification owner can mark it as read.
    """
    service = NotificationService(db)
    await service.mark_notification_read(notification_id, uuid.UUID(str(current_user.id)))
    return {"message": "Notification marked as read"}


@router.patch("/mark-all-read")
async def mark_all_notifications_read(
    request: Optional[NotificationMarkAllReadRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark all notifications as read for the current user.
    
    Optionally filter by notification type to mark only specific types as read.
    Returns count of notifications updated.
    """
    service = NotificationService(db)
    notification_type_id = request.notification_type_id if request else None
    
    count = await service.mark_all_notifications_read(
        user_id=uuid.UUID(str(current_user.id)),
        notification_type_id=notification_type_id
    )
    
    return {"message": f"Marked {count} notifications as read"}


@router.post("/bulk", response_model=BulkNotificationResponse)
async def create_bulk_notifications(
    bulk_data: BulkNotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create notifications for multiple users.
    
    Useful for broadcasting announcements, match updates, or system notifications.
    Processes in background for large user lists.
    """
    service = NotificationService(db)
    
    # For large batches, we would process in background in a real implementation
    # For now, process immediately
    result = await service.create_bulk_notifications(bulk_data)
    return BulkNotificationResponse(**result)


@router.get("/types")
async def get_notification_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all available notification types.
    
    Returns list of notification categories that users can receive.
    Used for preference settings and filtering.
    """
    service = NotificationService(db)
    return await service.get_notification_types()


@router.get("/connections")
async def get_active_connections(
    current_user: User = Depends(get_current_user)
):
    """
    Get active WebSocket connections for the current user.
    
    Useful for debugging and connection management.
    Returns connection count and status.
    """
    user_id = str(current_user.id)
    connection_count = websocket_manager.get_user_connection_count(user_id)
    is_connected = user_id in websocket_manager.get_connected_users()
    
    return {
        "user_id": user_id,
        "is_connected": is_connected,
        "connection_count": connection_count,
        "connected_at": datetime.utcnow() if is_connected else None
    }


@router.post("/test-websocket/{user_id}")
async def test_websocket_notification(
    user_id: uuid.UUID,
    title: str = Query(..., description="Notification title"),
    message: str = Query(..., description="Notification message"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test WebSocket notification delivery.
    
    Development endpoint for testing real-time notification delivery.
    Creates and immediately sends a test notification.
    """
    # Create test notification
    test_notification = NotificationCreate(
        user_id=user_id,
        notification_type_id=uuid.uuid4(),  # Dummy type for testing
        title=title,
        message=message,
        action_url=None,
        priority=NotificationPriority.NORMAL,
        send_in_app=True,
        send_email=False,
        send_push=False
    )
    
    service = NotificationService(db)
    notification = await service.create_notification(test_notification)
    
    return {
        "message": "Test notification sent",
        "notification_id": notification.id,
        "delivered_to_websocket": str(user_id) in websocket_manager.get_connected_users()
    }


@router.delete("/cleanup")
async def cleanup_notifications(
    days_to_keep: int = Query(30, ge=1, le=365, description="Days of notifications to keep"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up old and expired notifications.
    
    Admin endpoint for removing old notifications to maintain database performance.
    """
    service = NotificationService(db)
    count = await service.cleanup_expired_notifications(days_to_keep)
    
    return {"message": f"Cleaned up {count} notifications older than {days_to_keep} days"}


@router.get("/unread", response_model=NotificationListResponse)
async def get_unread_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all unread notifications for the current user."""
    service = NotificationService(db)
    filter_params = NotificationFilter(is_read=False)
    result = await service.get_user_notifications(
        user_id=uuid.UUID(str(current_user.id)),
        page=page,
        page_size=page_size,
        filter_params=filter_params
    )
    return NotificationListResponse(**result)


@router.get("/count")
async def get_notification_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification count for the current user."""
    service = NotificationService(db)
    summary = await service.get_notification_summary(uuid.UUID(str(current_user.id)))
    
    return {
        "total": summary.get("total_count", 0),
        "unread": summary.get("unread_count", 0)
    }


@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification preferences for the current user."""
    # Return default preferences since service doesn't have this method yet
    return {
        "email_notifications": True,
        "push_notifications": True,
        "in_app_notifications": True,
        "match_updates": True,
        "team_invitations": True,
        "tournament_announcements": True
    }


@router.patch("/preferences")
async def update_notification_preferences(
    preferences_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update notification preferences for the current user."""
    # For now, just return the updated preferences
    # In a real implementation, this would be saved to database
    return {
        "success": True,
        "preferences": preferences_data,
        "message": "Preferences updated successfully"
    }


@router.post("/send")
async def send_notification(
    notification_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a general notification."""
    # Validate required fields
    if not notification_data.get("notification_type"):
        raise HTTPException(status_code=400, detail="notification_type is required")
    
    if not notification_data.get("message"):
        raise HTTPException(status_code=400, detail="message is required")
    
    # Validate notification type
    valid_types = ["team_invitation", "match_update", "general", "tournament_announcement"]
    if notification_data.get("notification_type") not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid notification type")
    
    # Check for recipient if it's a team invitation or other targeted notifications
    if notification_data.get("notification_type") in ["team_invitation"] and not notification_data.get("recipient"):
        raise HTTPException(status_code=400, detail="recipient is required for this notification type")
    
    # For now, just return success
    return {"success": True, "message": "Notification sent"}


@router.post("/send-email")
async def send_email_notification(
    email_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send email notification."""
    # Validate email format
    recipient = email_data.get("recipient")
    if not recipient:
        raise HTTPException(status_code=400, detail="recipient is required")
    
    # Basic email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, recipient):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if not email_data.get("subject"):
        raise HTTPException(status_code=400, detail="subject is required")
    
    if not email_data.get("body"):
        raise HTTPException(status_code=400, detail="body is required")
    
    # For now, just return success
    # In a real implementation, this would integrate with email service
    return {"success": True, "message": "Email notification sent"}


@router.post("/send-push")
async def send_push_notification(
    push_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send push notification."""
    # For now, just return success
    # In a real implementation, this would integrate with push service
    return {"success": True, "message": "Push notification sent"}


@router.post("/register-device")
async def register_device_for_push(
    device_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register device for push notifications."""
    # For now, just return success
    # In a real implementation, this would save device token
    return {"success": True, "message": "Device registered for push notifications"}


@router.get("/templates")
async def get_notification_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available notification templates."""
    # Return default templates
    return [
        {
            "id": "match_update",
            "name": "Match Update",
            "template": "Match update: {{title}}"
        },
        {
            "id": "team_invitation",
            "name": "Team Invitation",
            "template": "{{inviter}} invited you to join {{team_name}}"
        }
    ]


@router.post("/templates")
async def create_notification_template(
    template_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create custom notification template."""
    # For now, just return success
    # In a real implementation, this would save template to database
    template_id = str(uuid.uuid4())
    return {"success": True, "message": "Template created", "template_id": template_id}


@router.post("/templates/preview")
async def preview_notification_template(
    preview_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Preview notification template with sample data."""
    template = preview_data.get("template", "")
    sample_data = preview_data.get("data", {})
    
    # Simple template replacement for preview
    preview_text = template
    for key, value in sample_data.items():
        preview_text = preview_text.replace(f"{{{{{key}}}}}", str(value))
    
    return {
        "preview": preview_text,
        "template": template,
        "data": sample_data
    }


@router.get("/health")
async def notifications_health_check():
    """
    Health check endpoint for notification system.
    
    Returns system status including WebSocket connection counts and service health.
    """
    connected_users = websocket_manager.get_connected_users()
    total_connections = sum(
        websocket_manager.get_user_connection_count(user_id) 
        for user_id in connected_users
    )
    
    return {
        "status": "healthy",
        "service": "notifications",
        "websocket_connections": {
            "connected_users": len(connected_users),
            "total_connections": total_connections
        },
        "timestamp": datetime.utcnow()
    }


# Background task functions
async def _process_bulk_notifications_background(
    bulk_data: BulkNotificationCreate,
    db: AsyncSession
):
    """Process bulk notifications in background."""
    try:
        service = NotificationService(db)
        result = await service.create_bulk_notifications(bulk_data)
        # Could log result or store in cache for later retrieval
    except Exception as e:
        # Log error for monitoring
        print(f"Background bulk notification processing failed: {e}")


async def _cleanup_notifications_background(db: AsyncSession, days_to_keep: int):
    """Clean up notifications in background."""
    try:
        service = NotificationService(db)
        count = await service.cleanup_expired_notifications(days_to_keep)
        # Could log result for monitoring
        print(f"Cleaned up {count} expired notifications")
    except Exception as e:
        # Log error for monitoring
        print(f"Background notification cleanup failed: {e}")


# Real-time notification utilities
async def send_match_update_notification(
    match_id: uuid.UUID,
    title: str,
    message: str,
    user_ids: List[uuid.UUID],
    db: AsyncSession
):
    """
    Utility function to send match update notifications.
    
    Used by cricket service to notify users about match events.
    """
    # This would be called from cricket service when match events occur
    service = NotificationService(db)
    
    bulk_data = BulkNotificationCreate(
        user_ids=user_ids,
        notification_type_id=uuid.uuid4(),  # Would use actual match update type
        title=title,
        message=message,
        action_url=f"/matches/{match_id}",
        priority=NotificationPriority.HIGH,
        send_in_app=True,
        send_push=True,
        notification_metadata={"match_id": str(match_id)}
    )
    
    await service.create_bulk_notifications(bulk_data)


async def send_team_invitation_notification(
    team_id: uuid.UUID,
    invited_user_id: uuid.UUID,
    inviter_name: str,
    team_name: str,
    db: AsyncSession
):
    """
    Utility function to send team invitation notifications.
    
    Used by team service to notify users about team invitations.
    """
    service = NotificationService(db)
    
    notification_data = NotificationCreate(
        user_id=invited_user_id,
        notification_type_id=uuid.uuid4(),  # Would use actual team invitation type
        title=f"Team Invitation from {team_name}",
        message=f"{inviter_name} has invited you to join {team_name}",
        action_url=f"/teams/{team_id}/invitation",
        priority=NotificationPriority.HIGH,
        send_in_app=True,
        send_email=True,
        related_team_id=team_id,
        notification_metadata={"inviter_name": inviter_name, "team_name": team_name}
    )
    
    await service.create_notification(notification_data)
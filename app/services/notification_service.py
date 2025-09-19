"""
Notification service layer for managing real-time notifications.

This module provides comprehensive notification management including:
- Real-time WebSocket notifications
- Email and push notification delivery
- Notification preferences and scheduling
- Bulk notification operations
"""

import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from decimal import Decimal

from sqlalchemy import select, insert, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, WebSocket
import logging

from app.models.notifications import (
    Notification, NotificationType, NotificationPreference, 
    NotificationTemplate, NotificationQueue, UserDeviceToken
)
from app.schemas.notifications import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationPreferenceCreate, NotificationPreferenceUpdate,
    BulkNotificationCreate, NotificationFilter, WebSocketNotification
)

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time notifications.
    
    Handles connection lifecycle, message broadcasting, and user session management.
    """
    
    def __init__(self):
        # Active connections: {user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
            
        self.active_connections[user_id][connection_id] = websocket
        logger.info(f"WebSocket connected: user_id={user_id}, connection_id={connection_id}")
        
    async def disconnect(self, user_id: str, connection_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]
                logger.info(f"WebSocket disconnected: user_id={user_id}, connection_id={connection_id}")
                
            # Remove user if no active connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
    async def send_personal_message(self, message: str, user_id: str):
        """Send a message to all connections for a specific user."""
        if user_id in self.active_connections:
            disconnected_connections = []
            
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send message to {user_id}:{connection_id}: {e}")
                    disconnected_connections.append(connection_id)
                    
            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                await self.disconnect(user_id, connection_id)
                
    async def broadcast_to_users(self, message: str, user_ids: List[str]):
        """Broadcast a message to multiple users."""
        tasks = []
        for user_id in user_ids:
            if user_id in self.active_connections:
                tasks.append(self.send_personal_message(message, user_id))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    def get_connected_users(self) -> Set[str]:
        """Get set of currently connected user IDs."""
        return set(self.active_connections.keys())
        
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user."""
        return len(self.active_connections.get(user_id, {}))


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


class NotificationService:
    """
    Service layer for notification management and delivery.
    
    Handles notification creation, delivery, preferences, and real-time updates.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_notification(self, notification_data: NotificationCreate) -> NotificationResponse:
        """Create a new notification and queue for delivery."""
        try:
            # Validate notification type exists
            notification_type = await self.db.scalar(
                select(NotificationType).where(NotificationType.id == notification_data.notification_type_id)
            )
            if not notification_type:
                raise HTTPException(status_code=404, detail="Notification type not found")
                
            # Create notification record
            notification = Notification(
                user_id=notification_data.user_id,
                notification_type_id=notification_data.notification_type_id,
                title=notification_data.title,
                message=notification_data.message,
                action_url=notification_data.action_url,
                related_match_id=notification_data.related_match_id,
                related_team_id=notification_data.related_team_id,
                related_tournament_id=notification_data.related_tournament_id,
                related_user_id=notification_data.related_user_id,
                priority=notification_data.priority,
                scheduled_for=notification_data.scheduled_for,
                expires_at=notification_data.expires_at,
                sent_in_app=notification_data.send_in_app,
                sent_email=notification_data.send_email,
                sent_push=notification_data.send_push,
                notification_metadata=notification_data.notification_metadata
            )
            
            self.db.add(notification)
            await self.db.flush()
            
            # Queue for delivery if immediate
            if not notification_data.scheduled_for or notification_data.scheduled_for <= datetime.utcnow():
                await self._queue_notification_delivery(notification)
                
            await self.db.commit()
            
            # Convert to response model
            notification_response = NotificationResponse.model_validate(notification)
            notification_response.notification_type = notification_type
            
            logger.info(f"Created notification {notification.id} for user {notification_data.user_id}")
            return notification_response
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create notification: {e}")
            raise HTTPException(status_code=500, detail="Failed to create notification")
            
    async def get_user_notifications(
        self, 
        user_id: uuid.UUID, 
        page: int = 1, 
        page_size: int = 20,
        filter_params: Optional[NotificationFilter] = None
    ) -> Dict[str, Any]:
        """Get paginated notifications for a user with optional filtering."""
        try:
            # Build query
            query = select(Notification).where(Notification.user_id == user_id)
            
            # Apply filters
            if filter_params:
                if filter_params.notification_type_id:
                    query = query.where(Notification.notification_type_id == filter_params.notification_type_id)
                if filter_params.is_read is not None:
                    query = query.where(Notification.is_read == filter_params.is_read)
                if filter_params.priority:
                    query = query.where(Notification.priority == filter_params.priority)
                if filter_params.from_date:
                    query = query.where(Notification.created_at >= filter_params.from_date)
                if filter_params.to_date:
                    query = query.where(Notification.created_at <= filter_params.to_date)
                    
            # Add ordering
            query = query.order_by(Notification.created_at.desc())
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await self.db.scalar(count_query)
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # Execute query
            result = await self.db.execute(query)
            notifications = result.scalars().all()
            
            # Convert to response models
            notification_responses = []
            for notification in notifications:
                response = NotificationResponse.model_validate(notification)
                notification_responses.append(response)
                
            return {
                "notifications": notification_responses,
                "total_count": total_count or 0,
                "page": page,
                "page_size": page_size,
                "total_pages": ((total_count or 0) + page_size - 1) // page_size,
                "has_next": page * page_size < (total_count or 0),
                "has_previous": page > 1
            }
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve notifications")
            
    async def mark_notification_read(self, notification_id: uuid.UUID, user_id: uuid.UUID):
        """Mark a specific notification as read."""
        try:
            # Update notification
            result = await self.db.execute(
                update(Notification)
                .where(and_(Notification.id == notification_id, Notification.user_id == user_id))
                .values(is_read=True, read_at=datetime.utcnow())
            )
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Notification not found")
                
            await self.db.commit()
            logger.info(f"Marked notification {notification_id} as read for user {user_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to mark notification as read: {e}")
            raise HTTPException(status_code=500, detail="Failed to update notification")
            
    async def mark_all_notifications_read(self, user_id: uuid.UUID, notification_type_id: Optional[uuid.UUID] = None):
        """Mark all notifications as read for a user, optionally filtered by type."""
        try:
            query = update(Notification).where(
                and_(Notification.user_id == user_id, Notification.is_read == False)
            )
            
            if notification_type_id:
                query = query.where(Notification.notification_type_id == notification_type_id)
                
            query = query.values(is_read=True, read_at=datetime.utcnow())
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            logger.info(f"Marked {result.rowcount} notifications as read for user {user_id}")
            return result.rowcount
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to mark all notifications as read: {e}")
            raise HTTPException(status_code=500, detail="Failed to update notifications")
            
    async def get_notification_summary(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get notification summary for a user."""
        try:
            # Get counts using SQL for efficiency
            result = await self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_notifications,
                    COUNT(*) FILTER (WHERE is_read = false) as unread_count,
                    COUNT(*) FILTER (WHERE is_read = false AND priority = 'urgent') as unread_urgent,
                    COUNT(*) FILTER (WHERE is_read = false AND priority = 'high') as unread_high,
                    MAX(created_at) as last_notification_at
                FROM notifications 
                WHERE user_id = :user_id
            """), {"user_id": str(user_id)})
            
            row = result.fetchone()
            
            return {
                "total_notifications": row[0] if row else 0,
                "unread_count": row[1] if row else 0,
                "unread_urgent": row[2] if row else 0,
                "unread_high": row[3] if row else 0,
                "last_notification_at": row[4] if row else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to get notification summary")
            
    async def create_bulk_notifications(self, bulk_data: BulkNotificationCreate) -> Dict[str, Any]:
        """Create notifications for multiple users."""
        try:
            notifications_created = 0
            failed_users = []
            
            # Create notifications in batches for performance
            batch_size = 100
            for i in range(0, len(bulk_data.user_ids), batch_size):
                batch_user_ids = bulk_data.user_ids[i:i + batch_size]
                
                notification_records = []
                for user_id in batch_user_ids:
                    try:
                        notification = Notification(
                            user_id=user_id,
                            notification_type_id=bulk_data.notification_type_id,
                            title=bulk_data.title,
                            message=bulk_data.message,
                            action_url=bulk_data.action_url,
                            priority=bulk_data.priority,
                            scheduled_for=bulk_data.scheduled_for,
                            expires_at=bulk_data.expires_at,
                            sent_in_app=bulk_data.send_in_app,
                            sent_email=bulk_data.send_email,
                            sent_push=bulk_data.send_push,
                            notification_metadata=bulk_data.notification_metadata
                        )
                        notification_records.append(notification)
                        
                    except Exception as e:
                        logger.warning(f"Failed to create notification for user {user_id}: {e}")
                        failed_users.append(user_id)
                        
                # Bulk insert
                if notification_records:
                    self.db.add_all(notification_records)
                    await self.db.flush()
                    notifications_created += len(notification_records)
                    
                    # Queue for delivery if immediate
                    if not bulk_data.scheduled_for or bulk_data.scheduled_for <= datetime.utcnow():
                        for notification in notification_records:
                            await self._queue_notification_delivery(notification)
                            
            await self.db.commit()
            
            logger.info(f"Created {notifications_created} bulk notifications, {len(failed_users)} failed")
            
            return {
                "notifications_created": notifications_created,
                "failed_users": failed_users,
                "batch_id": uuid.uuid4()  # For tracking purposes
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create bulk notifications: {e}")
            raise HTTPException(status_code=500, detail="Failed to create bulk notifications")
            
    async def _queue_notification_delivery(self, notification: Notification):
        """Queue notification for delivery through appropriate channels."""
        try:
            # Queue for in-app delivery (WebSocket)
            if notification.sent_in_app:
                await self._deliver_websocket_notification(notification)
                
            # Queue for email delivery (would integrate with email service)
            if notification.sent_email:
                # TODO: Integrate with email service
                logger.info(f"Queuing email notification {notification.id}")
                
            # Queue for push notification delivery (would integrate with FCM/APNS)
            if notification.sent_push:
                # TODO: Integrate with push notification service
                logger.info(f"Queuing push notification {notification.id}")
                
        except Exception as e:
            logger.error(f"Failed to queue notification delivery: {e}")
            
    async def _deliver_websocket_notification(self, notification: Notification):
        """Deliver notification via WebSocket to connected users."""
        try:
            user_id = str(notification.user_id)
            
            # Check if user is connected
            if user_id in websocket_manager.active_connections:
                # Create WebSocket message
                ws_notification = WebSocketNotification(
                    notification=NotificationResponse.model_validate(notification)
                )
                
                # Send to all user connections
                await websocket_manager.send_personal_message(
                    ws_notification.model_dump_json(),
                    user_id
                )
                
                # Mark as delivered
                await self.db.execute(
                    update(Notification)
                    .where(Notification.id == notification.id)
                    .values(is_delivered=True, delivered_at=datetime.utcnow())
                )
                
                logger.info(f"Delivered WebSocket notification {notification.id} to user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to deliver WebSocket notification: {e}")
            
    async def get_notification_types(self) -> List[Dict[str, Any]]:
        """Get all available notification types."""
        try:
            result = await self.db.execute(
                select(NotificationType).where(NotificationType.is_active == True)
            )
            types = result.scalars().all()
            
            return [
                {
                    "id": str(type.id),
                    "name": type.name,
                    "display_name": type.display_name,
                    "description": type.description,
                    "icon": type.icon,
                    "color": type.color
                }
                for type in types
            ]
            
        except Exception as e:
            logger.error(f"Failed to get notification types: {e}")
            raise HTTPException(status_code=500, detail="Failed to get notification types")
            
    async def cleanup_expired_notifications(self, days_to_keep: int = 30):
        """Clean up old and expired notifications."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete expired notifications
            result = await self.db.execute(
                delete(Notification).where(
                    or_(
                        Notification.expires_at < datetime.utcnow(),
                        and_(
                            Notification.created_at < cutoff_date,
                            Notification.is_read == True
                        )
                    )
                )
            )
            
            await self.db.commit()
            logger.info(f"Cleaned up {result.rowcount} expired notifications")
            
            return result.rowcount
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to cleanup notifications: {e}")
            raise
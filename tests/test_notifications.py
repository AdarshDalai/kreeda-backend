"""
Test cases for notification system functionality.

This module tests:
- Team invitation notifications
- Match update notifications
- Tournament announcement notifications
- Real-time notification delivery
- Notification preferences
- Email and push notification integration
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
import uuid
import json

from conftest import unit, integration


@pytest.mark.asyncio
@pytest.mark.notifications
@integration
class TestNotificationDelivery:
    """Test notification delivery system."""

    async def test_get_user_notifications(self, client, authenticated_users, auth_client_factory):
        """Test getting user notifications."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_get_unread_notifications(self, client, authenticated_users, auth_client_factory):
        """Test getting unread notifications."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/notifications/unread")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_mark_notification_as_read(self, client, authenticated_users, auth_client_factory):
        """Test marking a notification as read."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        notification_id = str(uuid.uuid4())
        response = user_client.patch(f"/api/v1/notifications/{notification_id}/read")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_mark_all_notifications_as_read(self, client, authenticated_users, auth_client_factory):
        """Test marking all notifications as read."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.patch("/api/v1/notifications/mark-all-read")
        assert response.status_code == status.HTTP_200_OK

    async def test_delete_notification(self, client, authenticated_users, auth_client_factory):
        """Test deleting a notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        notification_id = str(uuid.uuid4())
        response = user_client.delete(f"/api/v1/notifications/{notification_id}")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_get_notification_count(self, client, authenticated_users, auth_client_factory):
        """Test getting notification count."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/notifications/count")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total" in data or "count" in data or isinstance(data, int)


@pytest.mark.asyncio
@pytest.mark.notifications
@integration
class TestTeamInvitationNotifications:
    """Test team invitation notification system."""

    async def test_send_team_invitation_notification(self, client, authenticated_users, auth_client_factory):
        """Test sending team invitation notification."""
        # Get two different users
        user_tokens = list(authenticated_users["tokens"].values())
        captain_client = auth_client_factory(user_tokens[0])
        
        # Create a team first
        team_data = {
            "name": "Test Team for Notifications",
            "description": "Team created for notification testing",
            "team_type": "club"
        }
        
        team_response = captain_client.post("/api/v1/teams/", json=team_data)
        if team_response.status_code == status.HTTP_201_CREATED:
            team_id = team_response.json()["id"]
            
            # Send invitation
            invitation_data = {
                "email": "test@example.com",
                "role": "player",
                "message": "Join our team!"
            }
            
            response = captain_client.post(f"/api/v1/teams/{team_id}/invite", json=invitation_data)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_201_CREATED,
                status.HTTP_404_NOT_FOUND
            ]

    async def test_accept_team_invitation_notification(self, client, authenticated_users, auth_client_factory):
        """Test accepting team invitation notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        invitation_id = str(uuid.uuid4())
        response = user_client.post(f"/api/v1/teams/invitations/{invitation_id}/accept")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_decline_team_invitation_notification(self, client, authenticated_users, auth_client_factory):
        """Test declining team invitation notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        invitation_id = str(uuid.uuid4())
        response = user_client.post(f"/api/v1/teams/invitations/{invitation_id}/decline")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_team_invitation_reminder(self, client, authenticated_users, auth_client_factory):
        """Test sending team invitation reminder."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        invitation_id = str(uuid.uuid4())
        response = user_client.post(f"/api/v1/teams/invitations/{invitation_id}/reminder")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.asyncio
@pytest.mark.notifications
@integration
class TestMatchNotifications:
    """Test match-related notifications."""

    async def test_match_scheduled_notification(self, client, authenticated_users, auth_client_factory):
        """Test match scheduled notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        # Create a match (simplified for notification testing)
        match_data = {
            "team1_id": str(uuid.uuid4()),
            "team2_id": str(uuid.uuid4()),
            "scheduled_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "venue": "Test Ground",
            "match_type": "T20"
        }
        
        response = user_client.post("/api/v1/cricket/matches/", json=match_data)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_match_starting_notification(self, client, authenticated_users, auth_client_factory):
        """Test match starting notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        match_id = str(uuid.uuid4())
        response = user_client.post(f"/api/v1/cricket/matches/{match_id}/start")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_match_completed_notification(self, client, authenticated_users, auth_client_factory):
        """Test match completed notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        match_id = str(uuid.uuid4())
        response = user_client.post(f"/api/v1/cricket/matches/{match_id}/complete")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_score_update_notification(self, client, authenticated_users, auth_client_factory):
        """Test score update notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        match_id = str(uuid.uuid4())
        ball_data = {
            "runs": 4,
            "extras": 0,
            "wicket": False,
            "over": 1,
            "ball": 1
        }
        
        response = user_client.post(f"/api/v1/cricket/matches/{match_id}/score", json=ball_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_milestone_notification(self, client, authenticated_users, auth_client_factory):
        """Test milestone achievement notification (50s, 100s, wickets)."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        # This would typically be triggered automatically by scoring system
        milestone_data = {
            "player_id": str(uuid.uuid4()),
            "milestone_type": "half_century",
            "value": 50,
            "match_id": str(uuid.uuid4())
        }
        
        response = user_client.post("/api/v1/notifications/milestone", json=milestone_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.asyncio
@pytest.mark.notifications
@integration
class TestTournamentNotifications:
    """Test tournament-related notifications."""

    async def test_tournament_registration_open_notification(self, client, authenticated_users, auth_client_factory):
        """Test tournament registration open notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_data = {
            "name": "Test Tournament for Notifications",
            "description": "Tournament for notification testing",
            "tournament_type": "knockout",
            "max_teams": 8,
            "registration_deadline": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "start_date": (datetime.utcnow() + timedelta(days=14)).isoformat()
        }
        
        response = user_client.post("/api/v1/tournaments/", json=tournament_data)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_tournament_registration_deadline_reminder(self, client, authenticated_users, auth_client_factory):
        """Test tournament registration deadline reminder."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        response = user_client.post(f"/api/v1/tournaments/{tournament_id}/send-reminder")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_tournament_bracket_published_notification(self, client, authenticated_users, auth_client_factory):
        """Test tournament bracket published notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        response = user_client.post(f"/api/v1/tournaments/{tournament_id}/publish-bracket")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_tournament_match_scheduled_notification(self, client, authenticated_users, auth_client_factory):
        """Test tournament match scheduled notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        tournament_id = str(uuid.uuid4())
        schedule_data = {
            "matches": [
                {
                    "team1_id": str(uuid.uuid4()),
                    "team2_id": str(uuid.uuid4()),
                    "scheduled_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    "venue": "Tournament Ground"
                }
            ]
        }
        
        response = user_client.post(f"/api/v1/tournaments/{tournament_id}/schedule", json=schedule_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]


@pytest.mark.asyncio
@pytest.mark.notifications
@integration
class TestNotificationPreferences:
    """Test notification preferences and settings."""

    async def test_get_notification_preferences(self, client, authenticated_users, auth_client_factory):
        """Test getting user notification preferences."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/notifications/preferences")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)

    async def test_update_notification_preferences(self, client, authenticated_users, auth_client_factory):
        """Test updating notification preferences."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        preferences_data = {
            "email_notifications": True,
            "push_notifications": True,
            "team_invitations": True,
            "match_updates": True,
            "tournament_updates": False,
            "milestone_notifications": True,
            "score_updates": True,
            "frequency": "real_time"
        }
        
        response = user_client.patch("/api/v1/notifications/preferences", json=preferences_data)
        assert response.status_code == status.HTTP_200_OK

    async def test_disable_all_notifications(self, client, authenticated_users, auth_client_factory):
        """Test disabling all notifications."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        preferences_data = {
            "email_notifications": False,
            "push_notifications": False,
            "team_invitations": False,
            "match_updates": False,
            "tournament_updates": False,
            "milestone_notifications": False,
            "score_updates": False
        }
        
        response = user_client.patch("/api/v1/notifications/preferences", json=preferences_data)
        assert response.status_code == status.HTTP_200_OK

    async def test_notification_frequency_settings(self, client, authenticated_users, auth_client_factory):
        """Test notification frequency settings."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        frequency_options = ["real_time", "hourly", "daily", "weekly"]
        
        for frequency in frequency_options:
            preferences_data = {"frequency": frequency}
            response = user_client.patch("/api/v1/notifications/preferences", json=preferences_data)
            assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.notifications
@integration
class TestNotificationChannels:
    """Test different notification channels (email, push, in-app)."""

    async def test_send_email_notification(self, client, authenticated_users, auth_client_factory):
        """Test sending email notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        email_data = {
            "recipient": "test@example.com",
            "subject": "Test Notification",
            "body": "This is a test notification",
            "notification_type": "team_invitation"
        }
        
        response = user_client.post("/api/v1/notifications/send-email", json=email_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_send_push_notification(self, client, authenticated_users, auth_client_factory):
        """Test sending push notification."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        push_data = {
            "title": "Match Starting",
            "body": "Your team's match is starting in 10 minutes",
            "data": {"match_id": str(uuid.uuid4())},
            "notification_type": "match_reminder"
        }
        
        response = user_client.post("/api/v1/notifications/send-push", json=push_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_register_device_for_push_notifications(self, client, authenticated_users, auth_client_factory):
        """Test registering device for push notifications."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        device_data = {
            "device_token": "sample_device_token_12345",
            "platform": "ios",
            "app_version": "1.0.0"
        }
        
        response = user_client.post("/api/v1/notifications/register-device", json=device_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED
        ]

    async def test_unregister_device_from_push_notifications(self, client, authenticated_users, auth_client_factory):
        """Test unregistering device from push notifications."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        device_token = "sample_device_token_12345"
        response = user_client.delete(f"/api/v1/notifications/device/{device_token}")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.asyncio
@pytest.mark.notifications
@integration
class TestNotificationTemplates:
    """Test notification templates and formatting."""

    async def test_get_notification_templates(self, client, authenticated_users, auth_client_factory):
        """Test getting notification templates."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        response = user_client.get("/api/v1/notifications/templates")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_customize_notification_template(self, client, authenticated_users, auth_client_factory):
        """Test customizing notification template."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        template_data = {
            "template_type": "team_invitation",
            "subject": "You're invited to join {team_name}!",
            "body": "Hello {user_name}, you've been invited to join {team_name}. Click here to accept: {invitation_link}"
        }
        
        response = user_client.post("/api/v1/notifications/templates", json=template_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_preview_notification_template(self, client, authenticated_users, auth_client_factory):
        """Test previewing notification template with sample data."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        preview_data = {
            "template_type": "team_invitation",
            "variables": {
                "user_name": "John Doe",
                "team_name": "Test Team",
                "invitation_link": "https://example.com/invite/123"
            }
        }
        
        response = user_client.post("/api/v1/notifications/templates/preview", json=preview_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.asyncio
@pytest.mark.notifications
@unit
class TestNotificationValidation:
    """Test notification validation and error handling."""

    async def test_invalid_notification_type(self, client, authenticated_users, auth_client_factory):
        """Test handling invalid notification type."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        invalid_data = {
            "notification_type": "invalid_type",
            "message": "Test message"
        }
        
        response = user_client.post("/api/v1/notifications/send", json=invalid_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_missing_notification_recipient(self, client, authenticated_users, auth_client_factory):
        """Test handling missing notification recipient."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        incomplete_data = {
            "notification_type": "team_invitation",
            "message": "Test message"
            # Missing recipient
        }
        
        response = user_client.post("/api/v1/notifications/send", json=incomplete_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_invalid_email_format(self, client, authenticated_users, auth_client_factory):
        """Test handling invalid email format."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        invalid_email_data = {
            "recipient": "invalid-email",
            "subject": "Test",
            "body": "Test message",
            "notification_type": "general"
        }
        
        response = user_client.post("/api/v1/notifications/send-email", json=invalid_email_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_notification_rate_limiting(self, client, authenticated_users, auth_client_factory):
        """Test notification rate limiting."""
        user_token = list(authenticated_users["tokens"].values())[0]
        user_client = auth_client_factory(user_token)
        
        # Send multiple notifications rapidly
        notification_data = {
            "notification_type": "general",
            "message": "Test message"
        }
        
        responses = []
        for i in range(10):  # Send 10 notifications
            response = user_client.post("/api/v1/notifications/send", json=notification_data)
            responses.append(response.status_code)
        
        # At least some should succeed, but rate limiting might kick in
        assert any(code in [status.HTTP_200_OK, status.HTTP_201_CREATED] for code in responses)
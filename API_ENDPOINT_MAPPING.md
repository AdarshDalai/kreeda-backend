# KREEDA API ENDPOINT MAPPING

## Complete Endpoint Coverage for Postman Collections

Generated on: $(date)

### Authentication Endpoints
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me
- PATCH /api/v1/auth/me
- POST /api/v1/auth/reset-password
- POST /api/v1/auth/verify-otp
- POST /api/v1/auth/oauth/{provider}

### Team Management Endpoints
- GET /api/v1/teams/
- POST /api/v1/teams/
- GET /api/v1/teams/{team_id}
- PUT /api/v1/teams/{team_id}
- DELETE /api/v1/teams/{team_id}
- GET /api/v1/teams/{team_id}/members
- POST /api/v1/teams/{team_id}/invite
- GET /api/v1/teams/{team_id}/invitations
- POST /api/v1/teams/join/{invitation_token}
- GET /api/v1/teams/discover
- POST /api/v1/teams/{team_id}/join-request

### Match Management Endpoints
- GET /api/v1/matches/
- POST /api/v1/matches/
- GET /api/v1/matches/{match_id}
- PUT /api/v1/matches/{match_id}
- DELETE /api/v1/matches/{match_id}
- POST /api/v1/matches/{match_id}/balls
- GET /api/v1/matches/{match_id}/scorecard
- POST /api/v1/matches/{match_id}/toss
- POST /api/v1/matches/{match_id}/playing-xi
- GET /api/v1/matches/{match_id}/playing-xi/{team_id}

### Tournament Endpoints
- GET /api/v1/tournaments/
- POST /api/v1/tournaments/
- GET /api/v1/tournaments/{tournament_id}
- PUT /api/v1/tournaments/{tournament_id}
- DELETE /api/v1/tournaments/{tournament_id}
- POST /api/v1/tournaments/{tournament_id}/register
- GET /api/v1/tournaments/{tournament_id}/standings
- GET /api/v1/tournaments/{tournament_id}/teams

### Statistics Endpoints
- GET /api/v1/statistics/career/{user_id}
- POST /api/v1/statistics/career/{user_id}/update
- GET /api/v1/statistics/players/performance
- GET /api/v1/statistics/leaderboard/{category}
- GET /api/v1/statistics/matches/{user_id}
- GET /api/v1/statistics/teams/rankings
- GET /api/v1/statistics/team/{team_id}/season
- GET /api/v1/statistics/tournament/{tournament_id}/leaderboard

### Notification Endpoints
- GET /api/v1/notifications/
- POST /api/v1/notifications/
- GET /api/v1/notifications/summary
- PATCH /api/v1/notifications/{notification_id}/read
- PATCH /api/v1/notifications/mark-all-read
- POST /api/v1/notifications/bulk
- GET /api/v1/notifications/types
- GET /api/v1/notifications/unread

### User Profile Endpoints
- GET /api/v1/user/
- PUT /api/v1/user/
- DELETE /api/v1/user/
- POST /api/v1/user/upload-avatar
- GET /api/v1/user/privacy
- PUT /api/v1/user/privacy
- PUT /api/v1/user/notifications
- PUT /api/v1/user/change-password
- GET /api/v1/user/dashboard
- GET /api/v1/user/activity

### User Management Endpoints
- GET /api/v1/users/
- GET /api/v1/users/count
- GET /api/v1/users/search
- GET /api/v1/users/{user_id}
- PATCH /api/v1/users/{user_id}
- DELETE /api/v1/users/{user_id}

### Health Check Endpoints
- GET /health
- GET /api/v1/auth/health
- GET /api/v1/teams/health
- GET /api/v1/matches/health
- GET /api/v1/stats/health
- GET /api/v1/statistics/health
- GET /api/v1/notifications/health


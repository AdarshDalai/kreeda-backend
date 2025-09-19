# Import all models to ensure they are registered with SQLAlchemy
from app.models.cricket import CricketBall, CricketMatch, MatchPlayerStats
from app.models.statistics import (
    PlayerCareerStats,
    PlayerMatchPerformance,
    TeamSeasonStats,
    PlayerPerformanceTrend,
    Leaderboard,
    PlayerComparison,
)
from app.models.tournament import Tournament, TournamentMatch, TournamentStanding, TournamentTeam
from app.models.user import Team, TeamMember, User, TeamInvitation, MatchPlayingXI
from app.models.notifications import (
    Notification,
    NotificationType,
    NotificationPreference,
    NotificationTemplate,
    NotificationQueue,
    UserDeviceToken,
)

__all__ = [
    "User",
    "Team",
    "TeamMember",
    "TeamInvitation",
    "CricketMatch",
    "CricketBall",
    "MatchPlayerStats",
    "MatchPlayingXI",
    "Tournament",
    "TournamentTeam",
    "TournamentMatch", 
    "TournamentStanding",
    "PlayerCareerStats",
    "PlayerMatchPerformance",
    "TeamSeasonStats",
    "PlayerPerformanceTrend",
    "Leaderboard",
    "PlayerComparison",
    "Notification",
    "NotificationType",
    "NotificationPreference",
    "NotificationTemplate",
    "NotificationQueue",
    "UserDeviceToken",
]

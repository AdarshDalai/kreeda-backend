"""
Enums for Kreeda Backend
All ENUM types used across the application
"""
from enum import Enum as PyEnum


# ============================================================================
# USER & AUTHENTICATION ENUMS
# ============================================================================

class UserRole(str, PyEnum):
    """User role in the application"""
    USER = "user"
    ADMIN = "admin"
    VERIFIED_PLAYER = "verified_player"


# ============================================================================
# SPORT PROFILE ENUMS
# ============================================================================

class SportType(str, PyEnum):
    """Types of sports supported"""
    CRICKET = "cricket"
    FOOTBALL = "football"
    HOCKEY = "hockey"
    BASKETBALL = "basketball"


class ProfileVisibility(str, PyEnum):
    """Profile visibility settings"""
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


# ============================================================================
# CRICKET PLAYER ENUMS
# ============================================================================

class PlayingRole(str, PyEnum):
    """Cricket playing role"""
    BATSMAN = "batsman"
    BOWLER = "bowler"
    ALL_ROUNDER = "all_rounder"
    WICKET_KEEPER = "wicket_keeper"


class BattingStyle(str, PyEnum):
    """Batting hand preference"""
    RIGHT_HAND = "right_hand"
    LEFT_HAND = "left_hand"


class BowlingStyle(str, PyEnum):
    """Bowling style categories"""
    RIGHT_ARM_FAST = "right_arm_fast"
    RIGHT_ARM_MEDIUM = "right_arm_medium"
    RIGHT_ARM_OFF_SPIN = "right_arm_off_spin"
    RIGHT_ARM_LEG_SPIN = "right_arm_leg_spin"
    LEFT_ARM_FAST = "left_arm_fast"
    LEFT_ARM_MEDIUM = "left_arm_medium"
    LEFT_ARM_ORTHODOX = "left_arm_orthodox"
    LEFT_ARM_CHINAMAN = "left_arm_chinaman"


# ============================================================================
# TEAM ENUMS
# ============================================================================

class TeamType(str, PyEnum):
    """Team organization type"""
    CASUAL = "casual"
    CLUB = "club"
    TOURNAMENT_REGISTERED = "tournament_registered"
    FRANCHISE = "franchise"


class TeamMemberRole(str, PyEnum):
    """Role of team member"""
    PLAYER = "player"
    CAPTAIN = "captain"
    VICE_CAPTAIN = "vice_captain"
    COACH = "coach"
    TEAM_ADMIN = "team_admin"


class MembershipStatus(str, PyEnum):
    """Team membership status"""
    ACTIVE = "active"
    BENCHED = "benched"
    INJURED = "injured"
    SUSPENDED = "suspended"
    LEFT = "left"


# ============================================================================
# MATCH ENUMS
# ============================================================================

class MatchType(str, PyEnum):
    """Cricket match format"""
    T20 = "t20"
    ODI = "odi"
    TEST = "test"
    ONE_DAY = "one_day"
    THE_HUNDRED = "the_hundred"
    CUSTOM = "custom"


class MatchCategory(str, PyEnum):
    """Match organization category"""
    CASUAL = "casual"
    TOURNAMENT = "tournament"
    LEAGUE = "league"
    FRIENDLY = "friendly"
    PRACTICE = "practice"


class MatchStatus(str, PyEnum):
    """Match progression status"""
    SCHEDULED = "scheduled"
    TOSS_PENDING = "toss_pending"
    LIVE = "live"
    INNINGS_BREAK = "innings_break"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class MatchVisibility(str, PyEnum):
    """Match visibility to public"""
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS_ONLY = "friends_only"


class ResultType(str, PyEnum):
    """Match result type"""
    NORMAL = "normal"
    TIE = "tie"
    NO_RESULT = "no_result"
    SUPER_OVER = "super_over"
    FORFEIT = "forfeit"


class ElectedTo(str, PyEnum):
    """Toss decision"""
    BAT = "bat"
    BOWL = "bowl"


class OfficialRole(str, PyEnum):
    """Match official role"""
    SCORER = "scorer"
    UMPIRE = "umpire"
    THIRD_UMPIRE = "third_umpire"
    MATCH_REFEREE = "match_referee"


class OfficialAssignment(str, PyEnum):
    """Which team the official represents"""
    TEAM_A = "team_a"
    TEAM_B = "team_b"
    NEUTRAL = "neutral"


# ============================================================================
# SCORING ENUMS
# ============================================================================

class ExtraType(str, PyEnum):
    """Type of extra runs"""
    NONE = "none"
    WIDE = "wide"
    NO_BALL = "no_ball"
    BYE = "bye"
    LEG_BYE = "leg_bye"
    PENALTY = "penalty"


class BoundaryType(str, PyEnum):
    """Type of boundary"""
    FOUR = "four"
    SIX = "six"


class ShotType(str, PyEnum):
    """Type of cricket shot"""
    DEFENSIVE = "defensive"
    DRIVE = "drive"
    CUT = "cut"
    PULL = "pull"
    HOOK = "hook"
    SWEEP = "sweep"
    REVERSE_SWEEP = "reverse_sweep"
    LOFTED = "lofted"
    FLICK = "flick"
    EDGE = "edge"
    MISSED = "missed"
    LEAVE = "leave"


class DismissalType(str, PyEnum):
    """How batsman got out"""
    BOWLED = "bowled"
    CAUGHT = "caught"
    LBW = "lbw"
    RUN_OUT = "run_out"
    STUMPED = "stumped"
    HIT_WICKET = "hit_wicket"
    HANDLED_BALL = "handled_ball"
    OBSTRUCTING_FIELD = "obstructing_field"
    TIMED_OUT = "timed_out"
    RETIRED_HURT = "retired_hurt"
    RETIRED_OUT = "retired_out"


# ============================================================================
# SCORING INTEGRITY ENUMS
# ============================================================================

class EventType(str, PyEnum):
    """Type of scoring event"""
    BALL_BOWLED = "ball_bowled"
    WICKET_FALLEN = "wicket_fallen"
    OVER_COMPLETE = "over_complete"
    INNINGS_COMPLETE = "innings_complete"
    BATSMAN_CHANGE = "batsman_change"
    BOWLER_CHANGE = "bowler_change"
    DRINKS_BREAK = "drinks_break"
    INJURY_TIMEOUT = "injury_timeout"
    INNINGS_START = "innings_start"
    MATCH_START = "match_start"
    MATCH_END = "match_end"
    TOSS_COMPLETED = "toss_completed"


class ValidationStatus(str, PyEnum):
    """Status of scoring event validation"""
    PENDING = "pending"
    VALIDATED = "validated"
    AUTO_VALIDATED = "auto_validated"
    DISPUTED = "disputed"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class ScorerTeamSide(str, PyEnum):
    """Which side the scorer represents"""
    TEAM_A = "team_a"
    TEAM_B = "team_b"
    UMPIRE = "umpire"
    SYSTEM = "system"


class DisputeType(str, PyEnum):
    """Type of scoring dispute"""
    RUNS_MISMATCH = "runs_mismatch"
    WICKET_MISMATCH = "wicket_mismatch"
    EXTRA_MISMATCH = "extra_mismatch"
    BOUNDARY_MISMATCH = "boundary_mismatch"
    DISMISSAL_TYPE_MISMATCH = "dismissal_type_mismatch"
    OTHER = "other"


class ResolutionStatus(str, PyEnum):
    """Dispute resolution status"""
    PENDING = "pending"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    ABANDONED = "abandoned"


class ConsensusMethod(str, PyEnum):
    """How consensus was reached"""
    EXACT_MATCH = "exact_match"
    MAJORITY_2_OF_3 = "majority_2_of_3"
    UMPIRE_OVERRIDE = "umpire_override"
    TIMEOUT_ACCEPT = "timeout_accept"
    MANUAL_RESOLVE = "manual_resolve"


# ============================================================================
# ARCHIVE ENUMS
# ============================================================================

class ArchiveStatus(str, PyEnum):
    """Match archive status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

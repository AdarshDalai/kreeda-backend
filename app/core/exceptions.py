"""
Custom Exceptions for Kreeda Backend
Proper error hierarchy for cricket domain
"""
from fastapi import HTTPException, status


class KreedaBaseException(Exception):
    """Base exception for Kreeda backend"""
    pass


class DatabaseException(KreedaBaseException):
    """Database related errors"""
    pass


class ValidationException(KreedaBaseException):
    """Input validation errors"""
    pass


class BusinessLogicException(KreedaBaseException):
    """Cricket business logic errors"""
    pass


# Specific cricket exceptions
class InningsNotFoundException(DatabaseException):
    """Innings not found in database"""
    def __init__(self, innings_id: int):
        self.innings_id = innings_id
        super().__init__(f"Innings with ID {innings_id} not found")


class MatchNotFoundException(DatabaseException):
    """Match not found in database"""
    def __init__(self, match_id: int):
        self.match_id = match_id
        super().__init__(f"Match with ID {match_id} not found")


class TeamNotFoundException(DatabaseException):
    """Team not found in database"""
    def __init__(self, team_id: int):
        self.team_id = team_id
        super().__init__(f"Team with ID {team_id} not found")


class PlayerNotFoundException(DatabaseException):
    """Player not found in database"""
    def __init__(self, player_id: int):
        self.player_id = player_id
        super().__init__(f"Player with ID {player_id} not found")


class InningsCompletedException(BusinessLogicException):
    """Trying to record ball in completed innings"""
    def __init__(self, innings_id: int):
        self.innings_id = innings_id
        super().__init__(f"Innings {innings_id} is already completed")


class MatchNotInProgressException(BusinessLogicException):
    """Match is not in progress for ball recording"""
    def __init__(self, match_status: str):
        self.match_status = match_status
        super().__init__(f"Match is not in progress. Current status: {match_status}")


class InvalidBallDataException(ValidationException):
    """Invalid ball data provided"""
    pass


class SameTeamException(ValidationException):
    """Teams cannot be the same"""
    def __init__(self, team_id: int):
        self.team_id = team_id
        super().__init__(f"Both teams cannot have the same ID: {team_id}")


# HTTP Exception converters
def convert_to_http_exception(error: KreedaBaseException) -> HTTPException:
    """Convert Kreeda exceptions to HTTP exceptions"""
    
    if isinstance(error, (InningsNotFoundException, MatchNotFoundException, 
                         TeamNotFoundException, PlayerNotFoundException)):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    
    if isinstance(error, (ValidationException, InvalidBallDataException, SameTeamException)):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    
    if isinstance(error, (BusinessLogicException, InningsCompletedException, MatchNotInProgressException)):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error)
        )
    
    if isinstance(error, DatabaseException):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    
    # Fallback for unknown Kreeda exceptions
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred"
    )

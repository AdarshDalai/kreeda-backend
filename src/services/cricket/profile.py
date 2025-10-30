"""
Cricket Profile Service Layer
Business logic for sport profiles and cricket player profiles

Follows SOLID principles:
- Single Responsibility: Each method handles one specific operation
- Open/Closed: Extensible for new sports without modification
- Dependency Inversion: Depends on abstractions (AsyncSession interface)
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from src.models.sport_profile import SportProfile
from src.models.cricket.player_profile import CricketPlayerProfile
from src.models.user_auth import UserAuth
from src.models.user_profile import UserProfile
from src.models.enums import SportType
from src.schemas.cricket.profile import (
    SportProfileCreate, SportProfileResponse,
    CricketPlayerProfileCreate, CricketPlayerProfileUpdate,
    CricketPlayerProfileResponse, CricketPlayerProfileDetailResponse,
    CareerStats, UserBasicInfo
)
from src.core.exceptions import (
    DuplicateSportProfileError, SportProfileNotFoundError,
    CricketProfileNotFoundError, DuplicateCricketProfileError,
    InvalidSportTypeError, NotFoundError
)
from src.core.logging import logger


class CricketProfileService:
    """
    Service class for cricket profile operations
    
    All methods are static to avoid state management
    Each method represents a single business operation
    """
    
    # ========================================================================
    # SPORT PROFILE OPERATIONS
    # ========================================================================
    
    @staticmethod
    async def create_sport_profile(
        user_id: UUID,
        request: SportProfileCreate,
        db: AsyncSession
    ) -> SportProfileResponse:
        """
        Create a new sport profile for a user
        
        Business Rules:
        - User can only have ONE profile per sport type
        - Profile is initially unverified
        
        Args:
            user_id: UUID of the user creating the profile
            request: Sport profile creation data
            db: Database session
        
        Returns:
            SportProfileResponse: Created profile data
        
        Raises:
            DuplicateSportProfileError: If user already has profile for this sport
            NotFoundError: If user doesn't exist
        
        Example:
            profile = await CricketProfileService.create_sport_profile(
                user_id=UUID("..."),
                request=SportProfileCreate(sport_type=SportType.CRICKET),
                db=db_session
            )
        """
        logger.info(
            f"Creating sport profile for user",
            extra={"user_id": str(user_id), "sport_type": request.sport_type.value}
        )
        
        try:
            # Verify user exists
            user_result = await db.execute(
                select(UserAuth).where(UserAuth.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise NotFoundError(
                    message=f"User not found",
                    error_code="USER_NOT_FOUND",
                    details={"user_id": str(user_id)}
                )
            
            # Check for duplicate profile
            existing_result = await db.execute(
                select(SportProfile).where(
                    and_(
                        SportProfile.user_id == user_id,
                        SportProfile.sport_type == request.sport_type
                    )
                )
            )
            existing_profile = existing_result.scalar_one_or_none()
            
            if existing_profile:
                raise DuplicateSportProfileError(sport_type=request.sport_type.value)
            
            # Create new sport profile
            sport_profile = SportProfile(
                user_id=user_id,
                sport_type=request.sport_type,
                visibility=request.visibility,
                is_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(sport_profile)
            await db.commit()
            await db.refresh(sport_profile)
            
            logger.info(
                f"Sport profile created successfully",
                extra={
                    "user_id": str(user_id),
                    "profile_id": str(sport_profile.id),
                    "sport_type": request.sport_type.value
                }
            )
            
            return SportProfileResponse.model_validate(sport_profile)
            
        except (DuplicateSportProfileError, NotFoundError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            # Rollback on any error
            await db.rollback()
            logger.error(
                f"Failed to create sport profile",
                exc_info=True,
                extra={"user_id": str(user_id), "error": str(e)}
            )
            raise
    
    @staticmethod
    async def get_sport_profile(
        profile_id: UUID,
        db: AsyncSession
    ) -> SportProfileResponse:
        """
        Get a sport profile by ID
        
        Args:
            profile_id: UUID of the sport profile
            db: Database session
        
        Returns:
            SportProfileResponse: Profile data
        
        Raises:
            SportProfileNotFoundError: If profile doesn't exist
        """
        result = await db.execute(
            select(SportProfile).where(SportProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise SportProfileNotFoundError(profile_id=str(profile_id))
        
        return SportProfileResponse.model_validate(profile)
    
    @staticmethod
    async def list_user_sport_profiles(
        user_id: UUID,
        sport_type: Optional[SportType],
        db: AsyncSession
    ) -> List[SportProfileResponse]:
        """
        List all sport profiles for a user
        
        Args:
            user_id: UUID of the user
            sport_type: Optional filter by sport type
            db: Database session
        
        Returns:
            List of SportProfileResponse
        """
        query = select(SportProfile).where(SportProfile.user_id == user_id)
        
        if sport_type:
            query = query.where(SportProfile.sport_type == sport_type)
        
        result = await db.execute(query)
        profiles = result.scalars().all()
        
        return [SportProfileResponse.model_validate(p) for p in profiles]
    
    # ========================================================================
    # CRICKET PLAYER PROFILE OPERATIONS
    # ========================================================================
    
    @staticmethod
    async def create_cricket_profile(
        request: CricketPlayerProfileCreate,
        db: AsyncSession
    ) -> CricketPlayerProfileResponse:
        """
        Create a cricket player profile
        
        Business Rules:
        - Must link to an existing sport profile
        - Sport profile must be CRICKET type
        - Each sport profile can only have ONE cricket profile
        
        Args:
            request: Cricket profile creation data
            db: Database session
        
        Returns:
            CricketPlayerProfileResponse: Created cricket profile
        
        Raises:
            SportProfileNotFoundError: If sport profile doesn't exist
            InvalidSportTypeError: If sport profile is not CRICKET type
            DuplicateCricketProfileError: If sport profile already has cricket profile
        """
        logger.info(
            f"Creating cricket profile",
            extra={
                "sport_profile_id": str(request.sport_profile_id),
                "playing_role": request.playing_role.value
            }
        )
        
        try:
            # Verify sport profile exists and is CRICKET type
            sport_result = await db.execute(
                select(SportProfile).where(SportProfile.id == request.sport_profile_id)
            )
            sport_profile = sport_result.scalar_one_or_none()
            
            if not sport_profile:
                raise SportProfileNotFoundError(profile_id=str(request.sport_profile_id))
            
            if sport_profile.sport_type != SportType.CRICKET:
                raise InvalidSportTypeError(actual_sport_type=sport_profile.sport_type.value)
            
            # Check for duplicate cricket profile
            existing_result = await db.execute(
                select(CricketPlayerProfile).where(
                    CricketPlayerProfile.sport_profile_id == request.sport_profile_id
                )
            )
            existing_cricket = existing_result.scalar_one_or_none()
            
            if existing_cricket:
                raise DuplicateCricketProfileError(sport_profile_id=str(request.sport_profile_id))
            
            # Create cricket profile with initialized stats
            cricket_profile = CricketPlayerProfile(
                sport_profile_id=request.sport_profile_id,
                playing_role=request.playing_role,
                batting_style=request.batting_style,
                bowling_style=request.bowling_style,
                jersey_number=request.jersey_number,
                # Initialize all stats to 0
                matches_played=0,
                total_runs=0,
                total_wickets=0,
                catches=0,
                stumpings=0,
                run_outs=0,
                batting_avg=None,
                strike_rate=None,
                highest_score=0,
                fifties=0,
                hundreds=0,
                balls_faced=0,
                fours=0,
                sixes=0,
                bowling_avg=None,
                economy_rate=None,
                best_bowling=None,
                five_wickets=0,
                ten_wickets=0,
                balls_bowled=0,
                runs_conceded=0,
                maidens=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(cricket_profile)
            await db.commit()
            await db.refresh(cricket_profile)
            
            logger.info(
                f"Cricket profile created successfully",
                extra={
                    "cricket_profile_id": str(cricket_profile.id),
                    "sport_profile_id": str(request.sport_profile_id)
                }
            )
            
            return CricketPlayerProfileResponse.model_validate(cricket_profile)
            
        except (SportProfileNotFoundError, InvalidSportTypeError, DuplicateCricketProfileError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to create cricket profile",
                exc_info=True,
                extra={"error": str(e)}
            )
            raise
    
    @staticmethod
    async def get_cricket_profile(
        profile_id: UUID,
        db: AsyncSession,
        include_user_info: bool = False
    ) -> CricketPlayerProfileDetailResponse:
        """
        Get cricket profile with full details
        
        Args:
            profile_id: UUID of the cricket profile
            db: Database session
            include_user_info: Whether to include user information
        
        Returns:
            CricketPlayerProfileDetailResponse: Full profile with stats
        
        Raises:
            CricketProfileNotFoundError: If profile doesn't exist
        """
        query = select(CricketPlayerProfile).where(CricketPlayerProfile.id == profile_id)
        
        if include_user_info:
            query = query.options(
                joinedload(CricketPlayerProfile.sport_profile).joinedload(SportProfile.user)
            )
        
        result = await db.execute(query)
        cricket_profile = result.scalar_one_or_none()
        
        if not cricket_profile:
            raise CricketProfileNotFoundError(profile_id=str(profile_id))
        
        # Build career stats
        career_stats = CareerStats(
            matches_played=cricket_profile.matches_played,
            total_runs=cricket_profile.total_runs,
            batting_avg=cricket_profile.batting_avg,
            strike_rate=cricket_profile.strike_rate,
            highest_score=cricket_profile.highest_score,
            fifties=cricket_profile.fifties,
            hundreds=cricket_profile.hundreds,
            balls_faced=cricket_profile.balls_faced,
            fours=cricket_profile.fours,
            sixes=cricket_profile.sixes,
            total_wickets=cricket_profile.total_wickets,
            bowling_avg=cricket_profile.bowling_avg,
            economy_rate=cricket_profile.economy_rate,
            best_bowling=cricket_profile.best_bowling,
            five_wickets=cricket_profile.five_wickets,
            ten_wickets=cricket_profile.ten_wickets,
            balls_bowled=cricket_profile.balls_bowled,
            runs_conceded=cricket_profile.runs_conceded,
            maidens=cricket_profile.maidens,
            catches=cricket_profile.catches,
            stumpings=cricket_profile.stumpings,
            run_outs=cricket_profile.run_outs
        )
        
        # Build user info if requested
        user_info = None
        if include_user_info and cricket_profile.sport_profile:
            sport_profile = cricket_profile.sport_profile
            if sport_profile.user:
                # Get user profile for full name and avatar
                user_profile_result = await db.execute(
                    select(UserProfile).where(UserProfile.user_id == sport_profile.user_id)
                )
                user_profile = user_profile_result.scalar_one_or_none()
                
                user_info = UserBasicInfo(
                    id=sport_profile.user.user_id,
                    email=sport_profile.user.email,
                    full_name=user_profile.name if user_profile else None,
                    avatar_url=user_profile.avatar_url if user_profile else None
                )
        
        return CricketPlayerProfileDetailResponse(
            id=cricket_profile.id,
            sport_profile_id=cricket_profile.sport_profile_id,
            user=user_info,
            playing_role=cricket_profile.playing_role,
            batting_style=cricket_profile.batting_style,
            bowling_style=cricket_profile.bowling_style,
            jersey_number=cricket_profile.jersey_number,
            career_stats=career_stats,
            stats_last_updated=cricket_profile.stats_last_updated,
            created_at=cricket_profile.created_at,
            updated_at=cricket_profile.updated_at
        )
    
    @staticmethod
    async def update_cricket_profile(
        profile_id: UUID,
        request: CricketPlayerProfileUpdate,
        db: AsyncSession
    ) -> CricketPlayerProfileResponse:
        """
        Update cricket player profile
        
        Only provided fields are updated (partial update)
        
        Args:
            profile_id: UUID of the cricket profile
            request: Update data (only provided fields)
            db: Database session
        
        Returns:
            CricketPlayerProfileResponse: Updated profile
        
        Raises:
            CricketProfileNotFoundError: If profile doesn't exist
        """
        logger.info(
            f"Updating cricket profile",
            extra={"cricket_profile_id": str(profile_id)}
        )
        
        try:
            # Fetch existing profile
            result = await db.execute(
                select(CricketPlayerProfile).where(CricketPlayerProfile.id == profile_id)
            )
            cricket_profile = result.scalar_one_or_none()
            
            if not cricket_profile:
                raise CricketProfileNotFoundError(profile_id=str(profile_id))
            
            # Update only provided fields
            update_data = request.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(cricket_profile, field, value)
            
            cricket_profile.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(cricket_profile)
            
            logger.info(
                f"Cricket profile updated successfully",
                extra={
                    "cricket_profile_id": str(profile_id),
                    "updated_fields": list(update_data.keys())
                }
            )
            
            return CricketPlayerProfileResponse.model_validate(cricket_profile)
            
        except CricketProfileNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to update cricket profile",
                exc_info=True,
                extra={"cricket_profile_id": str(profile_id), "error": str(e)}
            )
            raise

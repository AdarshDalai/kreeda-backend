from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Dict, Optional, Tuple
import json
import logging
from datetime import datetime

from app.models.scoring_integrity import (
    MatchScorer, BallScoreEntry, BallVerification, 
    ScoringAuditLog, MatchIntegrityCheck, ScorerRole
)
from app.models.cricket import CricketMatch, CricketBall
from app.models.user import User
from app.schemas.cricket import BallRecord

logger = logging.getLogger(__name__)


class ScoringIntegrityService:
    """Service to ensure scoring integrity and prevent match-fixing"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def assign_match_scorers(
        self, 
        match_id: str, 
        team_a_scorer_id: str, 
        team_b_scorer_id: str,
        appointed_by_id: str,
        umpire_id: Optional[str] = None
    ) -> Dict:
        """Assign official scorers for a match"""
        try:
            # Create scorer assignments
            scorers = [
                MatchScorer(
                    match_id=match_id,
                    user_id=team_a_scorer_id,
                    role=ScorerRole.TEAM_A_SCORER,
                    appointed_by_id=appointed_by_id
                ),
                MatchScorer(
                    match_id=match_id,
                    user_id=team_b_scorer_id,
                    role=ScorerRole.TEAM_B_SCORER,
                    appointed_by_id=appointed_by_id
                )
            ]
            
            if umpire_id:
                scorers.append(MatchScorer(
                    match_id=match_id,
                    user_id=umpire_id,
                    role=ScorerRole.UMPIRE,
                    appointed_by_id=appointed_by_id
                ))
            
            for scorer in scorers:
                self.db.add(scorer)
            
            await self.db.commit()
            
            # Log the assignment
            await self._log_audit_action(
                match_id=match_id,
                user_id=appointed_by_id,
                action_type="scorer_assignment",
                new_values=json.dumps({
                    "team_a_scorer": team_a_scorer_id,
                    "team_b_scorer": team_b_scorer_id,
                    "umpire": umpire_id
                })
            )
            
            return {"success": True, "message": "Scorers assigned successfully"}
            
        except Exception as e:
            logger.error(f"Error assigning scorers: {str(e)}")
            await self.db.rollback()
            raise
    
    async def verify_scorer_authorization(self, match_id: str, user_id: str) -> bool:
        """Check if user is authorized to score for this match"""
        try:
            query = select(MatchScorer).where(
                and_(
                    MatchScorer.match_id == match_id,
                    MatchScorer.user_id == user_id,
                    MatchScorer.is_active == True
                )
            )
            result = await self.db.execute(query)
            scorer = result.scalar_one_or_none()
            
            return scorer is not None
            
        except Exception as e:
            logger.error(f"Error verifying scorer authorization: {str(e)}")
            return False
    
    async def record_ball_entry(
        self, 
        match_id: str, 
        scorer_id: str, 
        ball_data: BallRecord,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """Record a ball entry from a scorer"""
        try:
            # Verify scorer authorization
            if not await self.verify_scorer_authorization(match_id, scorer_id):
                raise ValueError("User not authorized to score for this match")
            
            # Create ball score entry
            entry = BallScoreEntry(
                match_id=match_id,
                scorer_id=scorer_id,
                innings=1,  # TODO: Get current innings from match
                over_number=ball_data.over_number,
                ball_number=ball_data.ball_number,
                bowler_id=ball_data.bowler_id,
                batsman_striker_id=ball_data.batsman_striker_id,
                batsman_non_striker_id=ball_data.batsman_non_striker_id,
                runs_scored=ball_data.runs_scored,
                extras=ball_data.extras,
                ball_type=ball_data.ball_type,
                is_wicket=ball_data.is_wicket,
                wicket_type=ball_data.wicket_type,
                dismissed_player_id=ball_data.dismissed_player_id,
                is_boundary=ball_data.is_boundary,
                boundary_type=ball_data.boundary_type
            )
            
            self.db.add(entry)
            await self.db.flush()
            
            # Log the entry
            await self._log_audit_action(
                match_id=match_id,
                user_id=scorer_id,
                action_type="ball_entry",
                target_innings=1,
                target_over=ball_data.over_number,
                target_ball=ball_data.ball_number,
                new_values=json.dumps(ball_data.dict()),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Check for verification
            verification_result = await self._check_ball_verification(
                match_id=match_id,
                innings=1,
                over_number=ball_data.over_number,
                ball_number=ball_data.ball_number
            )
            
            await self.db.commit()
            
            return {
                "success": True,
                "entry_id": str(entry.id),
                "verification_status": verification_result["status"],
                "consensus_reached": verification_result.get("consensus_reached", False)
            }
            
        except Exception as e:
            logger.error(f"Error recording ball entry: {str(e)}")
            await self.db.rollback()
            raise
    
    async def _check_ball_verification(
        self, 
        match_id: str, 
        innings: int, 
        over_number: int, 
        ball_number: int
    ) -> Dict:
        """Check verification status for a specific ball"""
        try:
            # Get all entries for this ball
            query = select(BallScoreEntry).where(
                and_(
                    BallScoreEntry.match_id == match_id,
                    BallScoreEntry.innings == innings,
                    BallScoreEntry.over_number == over_number,
                    BallScoreEntry.ball_number == ball_number
                )
            )
            result = await self.db.execute(query)
            entries = result.scalars().all()
            
            if len(entries) < 2:
                return {"status": "pending", "message": "Waiting for second scorer"}
            
            # Check for consensus
            consensus_data = self._analyze_entries_consensus(list(entries))
            
            # Update or create verification record
            verification = await self._update_ball_verification(
                match_id=match_id,
                innings=innings,
                over_number=over_number,
                ball_number=ball_number,
                consensus_data=consensus_data
            )
            
            # If consensus reached, create official ball record
            if consensus_data["consensus_reached"]:
                await self._create_official_ball_record(
                    match_id=match_id,
                    verification=verification,
                    consensus_entry=consensus_data["consensus_entry"]
                )
            
            return {
                "status": "verified" if consensus_data["consensus_reached"] else "disputed",
                "consensus_reached": consensus_data["consensus_reached"],
                "total_entries": len(entries),
                "matching_entries": consensus_data["matching_count"]
            }
            
        except Exception as e:
            logger.error(f"Error checking ball verification: {str(e)}")
            raise
    
    def _analyze_entries_consensus(self, entries: List[BallScoreEntry]) -> Dict:
        """Analyze entries to determine consensus"""
        if len(entries) < 2:
            return {"consensus_reached": False, "matching_count": 0}
        
        # Group entries by key attributes
        entry_groups = {}
        for entry in entries:
            key = (
                entry.runs_scored,
                entry.extras,
                entry.ball_type,
                entry.is_wicket,
                entry.wicket_type,
                entry.is_boundary,
                entry.boundary_type
            )
            if key not in entry_groups:
                entry_groups[key] = []
            entry_groups[key].append(entry)
        
        # Find majority consensus
        max_count = 0
        consensus_entry = None
        
        for key, group in entry_groups.items():
            if len(group) > max_count:
                max_count = len(group)
                consensus_entry = group[0]  # Use first entry as representative
        
        # Consensus reached if majority agrees (>50% for multiple scorers)
        consensus_reached = max_count >= (len(entries) + 1) // 2
        
        return {
            "consensus_reached": consensus_reached,
            "matching_count": max_count,
            "total_count": len(entries),
            "consensus_entry": consensus_entry
        }
    
    async def _update_ball_verification(
        self, 
        match_id: str, 
        innings: int, 
        over_number: int, 
        ball_number: int,
        consensus_data: Dict
    ) -> BallVerification:
        """Update or create ball verification record"""
        try:
            # Check if verification already exists
            query = select(BallVerification).where(
                and_(
                    BallVerification.match_id == match_id,
                    BallVerification.innings == innings,
                    BallVerification.over_number == over_number,
                    BallVerification.ball_number == ball_number
                )
            )
            result = await self.db.execute(query)
            verification = result.scalar_one_or_none()
            
            if verification is None:
                verification = BallVerification(
                    match_id=match_id,
                    innings=innings,
                    over_number=over_number,
                    ball_number=ball_number
                )
                self.db.add(verification)
            
            # Update verification details
            setattr(verification, 'total_entries', consensus_data["total_count"])
            setattr(verification, 'matching_entries', consensus_data["matching_count"])
            setattr(verification, 'consensus_reached', consensus_data["consensus_reached"])
            setattr(verification, 'has_dispute', not consensus_data["consensus_reached"])
            
            if consensus_data["consensus_reached"]:
                setattr(verification, 'final_entry_id', consensus_data["consensus_entry"].id)
                setattr(verification, 'verified_at', datetime.utcnow())
            
            await self.db.flush()
            return verification
            
        except Exception as e:
            logger.error(f"Error updating ball verification: {str(e)}")
            raise
    
    async def _create_official_ball_record(
        self, 
        match_id: str, 
        verification: BallVerification,
        consensus_entry: BallScoreEntry
    ):
        """Create official ball record after verification"""
        try:
            # Check if ball record already exists
            query = select(CricketBall).where(
                and_(
                    CricketBall.match_id == match_id,
                    CricketBall.innings == verification.innings,
                    CricketBall.over_number == verification.over_number,
                    CricketBall.ball_number == verification.ball_number
                )
            )
            result = await self.db.execute(query)
            existing_ball = result.scalar_one_or_none()
            
            if existing_ball is None:
                # Create new official ball record
                official_ball = CricketBall(
                    match_id=match_id,
                    innings=verification.innings,
                    over_number=verification.over_number,
                    ball_number=verification.ball_number,
                    bowler_id=consensus_entry.bowler_id,
                    batsman_striker_id=consensus_entry.batsman_striker_id,
                    batsman_non_striker_id=consensus_entry.batsman_non_striker_id,
                    runs_scored=consensus_entry.runs_scored,
                    extras=consensus_entry.extras,
                    ball_type=consensus_entry.ball_type,
                    is_wicket=consensus_entry.is_wicket,
                    wicket_type=consensus_entry.wicket_type,
                    dismissed_player_id=consensus_entry.dismissed_player_id,
                    is_boundary=consensus_entry.is_boundary,
                    boundary_type=consensus_entry.boundary_type
                )
                
                self.db.add(official_ball)
                logger.info(f"Created official ball record for match {match_id}, over {verification.over_number}.{verification.ball_number}")
            
        except Exception as e:
            logger.error(f"Error creating official ball record: {str(e)}")
            raise
    
    async def _log_audit_action(
        self,
        match_id: str,
        user_id: str,
        action_type: str,
        target_innings: Optional[int] = None,
        target_over: Optional[int] = None,
        target_ball: Optional[int] = None,
        old_values: Optional[str] = None,
        new_values: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Log audit action"""
        try:
            audit_log = ScoringAuditLog(
                match_id=match_id,
                user_id=user_id,
                action_type=action_type,
                target_innings=target_innings,
                target_over=target_over,
                target_ball=target_ball,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                notes=notes
            )
            
            self.db.add(audit_log)
            await self.db.flush()
            
        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")
            # Don't raise here to avoid breaking main functionality
    
    async def get_match_scoring_status(self, match_id: str) -> Dict:
        """Get comprehensive scoring status for a match"""
        try:
            # Get scorers
            scorers_query = select(MatchScorer).where(
                and_(
                    MatchScorer.match_id == match_id,
                    MatchScorer.is_active == True
                )
            )
            scorers_result = await self.db.execute(scorers_query)
            scorers = scorers_result.scalars().all()
            
            # Get pending verifications
            pending_query = select(BallVerification).where(
                and_(
                    BallVerification.match_id == match_id,
                    BallVerification.consensus_reached == False
                )
            )
            pending_result = await self.db.execute(pending_query)
            pending_verifications = pending_result.scalars().all()
            
            # Get verified balls count
            verified_query = select(func.count(CricketBall.id)).where(
                CricketBall.match_id == match_id
            )
            verified_result = await self.db.execute(verified_query)
            verified_balls_count = verified_result.scalar()
            
            return {
                "match_id": match_id,
                "scorers": [
                    {
                        "user_id": str(scorer.user_id),
                        "role": scorer.role.value,
                        "appointed_at": scorer.appointed_at.isoformat()
                    }
                    for scorer in scorers
                ],
                "verified_balls": verified_balls_count,
                "pending_verifications": len(pending_verifications),
                "disputes": [
                    {
                        "over": v.over_number,
                        "ball": v.ball_number,
                        "total_entries": v.total_entries,
                        "matching_entries": v.matching_entries
                    }
                    for v in pending_verifications if getattr(v, 'has_dispute', False)
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting match scoring status: {str(e)}")
            raise
    
    async def resolve_dispute(
        self, 
        match_id: str, 
        innings: int, 
        over_number: int, 
        ball_number: int,
        resolver_id: str,
        final_entry_id: str,
        resolution_notes: str
    ) -> Dict:
        """Resolve a scoring dispute manually"""
        try:
            # Get verification record
            query = select(BallVerification).where(
                and_(
                    BallVerification.match_id == match_id,
                    BallVerification.innings == innings,
                    BallVerification.over_number == over_number,
                    BallVerification.ball_number == ball_number
                )
            )
            result = await self.db.execute(query)
            verification = result.scalar_one_or_none()
            
            if not verification:
                raise ValueError("Verification record not found")
            
            # Update verification
            setattr(verification, 'consensus_reached', True)
            setattr(verification, 'has_dispute', False)
            setattr(verification, 'final_entry_id', final_entry_id)
            setattr(verification, 'resolved_by_id', resolver_id)
            setattr(verification, 'resolution_notes', resolution_notes)
            setattr(verification, 'verified_at', datetime.utcnow())
            
            # Get the final entry to create official ball record
            entry_query = select(BallScoreEntry).where(
                BallScoreEntry.id == final_entry_id
            )
            entry_result = await self.db.execute(entry_query)
            final_entry = entry_result.scalar_one_or_none()
            
            if final_entry:
                await self._create_official_ball_record(
                    match_id=match_id,
                    verification=verification,
                    consensus_entry=final_entry
                )
            
            # Log resolution
            await self._log_audit_action(
                match_id=match_id,
                user_id=resolver_id,
                action_type="dispute_resolution",
                target_innings=innings,
                target_over=over_number,
                target_ball=ball_number,
                notes=resolution_notes
            )
            
            await self.db.commit()
            
            return {"success": True, "message": "Dispute resolved successfully"}
            
        except Exception as e:
            logger.error(f"Error resolving dispute: {str(e)}")
            await self.db.rollback()
            raise

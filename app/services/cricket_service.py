from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any
from datetime import datetime

from app.models.cricket import CricketMatch, CricketBall
from app.schemas.cricket import BallRecord


class CricketService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_ball(self, match: CricketMatch, ball_data: BallRecord) -> tuple:
        """Record a ball and update match statistics"""
        
        # Simple validation
        if ball_data.is_wicket and not ball_data.wicket_type:
            raise ValueError("Wicket type is required for wickets")
        
        if ball_data.is_boundary and ball_data.runs_scored not in [4, 6]:
            raise ValueError("Boundaries must score 4 or 6 runs")
        
        # Get fresh match data
        result = await self.db.execute(
            select(CricketMatch).where(CricketMatch.id == match.id)
        )
        fresh_match = result.scalar_one()
        
        # Create ball record
        ball = CricketBall(
            match_id=fresh_match.id,
            innings=fresh_match.current_innings,
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
        
        self.db.add(ball)
        await self.db.flush()
        
        # Update match scores based on innings
        total_runs = ball_data.runs_scored + ball_data.extras
        wicket_increment = 1 if ball_data.is_wicket else 0
        current_innings_value = getattr(fresh_match, 'current_innings', 1)
        
        if current_innings_value == 1:
            await self.db.execute(
                update(CricketMatch)
                .where(CricketMatch.id == fresh_match.id)
                .values(
                    team_a_score=CricketMatch.team_a_score + total_runs,
                    team_a_wickets=CricketMatch.team_a_wickets + wicket_increment,
                    updated_at=datetime.utcnow()
                )
            )
        else:
            await self.db.execute(
                update(CricketMatch)
                .where(CricketMatch.id == fresh_match.id)
                .values(
                    team_b_score=CricketMatch.team_b_score + total_runs,
                    team_b_wickets=CricketMatch.team_b_wickets + wicket_increment,
                    updated_at=datetime.utcnow()
                )
            )
        
        await self.db.commit()
        
        # Get updated match
        result = await self.db.execute(
            select(CricketMatch).where(CricketMatch.id == fresh_match.id)
        )
        updated_match = result.scalar_one()
        
        # Generate scorecard
        scorecard = await self.generate_scorecard(updated_match)
        
        return ball, scorecard
    
    async def complete_match(self, match: CricketMatch):
        """Complete the match"""
        
        await self.db.execute(
            update(CricketMatch)
            .where(CricketMatch.id == match.id)
            .values(
                status="completed",
                completed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        
        await self.db.commit()
    
    async def generate_scorecard(self, match: CricketMatch) -> Dict[str, Any]:
        """Generate current scorecard"""
        
        scorecard = {
            "team_a": {
                "score": match.team_a_score,
                "wickets": match.team_a_wickets,
                "overs": match.team_a_overs
            },
            "team_b": {
                "score": match.team_b_score,
                "wickets": match.team_b_wickets,
                "overs": match.team_b_overs
            },
            "current_partnership": 0,
            "required_run_rate": None,
            "balls_remaining": None,
            "status": match.status,
            "current_innings": match.current_innings
        }
        
        return scorecard

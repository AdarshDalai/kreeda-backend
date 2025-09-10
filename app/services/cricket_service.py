from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any
from datetime import datetime

from app.models.cricket import CricketMatch, CricketBall
from app.schemas.cricket import BallRecord
from app.utils.websocket import websocket_manager
from app.utils.commentary import commentary_generator


class CricketService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_ball(self, match_id: str, ball_data: BallRecord) -> tuple:
        """Record a ball and update match statistics with proper transaction handling"""
        
        # Simple validation
        if ball_data.is_wicket and not ball_data.wicket_type:
            raise ValueError("Wicket type is required for wickets")
        
        if ball_data.is_boundary and ball_data.runs_scored not in [4, 6]:
            raise ValueError("Boundaries must score 4 or 6 runs")
        
        try:
            # Start transaction
            async with self.db.begin():
                # Get fresh match data within transaction
                result = await self.db.execute(
                    select(CricketMatch).where(CricketMatch.id == match_id)
                )
                match = result.scalar_one_or_none()
                
                if not match:
                    raise ValueError("Match not found")
                
                # Auto-calculate over and ball position from existing balls
                balls_count_result = await self.db.execute(
                    select(CricketBall).where(
                        CricketBall.match_id == match_id,
                        CricketBall.innings == match.current_innings,
                        CricketBall.ball_type == "legal"
                    ).order_by(CricketBall.created_at.desc())
                )
                existing_balls = balls_count_result.scalars().all()
                legal_balls_count = len(existing_balls)
                
                # Calculate current over and ball
                current_over = (legal_balls_count // 6) + 1
                current_ball = (legal_balls_count % 6) + 1
                
                # Adjust for extras (don't increment ball count for wides/noballs)
                if ball_data.ball_type in ["wide", "no_ball"]:
                    # Use same over.ball position as previous
                    if existing_balls:
                        last_ball = existing_balls[0]
                        current_over = last_ball.over_number
                        current_ball = last_ball.ball_number
                    else:
                        current_over = 1
                        current_ball = 1
                else:
                    # Legal ball - increment position
                    if existing_balls and ball_data.ball_type == "legal":
                        current_ball += 1
                        if current_ball > 6:
                            current_over += 1
                            current_ball = 1
                
                # Create ball record
                ball = CricketBall(
                    match_id=match.id,
                    innings=match.current_innings,
                    over_number=current_over,
                    ball_number=current_ball,
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
                
                # Calculate scoring values
                total_runs = ball_data.runs_scored + ball_data.extras
                wicket_increment = 1 if ball_data.is_wicket else 0
                
                # Calculate overs as float (e.g., 3.4 = 3 overs and 4 balls)
                current_overs = current_over - 1 + (current_ball / 10.0)
                
                # Update match scores using proper SQLAlchemy update
                current_innings_val = getattr(match, 'current_innings', 1)
                if current_innings_val == 1:
                    await self.db.execute(
                        update(CricketMatch)
                        .where(CricketMatch.id == match.id)
                        .values(
                            team_a_score=CricketMatch.team_a_score + total_runs,
                            team_a_wickets=CricketMatch.team_a_wickets + wicket_increment,
                            team_a_overs=current_overs,
                            updated_at=datetime.utcnow()
                        )
                    )
                else:
                    await self.db.execute(
                        update(CricketMatch)
                        .where(CricketMatch.id == match.id)
                        .values(
                            team_b_score=CricketMatch.team_b_score + total_runs,
                            team_b_wickets=CricketMatch.team_b_wickets + wicket_increment,
                            team_b_overs=current_overs,
                            updated_at=datetime.utcnow()
                        )
                    )
                
                await self.db.flush()
                
                # Get updated match for scorecard generation
                updated_result = await self.db.execute(
                    select(CricketMatch).where(CricketMatch.id == match.id)
                )
                updated_match = updated_result.scalar_one()
                
                # Generate scorecard
                scorecard = await self.generate_scorecard(updated_match)
                
                # Generate commentary for this ball
                match_context = {
                    "current_score": updated_match.team_a_score if updated_match.current_innings == 1 else updated_match.team_b_score,
                    "current_wickets": updated_match.team_a_wickets if updated_match.current_innings == 1 else updated_match.team_b_wickets,
                    "required_run_rate": getattr(updated_match, 'required_run_rate', 0),
                    "current_run_rate": getattr(updated_match, 'current_run_rate', 0),
                    "overs_remaining": updated_match.overs_per_innings - (updated_match.team_a_overs if updated_match.current_innings == 1 else updated_match.team_b_overs or 0)
                }
                
                commentary = commentary_generator.generate_ball_commentary(ball, match_context)
                
                # Send real-time updates
                ball_data = {
                    "over": getattr(ball, 'over_number', 0),
                    "ball": getattr(ball, 'ball_number', 0),
                    "runs": getattr(ball, 'runs_scored', 0),
                    "extras": getattr(ball, 'extras', 0),
                    "is_wicket": getattr(ball, 'is_wicket', False),
                    "is_boundary": getattr(ball, 'is_boundary', False),
                    "ball_type": getattr(ball, 'ball_type', 'legal'),
                    "commentary": commentary
                }
                
                # Broadcast ball update with commentary
                await websocket_manager.broadcast_ball_update(match_id, ball_data, scorecard)
                
                # Special alerts for wickets and boundaries
                if getattr(ball, 'is_wicket', False):
                    wicket_data = {
                        "wicket_type": getattr(ball, 'wicket_type', ''),
                        "dismissed_player_name": "Player",  # Would need to fetch from DB
                        "runs": getattr(ball, 'runs_scored', 0)
                    }
                    await websocket_manager.broadcast_wicket_alert(match_id, wicket_data)
                
                if getattr(ball, 'is_boundary', False):
                    boundary_data = {
                        "runs_scored": getattr(ball, 'runs_scored', 0),
                        "boundary_type": getattr(ball, 'boundary_type', '')
                    }
                    await websocket_manager.broadcast_boundary_alert(match_id, boundary_data)
                
                return ball, scorecard
                
        except Exception as e:
            await self.db.rollback()
            raise
    
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
    
    async def get_match_scorecard(self, match_id: str) -> Dict[str, Any]:
        """Get scorecard for a specific match"""
        try:
            # Get match
            result = await self.db.execute(
                select(CricketMatch).where(CricketMatch.id == match_id)
            )
            match = result.scalar_one_or_none()
            
            if not match:
                raise ValueError("Match not found")
            
            return await self.generate_scorecard(match)
            
        except Exception as e:
            raise ValueError(f"Error generating scorecard: {str(e)}")

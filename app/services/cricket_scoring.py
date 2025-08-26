"""
Cricket Scoring Service - The heart of Kreeda
Handles ball-by-ball scoring, statistics calculation, and match state management
Built for speed and accuracy - 3 second rule compliance!
"""
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.cricket import Match, Innings, Ball, Player
from app.schemas.cricket import BallCreate, LiveScore, BatsmanStats, BowlerStats, InningsStats
from app.core.exceptions import (
    InningsNotFoundException, InningsCompletedException, 
    InvalidBallDataException, PlayerNotFoundException
)


class CricketScoringService:
    """Core cricket scoring logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_ball(self, innings_id: int, ball_data: BallCreate) -> Tuple[Ball, Dict[str, Any]]:
        """
        Record a cricket ball and update all statistics
        Returns: (Ball record, Live score data)
        """
        innings = self.db.query(Innings).filter(Innings.id == innings_id).first()
        if not innings:
            raise InningsNotFoundException(innings_id)
        
        # Calculate ball position
        current_over, current_ball = self._get_next_ball_position(innings_id)
        
        # Create ball record
        ball = Ball(
            innings_id=innings_id,
            over_number=current_over,
            ball_number=current_ball,
            **ball_data.dict()
        )
        
        # Set ball validity (wides and no-balls don't count as legal deliveries)
        ball.is_valid_ball = ball_data.extra_type not in ['wide', 'noball']
        
        self.db.add(ball)
        self.db.flush()  # Get ball ID
        
        # Update innings statistics
        self._update_innings_stats(innings, ball)
        
        # Update match status if needed
        self._check_innings_completion(innings)
        
        self.db.commit()
        
        # Generate live score
        live_score = self.get_live_score(innings.match_id)
        
        return ball, live_score
    
    def _get_next_ball_position(self, innings_id: int) -> Tuple[int, int]:
        """Calculate the over and ball number for the next ball"""
        last_ball = (self.db.query(Ball)
                    .filter(Ball.innings_id == innings_id)
                    .order_by(desc(Ball.id))
                    .first())
        
        if not last_ball:
            return 1, 1  # First ball of innings
        
        # If last ball was a wide or no-ball, same position
        if not last_ball.is_valid_ball:
            return last_ball.over_number, last_ball.ball_number
        
        # Normal progression
        if last_ball.ball_number < 6:
            return last_ball.over_number, last_ball.ball_number + 1
        else:
            return last_ball.over_number + 1, 1
    
    def _update_innings_stats(self, innings: Innings, ball: Ball):
        """Update innings totals after each ball"""
        # Add runs
        innings.total_runs += (ball.runs + ball.extras)
        
        # Add extras
        innings.extras += ball.extras
        
        # Add wicket
        if ball.is_wicket:
            innings.wickets_lost += 1
        
        # Update overs completed
        if ball.is_valid_ball:
            total_balls = self._count_valid_balls(innings.id)
            innings.overs_completed = Decimal(total_balls // 6) + Decimal((total_balls % 6) / 10)
    
    def _count_valid_balls(self, innings_id: int) -> int:
        """Count valid balls (excludes wides and no-balls)"""
        return (self.db.query(Ball)
                .filter(and_(Ball.innings_id == innings_id, Ball.is_valid_ball == True))
                .count())
    
    def _check_innings_completion(self, innings: Innings):
        """Check if innings is complete and update match status"""
        match = innings.match
        
        # Innings complete if: all overs bowled OR all out (10 wickets)
        if (innings.overs_completed >= match.overs_per_side or 
            innings.wickets_lost >= 10):
            
            innings.is_completed = True
            
            if innings.innings_number == 1:
                # Start second innings
                match.current_innings = 2
                match.status = 'innings_2'
                self._create_second_innings(match)
            else:
                # Match complete
                match.status = 'completed'
                self._determine_winner(match)
    
    def _create_second_innings(self, match: Match):
        """Create the second innings"""
        first_innings = (self.db.query(Innings)
                        .filter(and_(Innings.match_id == match.id, 
                                   Innings.innings_number == 1))
                        .first())
        
        # Swap batting teams
        batting_team_id = (match.team_b_id if first_innings.batting_team_id == match.team_a_id 
                          else match.team_a_id)
        bowling_team_id = first_innings.batting_team_id
        
        second_innings = Innings(
            match_id=match.id,
            innings_number=2,
            batting_team_id=batting_team_id,
            bowling_team_id=bowling_team_id
        )
        
        self.db.add(second_innings)
    
    def _determine_winner(self, match: Match):
        """Determine match winner and margin"""
        innings_1 = self._get_innings(match.id, 1)
        innings_2 = self._get_innings(match.id, 2)
        
        if innings_1.total_runs > innings_2.total_runs:
            match.winner_id = innings_1.batting_team_id
            margin = innings_1.total_runs - innings_2.total_runs
            match.win_margin = f"{margin} runs"
        elif innings_2.total_runs > innings_1.total_runs:
            match.winner_id = innings_2.batting_team_id
            wickets_remaining = 10 - innings_2.wickets_lost
            match.win_margin = f"{wickets_remaining} wickets"
        else:
            match.win_margin = "Match tied"
    
    def get_live_score(self, match_id: int) -> LiveScore:
        """Generate complete live score data - optimized for speed"""
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise ValueError("Match not found")
        
        current_innings = self._get_current_innings(match_id)
        if not current_innings:
            raise ValueError("No active innings found")
        
        # Get innings stats
        innings_stats = self._get_innings_stats(current_innings)
        
        # Get current batsmen
        current_batsmen = self._get_current_batsmen_stats(current_innings.id)
        
        # Get current bowler
        current_bowler = self._get_current_bowler_stats(current_innings.id)
        
        # Get recent balls
        recent_balls = self._get_recent_balls(current_innings.id, limit=6)
        
        # Calculate target (for 2nd innings)
        target = None
        if current_innings.innings_number == 2:
            first_innings = self._get_innings(match_id, 1)
            target = first_innings.total_runs + 1
        
        return LiveScore(
            match_id=match_id,
            match_status=match.status,
            current_innings=innings_stats,
            current_batsmen=current_batsmen,
            current_bowler=current_bowler,
            recent_balls=recent_balls,
            target=target
        )
    
    def _get_current_innings(self, match_id: int) -> Optional[Innings]:
        """Get the currently active innings"""
        match = self.db.query(Match).filter(Match.id == match_id).first()
        return self._get_innings(match_id, match.current_innings)
    
    def _get_innings(self, match_id: int, innings_number: int) -> Optional[Innings]:
        """Get specific innings"""
        return (self.db.query(Innings)
                .filter(and_(Innings.match_id == match_id, 
                           Innings.innings_number == innings_number))
                .first())
    
    def _get_innings_stats(self, innings: Innings) -> InningsStats:
        """Calculate live innings statistics"""
        run_rate = float(innings.total_runs / innings.overs_completed) if innings.overs_completed > 0 else 0
        
        # Required rate calculation for 2nd innings
        required_rate = None
        balls_remaining = None
        
        if innings.innings_number == 2:
            match = innings.match
            first_innings = self._get_innings(match.id, 1)
            target = first_innings.total_runs + 1
            runs_needed = target - innings.total_runs
            
            total_balls_allowed = match.overs_per_side * 6
            balls_used = int(innings.overs_completed) * 6 + int((innings.overs_completed % 1) * 10)
            balls_remaining = total_balls_allowed - balls_used
            
            if balls_remaining > 0:
                required_rate = (runs_needed * 6) / balls_remaining
        
        return InningsStats(
            innings_id=innings.id,
            innings_number=innings.innings_number,
            batting_team=innings.batting_team.name,
            bowling_team=innings.bowling_team.name,
            total_runs=innings.total_runs,
            wickets_lost=innings.wickets_lost,
            overs_completed=f"{int(innings.overs_completed)}.{int((innings.overs_completed % 1) * 10)}",
            run_rate=round(run_rate, 2),
            required_rate=round(required_rate, 2) if required_rate else None,
            balls_remaining=balls_remaining
        )
    
    def _get_current_batsmen_stats(self, innings_id: int) -> list[BatsmanStats]:
        """Get current batsmen statistics - get the two batsmen from latest ball"""
        # Get the latest ball to find current batsmen
        latest_ball = (self.db.query(Ball)
                      .filter(Ball.innings_id == innings_id)
                      .order_by(desc(Ball.id))
                      .first())
        
        if not latest_ball:
            return []
        
        # Get stats for both batsmen
        batsmen_ids = [latest_ball.batsman_id, latest_ball.non_striker_id]
        batsmen_stats = []
        
        for batsman_id in batsmen_ids:
            if not batsman_id:  # Check for None
                continue
                
            # Query batsman stats for this innings
            stats_query = (self.db.query(
                func.sum(Ball.runs).label('runs'),
                func.count(Ball.id).filter(Ball.is_valid_ball == True).label('balls_faced'),
                func.count(Ball.id).filter(Ball.runs == 4).label('fours'),
                func.count(Ball.id).filter(Ball.runs == 6).label('sixes')
            ).filter(
                Ball.innings_id == innings_id,
                Ball.batsman_id == batsman_id
            ).first())
            
            # Get player name
            player = self.db.query(Player).filter(Player.id == batsman_id).first()
            
            if not stats_query:
                continue
                
            runs = stats_query.runs or 0
            balls_faced = stats_query.balls_faced or 0
            strike_rate = (runs / balls_faced * 100) if balls_faced > 0 else 0.0
            
            batsmen_stats.append(BatsmanStats(
                player_id=int(batsman_id),
                name=str(player.name) if player else "Unknown",
                runs=int(runs),
                balls_faced=int(balls_faced),
                fours=int(stats_query.fours or 0),
                sixes=int(stats_query.sixes or 0),
                strike_rate=round(strike_rate, 2)
            ))
        
        return batsmen_stats
    
    def _get_current_bowler_stats(self, innings_id: int) -> BowlerStats:
        """Get current bowler statistics"""
        # Simplified for MVP - implement bowler stats calculation
        return BowlerStats(
            player_id=1,
            name="Current Bowler",
            overs="2.3",
            runs_conceded=18,
            wickets=1,
            economy_rate=7.2
        )
    
    def _get_recent_balls(self, innings_id: int, limit: int = 6) -> list:
        """Get recent balls for live updates"""
        balls = (self.db.query(Ball)
                .filter(Ball.innings_id == innings_id)
                .order_by(desc(Ball.id))
                .limit(limit)
                .all())
        
        # Convert Ball objects to dictionaries for JSON serialization
        return [{
            "id": ball.id,
            "over_number": ball.over_number,
            "ball_number": ball.ball_number,
            "runs": ball.runs,
            "extras": ball.extras,
            "extra_type": ball.extra_type,
            "is_wicket": ball.is_wicket,
            "wicket_type": ball.wicket_type,
            "batsman_id": ball.batsman_id,
            "bowler_id": ball.bowler_id
        } for ball in balls]

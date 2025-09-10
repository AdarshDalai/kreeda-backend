"""
Cricket Statistics Engine
Calculates and aggregates player and team statistics
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

from app.models.cricket import CricketMatch, CricketBall, MatchPlayerStats
from app.models.user import User, Team

logger = logging.getLogger(__name__)


class CricketStatsEngine:
    """Calculate comprehensive cricket statistics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_player_career_stats(self, player_id: str) -> Dict:
        """Get comprehensive career statistics for a player"""
        try:
            # Batting statistics
            batting_query = select(
                func.count(MatchPlayerStats.match_id).label('matches_played'),
                func.sum(MatchPlayerStats.batting_runs).label('total_runs'),
                func.sum(MatchPlayerStats.balls_faced).label('total_balls'),
                func.sum(MatchPlayerStats.fours_hit).label('total_fours'),
                func.sum(MatchPlayerStats.sixes_hit).label('total_sixes'),
                func.avg(MatchPlayerStats.batting_runs).label('average'),
                func.max(MatchPlayerStats.batting_runs).label('highest_score')
            ).where(
                and_(
                    MatchPlayerStats.player_id == player_id,
                    MatchPlayerStats.balls_faced > 0  # Only count innings where player batted
                )
            )
            
            batting_result = await self.db.execute(batting_query)
            batting_stats = batting_result.first()
            
            # Bowling statistics
            bowling_query = select(
                func.sum(MatchPlayerStats.overs_bowled).label('total_overs'),
                func.sum(MatchPlayerStats.runs_conceded).label('total_runs_conceded'),
                func.sum(MatchPlayerStats.wickets_taken).label('total_wickets'),
                func.avg(MatchPlayerStats.runs_conceded / MatchPlayerStats.overs_bowled).label('economy_rate')
            ).where(
                and_(
                    MatchPlayerStats.player_id == player_id,
                    MatchPlayerStats.overs_bowled > 0  # Only count matches where player bowled
                )
            )
            
            bowling_result = await self.db.execute(bowling_query)
            bowling_stats = bowling_result.first()
            
            # Calculate derived statistics
            strike_rate = 0.0
            if batting_stats.total_balls and batting_stats.total_balls > 0:
                strike_rate = (batting_stats.total_runs / batting_stats.total_balls) * 100
            
            bowling_average = 0.0
            if bowling_stats.total_wickets and bowling_stats.total_wickets > 0:
                bowling_average = bowling_stats.total_runs_conceded / bowling_stats.total_wickets
            
            return {
                "player_id": player_id,
                "batting": {
                    "matches": batting_stats.matches_played or 0,
                    "runs": batting_stats.total_runs or 0,
                    "balls_faced": batting_stats.total_balls or 0,
                    "average": round(batting_stats.average or 0, 2),
                    "strike_rate": round(strike_rate, 2),
                    "highest_score": batting_stats.highest_score or 0,
                    "fours": batting_stats.total_fours or 0,
                    "sixes": batting_stats.total_sixes or 0
                },
                "bowling": {
                    "overs": round(bowling_stats.total_overs or 0, 1),
                    "runs_conceded": bowling_stats.total_runs_conceded or 0,
                    "wickets": bowling_stats.total_wickets or 0,
                    "average": round(bowling_average, 2),
                    "economy_rate": round(bowling_stats.economy_rate or 0, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating player stats: {e}")
            return self._empty_player_stats(player_id)
    
    async def get_team_stats(self, team_id: str, season_year: Optional[int] = None) -> Dict:
        """Get team statistics for a season or all-time"""
        try:
            # Base query for team matches
            base_query = select(CricketMatch).where(
                or_(
                    CricketMatch.team_a_id == team_id,
                    CricketMatch.team_b_id == team_id
                )
            )
            
            if season_year:
                start_date = datetime(season_year, 1, 1)
                end_date = datetime(season_year + 1, 1, 1)
                base_query = base_query.where(
                    and_(
                        CricketMatch.match_date >= start_date,
                        CricketMatch.match_date < end_date
                    )
                )
            
            result = await self.db.execute(base_query)
            matches = result.scalars().all()
            
            # Calculate team statistics
            total_matches = len(matches)
            wins = 0
            losses = 0
            total_runs_scored = 0
            total_runs_conceded = 0
            highest_score = 0
            lowest_score = float('inf')
            
            for match in matches:
                if match.status == "completed" and match.winner_team_id:
                    if str(match.winner_team_id) == str(team_id):
                        wins += 1
                    else:
                        losses += 1
                
                # Team A stats
                if str(match.team_a_id) == str(team_id):
                    team_score = match.team_a_score
                    opponent_score = match.team_b_score
                else:
                    team_score = match.team_b_score
                    opponent_score = match.team_a_score
                
                total_runs_scored += team_score
                total_runs_conceded += opponent_score
                
                if team_score > highest_score:
                    highest_score = team_score
                if team_score < lowest_score and team_score > 0:
                    lowest_score = team_score
            
            win_percentage = (wins / total_matches * 100) if total_matches > 0 else 0
            average_score = total_runs_scored / total_matches if total_matches > 0 else 0
            
            return {
                "team_id": team_id,
                "season_year": season_year,
                "matches_played": total_matches,
                "wins": wins,
                "losses": losses,
                "win_percentage": round(win_percentage, 1),
                "total_runs_scored": total_runs_scored,
                "total_runs_conceded": total_runs_conceded,
                "average_score": round(average_score, 1),
                "highest_score": highest_score,
                "lowest_score": lowest_score if lowest_score != float('inf') else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating team stats: {e}")
            return self._empty_team_stats(team_id)
    
    async def get_recent_form(self, team_id: str, last_n_matches: int = 5) -> Dict:
        """Get recent form for a team"""
        try:
            recent_matches_query = select(CricketMatch).where(
                and_(
                    or_(
                        CricketMatch.team_a_id == team_id,
                        CricketMatch.team_b_id == team_id
                    ),
                    CricketMatch.status == "completed"
                )
            ).order_by(CricketMatch.match_date.desc()).limit(last_n_matches)
            
            result = await self.db.execute(recent_matches_query)
            matches = result.scalars().all()
            
            form_string = ""
            recent_wins = 0
            
            for match in matches:
                if match.winner_team_id:
                    if str(match.winner_team_id) == str(team_id):
                        form_string += "W"
                        recent_wins += 1
                    else:
                        form_string += "L"
                else:
                    form_string += "D"  # Draw/No result
            
            return {
                "team_id": team_id,
                "last_matches": len(matches),
                "form_string": form_string,
                "recent_wins": recent_wins,
                "recent_win_percentage": (recent_wins / len(matches) * 100) if matches else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating recent form: {e}")
            return {"team_id": team_id, "form_string": "", "recent_wins": 0}
    
    async def get_match_insights(self, match_id: str) -> Dict:
        """Get detailed insights for a specific match"""
        try:
            # Get match details
            match_query = select(CricketMatch).where(CricketMatch.id == match_id)
            match_result = await self.db.execute(match_query)
            match = match_result.scalar_one_or_none()
            
            if not match:
                return {"error": "Match not found"}
            
            # Get ball-by-ball data
            balls_query = select(CricketBall).where(
                CricketBall.match_id == match_id
            ).order_by(CricketBall.created_at)
            
            balls_result = await self.db.execute(balls_query)
            balls = balls_result.scalars().all()
            
            # Calculate insights
            total_balls = len(balls)
            boundaries = sum(1 for ball in balls if getattr(ball, 'is_boundary', False))
            sixes = sum(1 for ball in balls if getattr(ball, 'runs_scored', 0) == 6)
            fours = boundaries - sixes
            wickets = sum(1 for ball in balls if getattr(ball, 'is_wicket', False))
            dots = sum(1 for ball in balls if getattr(ball, 'runs_scored', 0) == 0 and getattr(ball, 'extras', 0) == 0)
            
            # Run rate progression (every 5 overs)
            run_rate_progression = []
            current_runs = 0
            current_balls = 0
            
            for i, ball in enumerate(balls, 1):
                current_runs += getattr(ball, 'runs_scored', 0) + getattr(ball, 'extras', 0)
                if getattr(ball, 'ball_type', '') == 'legal':
                    current_balls += 1
                
                if current_balls % 30 == 0:  # Every 5 overs
                    overs = current_balls / 6
                    run_rate = current_runs / overs if overs > 0 else 0
                    run_rate_progression.append({
                        "over": int(overs),
                        "runs": current_runs,
                        "run_rate": round(run_rate, 2)
                    })
            
            return {
                "match_id": match_id,
                "total_balls": total_balls,
                "boundaries": boundaries,
                "fours": fours,
                "sixes": sixes,
                "wickets": wickets,
                "dot_balls": dots,
                "dot_percentage": round((dots / total_balls * 100) if total_balls > 0 else 0, 1),
                "boundary_percentage": round((boundaries / total_balls * 100) if total_balls > 0 else 0, 1),
                "run_rate_progression": run_rate_progression
            }
            
        except Exception as e:
            logger.error(f"Error calculating match insights: {e}")
            return {"error": str(e)}
    
    def _empty_player_stats(self, player_id: str) -> Dict:
        """Return empty player statistics structure"""
        return {
            "player_id": player_id,
            "batting": {
                "matches": 0, "runs": 0, "balls_faced": 0,
                "average": 0.0, "strike_rate": 0.0, "highest_score": 0,
                "fours": 0, "sixes": 0
            },
            "bowling": {
                "overs": 0.0, "runs_conceded": 0, "wickets": 0,
                "average": 0.0, "economy_rate": 0.0
            }
        }
    
    def _empty_team_stats(self, team_id: str) -> Dict:
        """Return empty team statistics structure"""
        return {
            "team_id": team_id,
            "matches_played": 0, "wins": 0, "losses": 0,
            "win_percentage": 0.0, "total_runs_scored": 0,
            "total_runs_conceded": 0, "average_score": 0.0,
            "highest_score": 0, "lowest_score": 0
        }

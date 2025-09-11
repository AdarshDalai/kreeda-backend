"""
Cricket Statistics Engine
Calculates and aggregates player and team statistics
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.orm import selectinload
from typing import Dict, List, Optional, Union, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.models.cricket import CricketMatch, CricketBall, MatchPlayerStats
from app.models.user import User, Team

logger = logging.getLogger(__name__)


class StatsPeriod(Enum):
    """Time period for statistics calculation"""
    ALL_TIME = "all_time"
    CURRENT_SEASON = "current_season"
    LAST_12_MONTHS = "last_12_months"
    LAST_6_MONTHS = "last_6_months"


@dataclass
class BattingStats:
    """Structured batting statistics"""
    matches: int = 0
    runs: int = 0
    balls_faced: int = 0
    average: float = 0.0
    strike_rate: float = 0.0
    highest_score: int = 0
    fours: int = 0
    sixes: int = 0
    centuries: int = 0
    half_centuries: int = 0
    not_outs: int = 0


@dataclass
class BowlingStats:
    """Structured bowling statistics"""
    matches: int = 0
    overs: float = 0.0
    runs_conceded: int = 0
    wickets: int = 0
    average: float = 0.0
    economy_rate: float = 0.0
    strike_rate: float = 0.0
    best_bowling: str = "0/0"
    five_wickets: int = 0
    maiden_overs: int = 0


@dataclass
class FieldingStats:
    """Structured fielding statistics"""
    catches: int = 0
    stumpings: int = 0
    run_outs: int = 0
    total_dismissals: int = 0


class StatsCalculationError(Exception):
    """Custom exception for statistics calculation errors"""
    pass


class CricketStatsEngine:
    """Calculate comprehensive cricket statistics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache = {}  # Simple in-memory cache
    
    async def get_player_career_stats(
        self, 
        player_id: str, 
        period: StatsPeriod = StatsPeriod.ALL_TIME,
        tournament_id: Optional[str] = None
    ) -> Dict:
        """Get comprehensive career statistics for a player"""
        if not player_id:
            raise ValueError("Player ID cannot be empty")
        
        cache_key = f"player_stats_{player_id}_{period.value}_{tournament_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Return empty stats for now since integrity tables might not exist
            batting_stats = BattingStats()
            bowling_stats = BowlingStats()
            fielding_stats = FieldingStats()
            
            result = {
                "player_id": player_id,
                "period": period.value,
                "last_updated": datetime.utcnow().isoformat(),
                "batting": {
                    "matches": batting_stats.matches,
                    "runs": batting_stats.runs,
                    "balls_faced": batting_stats.balls_faced,
                    "average": batting_stats.average,
                    "strike_rate": batting_stats.strike_rate,
                    "highest_score": batting_stats.highest_score,
                    "fours": batting_stats.fours,
                    "sixes": batting_stats.sixes,
                    "centuries": batting_stats.centuries,
                    "half_centuries": batting_stats.half_centuries,
                    "not_outs": batting_stats.not_outs
                },
                "bowling": {
                    "matches": bowling_stats.matches,
                    "overs": bowling_stats.overs,
                    "runs_conceded": bowling_stats.runs_conceded,
                    "wickets": bowling_stats.wickets,
                    "average": bowling_stats.average,
                    "economy_rate": bowling_stats.economy_rate,
                    "strike_rate": bowling_stats.strike_rate,
                    "best_bowling": bowling_stats.best_bowling,
                    "five_wickets": bowling_stats.five_wickets,
                    "maiden_overs": bowling_stats.maiden_overs
                },
                "fielding": {
                    "catches": fielding_stats.catches,
                    "stumpings": fielding_stats.stumpings,
                    "run_outs": fielding_stats.run_outs,
                    "total_dismissals": fielding_stats.total_dismissals
                }
            }
            
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error calculating player stats for {player_id}: {e}")
            # Return empty stats if there's an error
            return {
                "player_id": player_id,
                "period": period.value,
                "last_updated": datetime.utcnow().isoformat(),
                "batting": {},
                "bowling": {},
                "fielding": {},
                "error": "Statistics calculation temporarily unavailable"
            }
                func.sum(MatchPlayerStats.balls_faced).label('total_balls'),
                func.sum(MatchPlayerStats.fours_hit).label('total_fours'),
                func.sum(MatchPlayerStats.sixes_hit).label('total_sixes'),
                func.avg(MatchPlayerStats.batting_runs).label('average'),
                func.max(MatchPlayerStats.batting_runs).label('highest_score'),
                func.sum(case((MatchPlayerStats.batting_runs >= 100, 1), else_=0)).label('centuries'),
                func.sum(case((and_(MatchPlayerStats.batting_runs >= 50, MatchPlayerStats.batting_runs < 100), 1), else_=0)).label('half_centuries'),
                func.sum(case((MatchPlayerStats.is_not_out == True, 1), else_=0)).label('not_outs')
            ).select_from(
                MatchPlayerStats.__table__.join(CricketMatch.__table__)
            ).where(
                and_(
                    MatchPlayerStats.player_id == player_id,
                    MatchPlayerStats.balls_faced > 0,
                    *date_filter
                )
            )
            
            if tournament_id:
                batting_query = batting_query.where(CricketMatch.tournament_id == tournament_id)
            
            batting_result = await self.db.execute(batting_query)
            batting_data = batting_result.first()
            
            # Enhanced bowling statistics
            bowling_query = select(
                func.count(MatchPlayerStats.match_id).label('matches_bowled'),
                func.sum(MatchPlayerStats.overs_bowled).label('total_overs'),
                func.sum(MatchPlayerStats.runs_conceded).label('total_runs_conceded'),
                func.sum(MatchPlayerStats.wickets_taken).label('total_wickets'),
                func.sum(MatchPlayerStats.maiden_overs).label('maiden_overs'),
                func.sum(case((MatchPlayerStats.wickets_taken >= 5, 1), else_=0)).label('five_wickets'),
                func.max(MatchPlayerStats.wickets_taken).label('best_wickets')
            ).select_from(
                MatchPlayerStats.__table__.join(CricketMatch.__table__)
            ).where(
                and_(
                    MatchPlayerStats.player_id == player_id,
                    MatchPlayerStats.overs_bowled > 0,
                    *date_filter
                )
            )
            
            if tournament_id:
                bowling_query = bowling_query.where(CricketMatch.tournament_id == tournament_id)
            
            bowling_result = await self.db.execute(bowling_query)
            bowling_data = bowling_result.first()
            
            # Fielding statistics
            fielding_query = select(
                func.sum(MatchPlayerStats.catches).label('total_catches'),
                func.sum(MatchPlayerStats.stumpings).label('total_stumpings'),
                func.sum(MatchPlayerStats.run_outs).label('total_run_outs')
            ).select_from(
                MatchPlayerStats.__table__.join(CricketMatch.__table__)
            ).where(
                and_(
                    MatchPlayerStats.player_id == player_id,
                    *date_filter
                )
            )
            
            if tournament_id:
                fielding_query = fielding_query.where(CricketMatch.tournament_id == tournament_id)
            
            fielding_result = await self.db.execute(fielding_query)
            fielding_data = fielding_result.first()
            
            # Calculate derived statistics
            batting_stats = self._calculate_batting_stats(batting_data)
            bowling_stats = self._calculate_bowling_stats(bowling_data)
            fielding_stats = self._calculate_fielding_stats(fielding_data)
            
            result = {
                "player_id": player_id,
                "period": period.value,
                "tournament_id": tournament_id,
                "batting": batting_stats.__dict__,
                "bowling": bowling_stats.__dict__,
                "fielding": fielding_stats.__dict__,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Cache the result for 5 minutes
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error calculating player stats for {player_id}: {e}")
            raise StatsCalculationError(f"Failed to calculate player stats: {str(e)}")
    
    async def get_team_stats(
        self, 
        team_id: str, 
        period: StatsPeriod = StatsPeriod.ALL_TIME,
        tournament_id: Optional[str] = None
    ) -> Dict:
        """Get comprehensive team statistics"""
        if not team_id:
            raise ValueError("Team ID cannot be empty")
        
        try:
            # Get basic team matches
            base_query = select(CricketMatch).where(
                or_(
                    CricketMatch.team_a_id == team_id,
                    CricketMatch.team_b_id == team_id
                )
            )
            
            result = await self.db.execute(base_query)
            matches = result.scalars().all()
            
            # Simple team statistics
            total_matches = len(matches)
            wins = 0
            total_runs_scored = 0
            total_runs_conceded = 0
            
            for match in matches:
                # Calculate basic stats
                if match.winner_team_id == team_id:
                    wins += 1
                
                # Add runs scored and conceded
                if str(match.team_a_id) == str(team_id):
                    total_runs_scored += match.team_a_score or 0
                    total_runs_conceded += match.team_b_score or 0
                else:
                    total_runs_scored += match.team_b_score or 0
                    total_runs_conceded += match.team_a_score or 0
            
            win_percentage = (wins / total_matches * 100) if total_matches > 0 else 0
            avg_score = total_runs_scored / total_matches if total_matches > 0 else 0
            avg_conceded = total_runs_conceded / total_matches if total_matches > 0 else 0
            
            stats = {
                "team_id": team_id,
                "period": period.value,
                "total_matches": total_matches,
                "wins": wins,
                "losses": total_matches - wins,
                "win_percentage": round(win_percentage, 2),
                "average_score": round(avg_score, 2),
                "average_conceded": round(avg_conceded, 2),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating team stats for {team_id}: {e}")
            return {
                "team_id": team_id,
                "period": period.value,
                "error": "Team statistics temporarily unavailable",
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def compare_players(
        self, 
        player_ids: List[str], 
        period: StatsPeriod = StatsPeriod.ALL_TIME
    ) -> Dict:
        """Compare statistics between multiple players"""
        if len(player_ids) < 2:
            raise ValueError("At least 2 players required for comparison")
        
        try:
            comparisons = {}
            for player_id in player_ids:
                player_stats = await self.get_player_career_stats(player_id, period)
                comparisons[player_id] = player_stats
            
            # Calculate comparison metrics
            best_batsman = max(comparisons.items(), key=lambda x: x[1]["batting"]["average"])
            best_bowler = min(
                [(pid, stats) for pid, stats in comparisons.items() if stats["bowling"]["wickets"] > 0],
                key=lambda x: x[1]["bowling"]["average"],
                default=(None, None)
            )
            
            return {
                "players": comparisons,
                "comparison_summary": {
                    "best_batsman": {
                        "player_id": best_batsman[0],
                        "average": best_batsman[1]["batting"]["average"]
                    },
                    "best_bowler": {
                        "player_id": best_bowler[0] if best_bowler[0] else None,
                        "average": best_bowler[1]["bowling"]["average"] if best_bowler[1] else None
                    }
                },
                "period": period.value
            }
            
        except Exception as e:
            logger.error(f"Error comparing players: {e}")
            raise StatsCalculationError(f"Failed to compare players: {str(e)}")
    
    async def get_recent_form(self, team_id: str, last_n_matches: int = 5) -> Dict:
        """Get recent form for a team with enhanced metrics"""
        if not team_id or last_n_matches <= 0:
            raise ValueError("Invalid team ID or match count")
        
        try:
            recent_matches_query = select(CricketMatch).where(
                or_(
                    CricketMatch.team_a_id == team_id,
                    CricketMatch.team_b_id == team_id
                )
            ).order_by(CricketMatch.created_at.desc()).limit(last_n_matches)
            
            result = await self.db.execute(recent_matches_query)
            matches = result.scalars().all()
            
            form_string = ""
            recent_wins = 0
            total_runs_scored = 0
            total_runs_conceded = 0
            match_results = []
            
            for match in matches:
                # Simple form analysis
                team_score = 0
                opponent_score = 0
                
                if str(match.team_a_id) == str(team_id):
                    team_score = match.team_a_score or 0
                    opponent_score = match.team_b_score or 0
                else:
                    team_score = match.team_b_score or 0
                    opponent_score = match.team_a_score or 0
                
                # Determine result
                if match.winner_team_id and str(match.winner_team_id) == str(team_id):
                    form_string += "W"
                    recent_wins += 1
                    result = "win"
                elif match.winner_team_id:
                    form_string += "L"
                    result = "loss"
                else:
                    form_string += "T"  # Tie or no result
                    result = "tie"
                
                total_runs_scored += team_score
                total_runs_conceded += opponent_score
                
                match_results.append({
                    "match_id": str(match.id),
                    "result": result,
                    "team_score": team_score,
                    "opponent_score": opponent_score,
                    "match_date": match.match_date.isoformat() if match.match_date else None
                })
            
            # Calculate averages
            matches_count = len(matches)
            average_score = total_runs_scored / matches_count if matches_count > 0 else 0
            average_conceded = total_runs_conceded / matches_count if matches_count > 0 else 0
            win_percentage = (recent_wins / matches_count * 100) if matches_count > 0 else 0
            
            return {
                "team_id": team_id,
                "last_n_matches": last_n_matches,
                "matches_analyzed": matches_count,
                "form_string": form_string,
                "wins": recent_wins,
                "losses": matches_count - recent_wins,
                "win_percentage": round(win_percentage, 2),
                "average_score": round(average_score, 2),
                "average_conceded": round(average_conceded, 2),
                "net_run_rate": round(average_score - average_conceded, 2),
                "recent_matches": match_results,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating recent form for {team_id}: {e}")
            return {
                "team_id": team_id,
                "error": "Team form temporarily unavailable",
                "last_updated": datetime.utcnow().isoformat()
            }
                    team_score = match.team_a_score
                    opponent_score = match.team_b_score
                else:
                    team_score = match.team_b_score
                    opponent_score = match.team_a_score
                
                total_runs_scored += team_score
                total_runs_conceded += opponent_score
                
                if match.winner_team_id is not None:
                    if str(match.winner_team_id) == str(team_id):
                        form_string += "W"
                        recent_wins += 1
                    else:
                        form_string += "L"
                else:
                    form_string += "D"
            
            avg_score = total_runs_scored / len(matches) if matches else 0
            avg_conceded = total_runs_conceded / len(matches) if matches else 0

            # Ensure values are plain floats (not SQLAlchemy ColumnElement)
            from sqlalchemy.sql.elements import ColumnElement

            def safe_float(val):
                if isinstance(val, ColumnElement):
                    return 0.0
                try:
                    return float(val)
                except Exception:
                    return 0.0

            average_score_val = safe_float(avg_score)
            average_conceded_val = safe_float(avg_conceded)

            return {
                "team_id": team_id,
                "last_matches": len(matches),
                "form_string": form_string,
                "recent_wins": recent_wins,
                "recent_win_percentage": round((recent_wins / len(matches) * 100) if matches else 0, 1),
                "average_score": round(average_score_val, 1),
                "average_conceded": round(average_conceded_val, 1),
                "net_run_rate": round(average_score_val - average_conceded_val, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating recent form for {team_id}: {e}")
            raise StatsCalculationError(f"Failed to calculate recent form: {str(e)}")
    
    async def get_match_insights(self, match_id: str) -> Dict:
        """Get detailed insights for a specific match with enhanced analytics"""
        if not match_id:
            raise ValueError("Match ID cannot be empty")
        
        try:
            # Get match details
            match_query = select(CricketMatch).where(CricketMatch.id == match_id)
            match_result = await self.db.execute(match_query)
            match = match_result.scalar_one_or_none()
            
            if not match:
                return {"error": "Match not found"}
            
            # Get basic match data and provide insights
            insights = {
                "match_id": match_id,
                "status": match.status,
                "current_innings": match.current_innings,
                "team_a_score": match.team_a_score,
                "team_a_wickets": match.team_a_wickets,
                "team_a_overs": match.team_a_overs,
                "team_b_score": match.team_b_score,
                "team_b_wickets": match.team_b_wickets,
                "team_b_overs": match.team_b_overs,
                "current_run_rate": match.current_run_rate,
                "required_run_rate": match.required_run_rate,
                "total_runs": (match.team_a_score or 0) + (match.team_b_score or 0),
                "total_wickets": (match.team_a_wickets or 0) + (match.team_b_wickets or 0),
                "analysis": "Basic match statistics available",
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error calculating match insights for {match_id}: {e}")
            return {
                "match_id": match_id,
                "error": "Match insights temporarily unavailable",
                "last_updated": datetime.utcnow().isoformat()
            }
    
    def _get_date_filter(self, period: StatsPeriod) -> List:
        """Get date filter conditions based on period"""
        if period == StatsPeriod.ALL_TIME:
            return []
        
        now = datetime.utcnow()
        if period == StatsPeriod.CURRENT_SEASON:
            start_date = datetime(now.year, 1, 1)
        elif period == StatsPeriod.LAST_12_MONTHS:
            start_date = now - timedelta(days=365)
        elif period == StatsPeriod.LAST_6_MONTHS:
            start_date = now - timedelta(days=180)
        else:
            return []
        
        return [CricketMatch.match_date >= start_date]
    
    def _calculate_batting_stats(self, batting_data) -> BattingStats:
        """Calculate batting statistics from query result"""
        if not batting_data or not batting_data.total_runs:
            return BattingStats()
        
        strike_rate = 0.0
        if batting_data.total_balls and batting_data.total_balls > 0:
            strike_rate = (batting_data.total_runs / batting_data.total_balls) * 100
        
        actual_average = 0.0
        if batting_data.matches_played and batting_data.not_outs is not None:
            innings = batting_data.matches_played - batting_data.not_outs
            if innings > 0:
                actual_average = batting_data.total_runs / innings
        
        return BattingStats(
            matches=batting_data.matches_played or 0,
            runs=batting_data.total_runs or 0,
            balls_faced=batting_data.total_balls or 0,
            average=round(actual_average, 2),
            strike_rate=round(strike_rate, 2),
            highest_score=batting_data.highest_score or 0,
            fours=batting_data.total_fours or 0,
            sixes=batting_data.total_sixes or 0,
            centuries=batting_data.centuries or 0,
            half_centuries=batting_data.half_centuries or 0,
            not_outs=batting_data.not_outs or 0
        )
    
    def _calculate_bowling_stats(self, bowling_data) -> BowlingStats:
        """Calculate bowling statistics from query result"""
        if not bowling_data or not bowling_data.total_overs:
            return BowlingStats()
        
        bowling_average = 0.0
        if bowling_data.total_wickets and bowling_data.total_wickets > 0:
            bowling_average = bowling_data.total_runs_conceded / bowling_data.total_wickets
        
        economy_rate = 0.0
        bowling_strike_rate = 0.0
        if bowling_data.total_overs and bowling_data.total_overs > 0:
            economy_rate = bowling_data.total_runs_conceded / bowling_data.total_overs
            if bowling_data.total_wickets and bowling_data.total_wickets > 0:
                bowling_strike_rate = (bowling_data.total_overs * 6) / bowling_data.total_wickets
        
        best_bowling = f"{bowling_data.best_wickets or 0}/{bowling_data.total_runs_conceded or 0}"
        
        return BowlingStats(
            matches=bowling_data.matches_bowled or 0,
            overs=round(bowling_data.total_overs or 0, 1),
            runs_conceded=bowling_data.total_runs_conceded or 0,
            wickets=bowling_data.total_wickets or 0,
            average=round(bowling_average, 2),
            economy_rate=round(economy_rate, 2),
            strike_rate=round(bowling_strike_rate, 2),
            best_bowling=best_bowling,
            five_wickets=bowling_data.five_wickets or 0,
            maiden_overs=bowling_data.maiden_overs or 0
        )
    
    def _calculate_fielding_stats(self, fielding_data) -> FieldingStats:
        """Calculate fielding statistics from query result"""
        if not fielding_data:
            return FieldingStats()
        
        catches = fielding_data.total_catches or 0
        stumpings = fielding_data.total_stumpings or 0
        run_outs = fielding_data.total_run_outs or 0
        
        return FieldingStats(
            catches=catches,
            stumpings=stumpings,
            run_outs=run_outs,
            total_dismissals=catches + stumpings + run_outs
        )
    
    def _calculate_team_stats(self, team_id: str, matches: List[CricketMatch]) -> Dict:
        """Calculate comprehensive team statistics"""
        total_matches = len(matches)
        wins = losses = draws = 0
        total_runs_scored = total_runs_conceded = 0
        highest_score = lowest_score = 0
        biggest_win_margin = biggest_loss_margin = 0
        
        if total_matches > 0:
            lowest_score = float('inf')
        
        for match in matches:
            # Determine team scores
            if str(match.team_a_id) == str(team_id):
                team_score = match.team_a_score
                opponent_score = match.team_b_score
            else:
                team_score = match.team_b_score
                opponent_score = match.team_a_score
            
            total_runs_scored += team_score
            total_runs_conceded += opponent_score
            
            # Track score extremes
            team_score_value = int(team_score) if isinstance(team_score, (int, float, str)) and team_score is not None else 0
            if team_score_value > highest_score:
                highest_score = team_score_value
            if team_score_value < lowest_score and team_score_value > 0:
                lowest_score = team_score_value
            
            # Determine result and margins
            if match.winner_team_id is not None:
                if str(match.winner_team_id) == str(team_id):
                    wins += 1
                    # Ensure team_score and opponent_score are actual numbers, not SQLAlchemy columns
                    team_score_value = float(team_score) if isinstance(team_score, (int, float, str)) and team_score is not None else 0
                    opponent_score_value = float(opponent_score) if isinstance(opponent_score, (int, float, str)) and opponent_score is not None else 0
                    margin = team_score_value - opponent_score_value
                    if margin > biggest_win_margin:
                        biggest_win_margin = margin
                else:
                    losses += 1
                    opponent_score_value = float(opponent_score) if isinstance(opponent_score, (int, float, str)) and opponent_score is not None else 0
                    team_score_value = float(team_score) if isinstance(team_score, (int, float, str)) and team_score is not None else 0
                    margin = opponent_score_value - team_score_value
                    if margin > biggest_loss_margin:
                        biggest_loss_margin = margin
            else:
                draws += 1
        
        # Calculate percentages and averages
        win_percentage = (wins / total_matches * 100) if total_matches > 0 else 0
        average_score = total_runs_scored / total_matches if total_matches > 0 else 0
        average_conceded = total_runs_conceded / total_matches if total_matches > 0 else 0

        # Ensure values are plain floats (not SQLAlchemy ColumnElement)
        from sqlalchemy.sql.elements import ColumnElement

        def safe_float(val):
            if isinstance(val, ColumnElement):
                return 0.0
            try:
                return float(val)
            except Exception:
                return 0.0

        average_score_val = safe_float(average_score)
        average_conceded_val = safe_float(average_conceded)

        return {
            "team_id": team_id,
            "matches_played": total_matches,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_percentage": round(win_percentage, 1),
            "total_runs_scored": total_runs_scored,
            "total_runs_conceded": total_runs_conceded,
            "average_score": round(average_score_val, 1),
            "average_conceded": round(average_conceded_val, 1),
            "net_run_rate": round(average_score_val - average_conceded_val, 2),
            "highest_score": highest_score,
            "lowest_score": lowest_score if lowest_score != float('inf') else 0,
            "biggest_win_margin": biggest_win_margin,
            "biggest_loss_margin": biggest_loss_margin
        }
    
    async def _get_performance_trend(self, team_id: str, period: StatsPeriod) -> List[Dict]:
        """Calculate performance trend over time"""
        # Implementation for performance trend calculation
        # This would analyze wins/losses over time periods
        return []
    
    def _calculate_match_insights(self, match: CricketMatch, balls: List[CricketBall]) -> Dict:
        """Calculate detailed match insights"""
        total_balls = len(balls)
        if total_balls == 0:
            return {"match_id": str(match.id), "error": "No ball data available"}
        
        # Enhanced analytics
        boundaries = sum(1 for ball in balls if getattr(ball, 'is_boundary', False))
        sixes = sum(1 for ball in balls if getattr(ball, 'runs_scored', 0) == 6)
        fours = boundaries - sixes
        wickets = sum(1 for ball in balls if getattr(ball, 'is_wicket', False))
        dots = sum(1 for ball in balls if getattr(ball, 'runs_scored', 0) == 0 and getattr(ball, 'extras', 0) == 0)
        wides = sum(1 for ball in balls if getattr(ball, 'ball_type', '') == 'wide')
        no_balls = sum(1 for ball in balls if getattr(ball, 'ball_type', '') == 'no_ball')
        
        # Innings-wise breakdown
        innings_breakdown = {}
        for ball in balls:
            innings = getattr(ball, 'innings', 1)
            if innings not in innings_breakdown:
                innings_breakdown[innings] = {'runs': 0, 'wickets': 0, 'balls': 0}
            
            innings_breakdown[innings]['runs'] += getattr(ball, 'runs_scored', 0) + getattr(ball, 'extras', 0)
            innings_breakdown[innings]['balls'] += 1
            if getattr(ball, 'is_wicket', False):
                innings_breakdown[innings]['wickets'] += 1
        
        # Power play analysis (first 6 overs)
        powerplay_runs = 0
        powerplay_wickets = 0
        powerplay_balls = 0
        
        for ball in balls:
            over_num = getattr(ball, 'over_number', 0)
            if over_num <= 6:
                powerplay_runs += getattr(ball, 'runs_scored', 0) + getattr(ball, 'extras', 0)
                powerplay_balls += 1
                if getattr(ball, 'is_wicket', False):
                    powerplay_wickets += 1
        
        return {
            "match_id": str(match.id),
            "match_summary": {
                "team_a": str(match.team_a_id),
                "team_b": str(match.team_b_id),
                "team_a_score": match.team_a_score,
                "team_b_score": match.team_b_score,
                "winner": str(match.winner_team_id) if match.winner_team_id is not None else None,
                "match_date": match.match_date.isoformat() if match.match_date is not None else None
            },
            "ball_analysis": {
                "total_balls": total_balls,
                "boundaries": boundaries,
                "fours": fours,
                "sixes": sixes,
                "wickets": wickets,
                "dot_balls": dots,
                "wides": wides,
                "no_balls": no_balls,
                "dot_percentage": round((dots / total_balls * 100) if total_balls > 0 else 0, 1),
                "boundary_percentage": round((boundaries / total_balls * 100) if total_balls > 0 else 0, 1)
            },
            "innings_breakdown": innings_breakdown,
            "powerplay_analysis": {
                "runs": powerplay_runs,
                "wickets": powerplay_wickets,
                "balls": powerplay_balls,
                "run_rate": round((powerplay_runs / (powerplay_balls / 6)) if powerplay_balls > 0 else 0, 2)
            }
        }
    
    def clear_cache(self):
        """Clear the statistics cache"""
        self._cache.clear()
    
    def _empty_player_stats(self, player_id: str) -> Dict:
        """Return empty player statistics structure"""
        return {
            "player_id": player_id,
            "batting": BattingStats().__dict__,
            "bowling": BowlingStats().__dict__,
            "fielding": FieldingStats().__dict__
        }
    
    def _empty_team_stats(self, team_id: str) -> Dict:
        """Return empty team statistics structure"""
        return {
            "team_id": team_id,
            "matches_played": 0, "wins": 0, "losses": 0, "draws": 0,
            "win_percentage": 0.0, "total_runs_scored": 0,
            "total_runs_conceded": 0, "average_score": 0.0,
            "average_conceded": 0.0, "net_run_rate": 0.0,
            "highest_score": 0, "lowest_score": 0,
            "biggest_win_margin": 0, "biggest_loss_margin": 0
        }

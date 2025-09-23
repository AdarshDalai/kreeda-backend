"""
Simplified Statistics service for player and team analytics
Provides core analytics functionality with database-driven calculations
"""
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cricket import CricketMatch, MatchPlayerStats
from app.models.statistics import (
    PlayerCareerStats,
    PlayerMatchPerformance,
    TeamSeasonStats,
    Leaderboard,
)
from app.models.tournament import Tournament
from app.models.user import Team, User
from app.utils.error_handler import (
    APIError,
    ValidationError,
    InternalServerError,
)

logger = logging.getLogger(__name__)


class StatisticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_player_career_stats(self, user_id: str) -> Optional[PlayerCareerStats]:
        """Get comprehensive career statistics for a player"""
        try:
            # Convert string user_id to UUID
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                # Invalid UUID format, return None (user not found)
                return None
                
            result = await self.db.execute(
                select(PlayerCareerStats)
                .options(selectinload(PlayerCareerStats.user))
                .where(PlayerCareerStats.user_id == user_uuid)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting career stats for user {user_id}: {e}")
            raise InternalServerError("get career stats")

    async def create_initial_career_stats(self, user_id: str) -> PlayerCareerStats:
        """Create initial career statistics for a new player"""
        try:
            # Convert string user_id to UUID
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                raise ValidationError("user_id", "Invalid UUID format")
                
            career_stats = PlayerCareerStats(user_id=user_uuid)
            self.db.add(career_stats)
            await self.db.commit()
            await self.db.refresh(career_stats)
            return career_stats
        except Exception as e:
            logger.error(f"Error creating career stats: {e}")
            await self.db.rollback()
            raise InternalServerError("create career stats")

    async def calculate_career_stats_from_matches(self, user_id: str) -> Dict[str, Any]:
        """Calculate career statistics directly from match data using SQL aggregation"""
        try:
            # Use raw SQL for reliable aggregation with correct column names
            query = text("""
                WITH player_matches AS (
                    SELECT 
                        mp.batting_runs,
                        mp.balls_faced,
                        mp.fours_hit,
                        mp.sixes_hit,
                        mp.wickets_taken,
                        mp.overs_bowled,
                        mp.runs_conceded,
                        mp.is_out,
                        CASE WHEN mp.batting_runs IS NOT NULL THEN 1 ELSE 0 END as batted,
                        CASE WHEN mp.wickets_taken IS NOT NULL THEN 1 ELSE 0 END as bowled
                    FROM match_player_stats mp
                    JOIN cricket_matches cm ON mp.match_id = cm.id
                    WHERE mp.player_id = :user_id
                    AND cm.status = 'completed'
                )
                SELECT 
                    COUNT(*) as total_matches,
                    SUM(CASE WHEN batted = 1 THEN 1 ELSE 0 END) as innings_batted,
                    COALESCE(SUM(batting_runs), 0) as total_runs,
                    COALESCE(MAX(batting_runs), 0) as highest_score,
                    COALESCE(SUM(balls_faced), 0) as total_balls_faced,
                    COALESCE(SUM(fours_hit), 0) as total_fours,
                    COALESCE(SUM(sixes_hit), 0) as total_sixes,
                    SUM(CASE WHEN is_out = true THEN 1 ELSE 0 END) as times_out,
                    SUM(CASE WHEN batted = 1 AND is_out = false THEN 1 ELSE 0 END) as times_not_out,
                    SUM(CASE WHEN bowled = 1 THEN 1 ELSE 0 END) as innings_bowled,
                    COALESCE(SUM(overs_bowled), 0) as total_overs_bowled,
                    COALESCE(SUM(runs_conceded), 0) as total_runs_conceded,
                    COALESCE(SUM(wickets_taken), 0) as total_wickets
                FROM player_matches
            """)
            
            result = await self.db.execute(query, {"user_id": user_id})
            row = result.fetchone()
            
            if not row:
                return {}
            
            # Calculate derived statistics
            stats = dict(row._mapping)
            
            # Batting average
            if stats['times_out'] > 0:
                stats['batting_average'] = round(stats['total_runs'] / stats['times_out'], 2)
            else:
                stats['batting_average'] = 0
            
            # Strike rate
            if stats['total_balls_faced'] > 0:
                stats['batting_strike_rate'] = round((stats['total_runs'] / stats['total_balls_faced']) * 100, 2)
            else:
                stats['batting_strike_rate'] = 0
            
            # Bowling average
            if stats['total_wickets'] > 0:
                stats['bowling_average'] = round(stats['total_runs_conceded'] / stats['total_wickets'], 2)
            else:
                stats['bowling_average'] = 0
            
            # Economy rate
            if stats['total_overs_bowled'] > 0:
                stats['bowling_economy_rate'] = round(stats['total_runs_conceded'] / float(stats['total_overs_bowled']), 2)
            else:
                stats['bowling_economy_rate'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating career stats: {e}")
            raise InternalServerError("calculate career stats")

    async def get_leaderboard_data(
        self, 
        category: str, 
        limit: int = 20,
        min_matches: int = 5
    ) -> List[Dict[str, Any]]:
        """Get leaderboard data using direct SQL queries"""
        try:
            if category == "batting_avg":
                query = text("""
                    WITH player_stats AS (
                        SELECT 
                            u.id as user_id,
                            u.full_name as name,
                            COUNT(*) as matches,
                            SUM(mp.batting_runs) as total_runs,
                            SUM(CASE WHEN mp.is_out = true THEN 1 ELSE 0 END) as dismissals
                        FROM users u
                        JOIN match_player_stats mp ON u.id = mp.player_id
                        JOIN cricket_matches cm ON mp.match_id = cm.id
                        WHERE cm.status = 'completed'
                        GROUP BY u.id, u.full_name
                        HAVING COUNT(*) >= :min_matches AND SUM(CASE WHEN mp.is_out = true THEN 1 ELSE 0 END) > 0
                    )
                    SELECT 
                        user_id,
                        name,
                        matches,
                        total_runs,
                        dismissals,
                        CASE 
                            WHEN dismissals > 0 THEN ROUND(CAST(total_runs AS FLOAT) / dismissals, 2)
                            ELSE 0
                        END as batting_average
                    FROM player_stats
                    ORDER BY batting_average DESC
                    LIMIT :limit
                """)
                
            elif category == "runs":
                query = text("""
                    SELECT 
                        u.id as user_id,
                        u.full_name as name,
                        COUNT(*) as matches,
                        SUM(mp.batting_runs) as total_runs
                    FROM users u
                    JOIN match_player_stats mp ON u.id = mp.player_id
                    JOIN cricket_matches cm ON mp.match_id = cm.id
                    WHERE cm.status = 'completed'
                    GROUP BY u.id, u.full_name
                    HAVING COUNT(*) >= :min_matches
                    ORDER BY total_runs DESC
                    LIMIT :limit
                """)
                
            elif category == "wickets":
                query = text("""
                    SELECT 
                        u.id as user_id,
                        u.full_name as name,
                        COUNT(*) as matches,
                        SUM(mp.wickets_taken) as total_wickets
                    FROM users u
                    JOIN match_player_stats mp ON u.id = mp.player_id
                    JOIN cricket_matches cm ON mp.match_id = cm.id
                    WHERE cm.status = 'completed'
                    GROUP BY u.id, u.full_name
                    HAVING COUNT(*) >= :min_matches
                    ORDER BY total_wickets DESC
                    LIMIT :limit
                """)
            else:
                raise ValidationError("category", f"Unknown leaderboard category: {category}")
            
            result = await self.db.execute(query, {"min_matches": min_matches, "limit": limit})
            rows = result.fetchall()
            
            leaderboard = []
            for position, row in enumerate(rows, 1):
                entry = dict(row._mapping)
                entry['position'] = position
                leaderboard.append(entry)
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            raise InternalServerError("get leaderboard")

    async def get_player_match_history(
        self, 
        user_id: str, 
        limit: int = 10,
        tournament_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get player's recent match performances"""
        try:
            # Build the base query
            query_text = """
                SELECT 
                    mp.*,
                    cm.match_date,
                    cm.venue,
                    t1.name as team_a_name,
                    t2.name as team_b_name,
                    tm.tournament_id,
                    tour.name as tournament_name
                FROM match_player_stats mp
                JOIN cricket_matches cm ON mp.match_id = cm.id
                JOIN teams t1 ON cm.team_a_id = t1.id
                JOIN teams t2 ON cm.team_b_id = t2.id
                LEFT JOIN tournament_matches tm ON cm.id = tm.match_id
                LEFT JOIN tournaments tour ON tm.tournament_id = tour.id
                WHERE mp.player_id = :user_id
                AND cm.status = 'completed'
            """
            
            params = {"user_id": user_id, "limit": limit}
            
            if tournament_id:
                query_text += " AND tm.tournament_id = :tournament_id"
                params["tournament_id"] = tournament_id
            
            query_text += " ORDER BY cm.match_date DESC LIMIT :limit"
            
            result = await self.db.execute(text(query_text), params)
            rows = result.fetchall()
            
            return [dict(row._mapping) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting match history: {e}")
            raise InternalServerError("get match history")

    async def get_team_season_summary(
        self, 
        team_id: str, 
        season_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get team performance summary for a season"""
        try:
            current_year = season_year or datetime.now().year
            
            query = text("""
                WITH team_matches AS (
                    SELECT 
                        cm.*,
                        CASE 
                            WHEN cm.team_a_id = :team_id THEN cm.team_a_score
                            ELSE cm.team_b_score
                        END as team_score,
                        CASE 
                            WHEN cm.team_a_id = :team_id THEN cm.team_b_score
                            ELSE cm.team_a_score
                        END as opponent_score,
                        CASE 
                            WHEN cm.team_a_id = :team_id AND cm.team_a_score > cm.team_b_score THEN 1
                            WHEN cm.team_b_id = :team_id AND cm.team_b_score > cm.team_a_score THEN 1
                            ELSE 0
                        END as won,
                        CASE 
                            WHEN cm.team_a_score = cm.team_b_score THEN 1
                            ELSE 0
                        END as tied
                    FROM cricket_matches cm
                    WHERE (cm.team_a_id = :team_id OR cm.team_b_id = :team_id)
                    AND cm.status = 'completed'
                    AND CAST(strftime('%Y', cm.match_date) AS INTEGER) = :season_year
                )
                SELECT 
                    COUNT(*) as matches_played,
                    SUM(won) as matches_won,
                    SUM(CASE WHEN won = 0 AND tied = 0 THEN 1 ELSE 0 END) as matches_lost,
                    SUM(tied) as matches_tied,
                    ROUND(AVG(team_score), 2) as avg_score,
                    MAX(team_score) as highest_score,
                    MIN(team_score) as lowest_score,
                    CASE 
                        WHEN COUNT(*) > 0 THEN ROUND((CAST(SUM(won) AS FLOAT) / COUNT(*)) * 100, 2)
                        ELSE 0
                    END as win_percentage
                FROM team_matches
            """)
            
            result = await self.db.execute(query, {
                "team_id": team_id, 
                "season_year": current_year
            })
            row = result.fetchone()
            
            return dict(row._mapping) if row else {}
            
        except Exception as e:
            logger.error(f"Error getting team season summary: {e}")
            raise InternalServerError("get team season summary")

    async def get_tournament_leaderboard(
        self, 
        tournament_id: str, 
        category: str = "runs"
    ) -> List[Dict[str, Any]]:
        """Get tournament-specific leaderboard"""
        try:
            query = text("""
                SELECT 
                    u.id as user_id,
                    u.full_name as name,
                    COUNT(DISTINCT cm.id) as matches,
                    SUM(mp.batting_runs) as total_runs,
                    SUM(mp.wickets_taken) as total_wickets,
                    AVG(mp.batting_runs) as avg_runs_per_match
                FROM users u
                JOIN match_player_stats mp ON u.id = mp.player_id
                JOIN cricket_matches cm ON mp.match_id = cm.id
                JOIN tournament_matches tm ON cm.id = tm.match_id
                WHERE tm.tournament_id = :tournament_id
                AND cm.status = 'completed'
                GROUP BY u.id, u.full_name
                ORDER BY total_runs DESC
                LIMIT 20
            """)
            
            result = await self.db.execute(query, {"tournament_id": tournament_id})
            rows = result.fetchall()
            
            leaderboard = []
            for position, row in enumerate(rows, 1):
                entry = dict(row._mapping)
                entry['position'] = position
                leaderboard.append(entry)
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting tournament leaderboard: {e}")
            raise InternalServerError("get tournament leaderboard")

    async def record_match_performance(
        self,
        user_id: str,
        match_id: str,
        team_id: str,
        performance_data: Dict[str, Any]
    ) -> PlayerMatchPerformance:
        """Record a player's performance in a match"""
        try:
            # Get match details
            match_result = await self.db.execute(
                select(CricketMatch).where(CricketMatch.id == match_id)
            )
            match = match_result.scalar_one_or_none()
            
            if not match:
                raise ValidationError("match_id", "Match not found")
            
            performance = PlayerMatchPerformance(
                user_id=user_id,
                match_id=match_id,
                team_id=team_id,
                match_date=match.match_date,
                venue=match.venue,
                **performance_data
            )
            
            self.db.add(performance)
            await self.db.commit()
            await self.db.refresh(performance)
            
            return performance
            
        except Exception as e:
            logger.error(f"Error recording match performance: {e}")
            await self.db.rollback()
            raise InternalServerError("record match performance")

    async def update_or_create_career_stats(self, user_id: str) -> PlayerCareerStats:
        """Update or create career statistics based on current match data"""
        try:
            # Calculate current stats from matches
            calculated_stats = await self.calculate_career_stats_from_matches(user_id)
            
            if not calculated_stats:
                # No match data, create empty stats
                return await self.create_initial_career_stats(user_id)
            
            # Get existing career stats or create new
            existing_stats = await self.get_player_career_stats(user_id)
            
            if existing_stats:
                # Update using SQL UPDATE statement to avoid attribute assignment issues
                await self.db.execute(
                    text("""
                        UPDATE player_career_stats SET
                            total_matches = :total_matches,
                            innings_batted = :innings_batted,
                            runs_scored = :total_runs,
                            highest_score = :highest_score,
                            balls_faced = :total_balls_faced,
                            fours_hit = :total_fours,
                            sixes_hit = :total_sixes,
                            times_out = :times_out,
                            times_not_out = :times_not_out,
                            innings_bowled = :innings_bowled,
                            overs_bowled = :total_overs_bowled,
                            runs_conceded = :total_runs_conceded,
                            wickets_taken = :total_wickets,
                            catches_taken = :total_catches,
                            stumpings_made = :total_stumpings,
                            run_outs_effected = :total_run_outs,
                            batting_average = :batting_average,
                            batting_strike_rate = :batting_strike_rate,
                            bowling_average = :bowling_average,
                            bowling_economy_rate = :bowling_economy_rate,
                            last_updated = NOW()
                        WHERE user_id = :user_id
                    """),
                    {**calculated_stats, "user_id": user_id}
                )
                await self.db.commit()
                
                # Refresh and return
                await self.db.refresh(existing_stats)
                return existing_stats
            else:
                # Create new career stats record
                await self.db.execute(
                    text("""
                        INSERT INTO player_career_stats (
                            user_id, total_matches, innings_batted, runs_scored, highest_score,
                            balls_faced, fours_hit, sixes_hit, times_out, times_not_out,
                            innings_bowled, overs_bowled, runs_conceded, wickets_taken,
                            catches_taken, stumpings_made, run_outs_effected,
                            batting_average, batting_strike_rate, bowling_average, bowling_economy_rate
                        ) VALUES (
                            :user_id, :total_matches, :innings_batted, :total_runs, :highest_score,
                            :total_balls_faced, :total_fours, :total_sixes, :times_out, :times_not_out,
                            :innings_bowled, :total_overs_bowled, :total_runs_conceded, :total_wickets,
                            :total_catches, :total_stumpings, :total_run_outs,
                            :batting_average, :batting_strike_rate, :bowling_average, :bowling_economy_rate
                        )
                    """),
                    {**calculated_stats, "user_id": user_id}
                )
                await self.db.commit()
                
                # Return the newly created stats
                return await self.get_player_career_stats(user_id)
                
        except Exception as e:
            logger.error(f"Error updating career stats: {e}")
            await self.db.rollback()
            raise InternalServerError("update career stats")

    async def get_team_rankings(
        self,
        sport: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get team rankings based on performance metrics"""
        try:
            # Build base query for team rankings
            # Note: Teams table doesn't have sport column, so we ignore sport filter for now
            base_query = """
                WITH team_stats AS (
                    SELECT 
                        t.id,
                        t.name,
                        COUNT(DISTINCT CASE 
                            WHEN cm.team_a_id = t.id OR cm.team_b_id = t.id 
                            THEN cm.id 
                        END) as total_matches,
                        COUNT(DISTINCT CASE 
                            WHEN (cm.team_a_id = t.id AND cm.team_a_score > cm.team_b_score) 
                                OR (cm.team_b_id = t.id AND cm.team_b_score > cm.team_a_score)
                            THEN cm.id 
                        END) as wins,
                        COUNT(DISTINCT CASE 
                            WHEN (cm.team_a_id = t.id AND cm.team_a_score < cm.team_b_score) 
                                OR (cm.team_b_id = t.id AND cm.team_b_score < cm.team_a_score)
                            THEN cm.id 
                        END) as losses
                    FROM teams t
                    LEFT JOIN cricket_matches cm ON (
                        (cm.team_a_id = t.id OR cm.team_b_id = t.id) 
                        AND cm.status = 'completed'
                    )
                    WHERE t.is_active = true
                    GROUP BY t.id, t.name
                )
                SELECT 
                    id,
                    name,
                    total_matches,
                    wins,
                    losses,
                    (total_matches - wins - losses) as draws,
                    CASE 
                        WHEN total_matches > 0 THEN ROUND((CAST(wins AS FLOAT) / total_matches) * 100, 2)
                        ELSE 0
                    END as win_percentage,
                    (wins * 2 + (total_matches - wins - losses)) as points
                FROM team_stats
                ORDER BY points DESC, win_percentage DESC, total_matches DESC
                LIMIT :limit
            """
            
            params = {"limit": limit}
                
            result = await self.db.execute(text(base_query), params)
            rows = result.fetchall()
            
            rankings = []
            for i, row in enumerate(rows, 1):
                rankings.append({
                    "rank": i,
                    "team_id": str(row.id),
                    "team_name": row.name,
                    "sport": "cricket",  # Default to cricket since we only have cricket matches
                    "total_matches": row.total_matches,
                    "wins": row.wins,
                    "losses": row.losses,
                    "draws": row.draws,
                    "win_percentage": row.win_percentage,
                    "points": row.points
                })
            
            return rankings
            
        except Exception as e:
            logger.error(f"Error getting team rankings: {e}")
            raise InternalServerError("get team rankings")
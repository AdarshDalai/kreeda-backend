"""
Statistics service for comprehensive player and team analytics
Provides career tracking, performance trends, and comparative statistics
"""
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, desc, func, select, update, case, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cricket import CricketMatch, MatchPlayerStats
from app.models.statistics import (
    PlayerCareerStats,
    PlayerMatchPerformance,
    TeamSeasonStats,
    PlayerPerformanceTrend,
    Leaderboard,
    PlayerComparison,
)
from app.models.tournament import Tournament, TournamentStanding
from app.models.user import Team, User
from app.schemas.statistics import (
    StatsFilterRequest,
    LeaderboardRequest,
    PlayerComparisonRequest,
    CareerMilestone,
    PlayerCareerSummary,
    TeamAnalytics,
)
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
            result = await self.db.execute(
                select(PlayerCareerStats)
                .options(selectinload(PlayerCareerStats.user))
                .where(PlayerCareerStats.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting career stats for user {user_id}: {e}")
            raise InternalServerError("get career stats")

    async def update_career_stats_after_match(
        self, 
        user_id: str, 
        match_performance: PlayerMatchPerformance
    ) -> None:
        """Update career statistics after a match performance"""
        try:
            # Get or create career stats
            career_stats = await self.get_player_career_stats(user_id)
            
            if not career_stats:
                career_stats = PlayerCareerStats(user_id=user_id)
                self.db.add(career_stats)
            
            # Update match counts
            career_stats.total_matches += 1
            
            # Update batting stats if player batted
            if match_performance.batted:
                career_stats.innings_batted += 1
                career_stats.runs_scored += match_performance.runs_scored
                career_stats.balls_faced += match_performance.balls_faced
                career_stats.fours_hit += match_performance.fours_hit
                career_stats.sixes_hit += match_performance.sixes_hit
                
                if match_performance.runs_scored > career_stats.highest_score:
                    career_stats.highest_score = match_performance.runs_scored
                
                if match_performance.dismissal_type:
                    career_stats.times_out += 1
                else:
                    career_stats.times_not_out += 1
            
            # Update bowling stats if player bowled
            if match_performance.bowled:
                career_stats.innings_bowled += 1
                career_stats.overs_bowled += match_performance.overs_bowled
                career_stats.runs_conceded += match_performance.runs_conceded
                career_stats.wickets_taken += match_performance.wickets_taken
                career_stats.maidens_bowled += match_performance.maidens_bowled
            
            # Update fielding stats
            career_stats.catches_taken += match_performance.catches_taken
            career_stats.stumpings_made += match_performance.stumpings_made
            career_stats.run_outs_effected += match_performance.run_outs_effected
            
            # Update awards
            if match_performance.man_of_match:
                career_stats.man_of_match_awards += 1
            
            # Recalculate averages and rates
            await self._recalculate_career_metrics(career_stats)
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating career stats: {e}")
            await self.db.rollback()
            raise InternalServerError("update career stats")

    async def _recalculate_career_metrics(self, career_stats: PlayerCareerStats) -> None:
        """Recalculate career performance metrics"""
        # Batting average
        if career_stats.times_out > 0:
            career_stats.batting_average = Decimal(
                career_stats.runs_scored / career_stats.times_out
            ).quantize(Decimal('0.01'))
        
        # Batting strike rate
        if career_stats.balls_faced > 0:
            career_stats.batting_strike_rate = Decimal(
                (career_stats.runs_scored / career_stats.balls_faced) * 100
            ).quantize(Decimal('0.01'))
        
        # Bowling average
        if career_stats.wickets_taken > 0:
            career_stats.bowling_average = Decimal(
                career_stats.runs_conceded / career_stats.wickets_taken
            ).quantize(Decimal('0.01'))
        
        # Bowling strike rate (balls per wicket)
        if career_stats.wickets_taken > 0 and career_stats.overs_bowled > 0:
            balls_bowled = float(career_stats.overs_bowled) * 6
            career_stats.bowling_strike_rate = Decimal(
                balls_bowled / career_stats.wickets_taken
            ).quantize(Decimal('0.01'))
        
        # Economy rate
        if career_stats.overs_bowled > 0:
            career_stats.bowling_economy_rate = Decimal(
                career_stats.runs_conceded / float(career_stats.overs_bowled)
            ).quantize(Decimal('0.01'))

    async def get_leaderboard(
        self, 
        category: str, 
        scope: str, 
        scope_id: Optional[str] = None, 
        limit: int = 20,
        min_matches: int = 5
    ) -> List[Leaderboard]:
        """Get leaderboard for a specific category and scope"""
        try:
            query = select(Leaderboard).where(
                and_(
                    Leaderboard.category == category,
                    Leaderboard.scope == scope,
                    Leaderboard.matches_qualification >= min_matches
                )
            )
            
            if scope_id:
                query = query.where(Leaderboard.scope_id == scope_id)
            
            query = query.order_by(Leaderboard.position.asc()).limit(limit)
            query = query.options(selectinload(Leaderboard.user))
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            raise InternalServerError("get leaderboard")

    async def generate_leaderboards(self, scope: str, scope_id: Optional[str] = None) -> None:
        """Generate leaderboards for all categories"""
        try:
            categories = [
                'batting_avg', 'bowling_avg', 'runs', 'wickets', 
                'strike_rate', 'economy_rate'
            ]
            
            for category in categories:
                await self._generate_category_leaderboard(category, scope, scope_id)
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error generating leaderboards: {e}")
            await self.db.rollback()
            raise InternalServerError("generate leaderboards")

    async def _generate_category_leaderboard(
        self, 
        category: str, 
        scope: str, 
        scope_id: Optional[str]
    ) -> None:
        """Generate leaderboard for a specific category"""
        # Clear existing leaderboard entries
        await self.db.execute(
            select(Leaderboard).where(
                and_(
                    Leaderboard.category == category,
                    Leaderboard.scope == scope,
                    Leaderboard.scope_id == scope_id if scope_id else Leaderboard.scope_id.is_(None)
                )
            ).delete()
        )
        
        # Query career stats and rank by category
        if category == 'batting_avg':
            order_col = PlayerCareerStats.batting_average.desc()
            value_col = PlayerCareerStats.batting_average
            min_qualification = 10  # minimum innings
            
        elif category == 'bowling_avg':
            order_col = PlayerCareerStats.bowling_average.asc()
            value_col = PlayerCareerStats.bowling_average
            min_qualification = 10  # minimum wickets
            
        elif category == 'runs':
            order_col = PlayerCareerStats.runs_scored.desc()
            value_col = PlayerCareerStats.runs_scored
            min_qualification = 5  # minimum matches
            
        elif category == 'wickets':
            order_col = PlayerCareerStats.wickets_taken.desc()
            value_col = PlayerCareerStats.wickets_taken
            min_qualification = 5  # minimum matches
            
        elif category == 'strike_rate':
            order_col = PlayerCareerStats.batting_strike_rate.desc()
            value_col = PlayerCareerStats.batting_strike_rate
            min_qualification = 10  # minimum balls faced
            
        elif category == 'economy_rate':
            order_col = PlayerCareerStats.bowling_economy_rate.asc()
            value_col = PlayerCareerStats.bowling_economy_rate
            min_qualification = 10  # minimum overs
        
        # Build query based on scope
        query = select(PlayerCareerStats).where(
            PlayerCareerStats.total_matches >= min_qualification
        ).order_by(order_col).limit(100)
        
        result = await self.db.execute(query)
        stats_list = result.scalars().all()
        
        # Create leaderboard entries
        for position, stats in enumerate(stats_list, 1):
            leaderboard_entry = Leaderboard(
                category=category,
                scope=scope,
                scope_id=scope_id,
                user_id=stats.user_id,
                position=position,
                value=getattr(stats, value_col.key),
                matches_qualification=stats.total_matches
            )
            self.db.add(leaderboard_entry)

    async def get_player_performance_trends(
        self, 
        user_id: str, 
        period_type: str = "monthly",
        periods: int = 6
    ) -> List[PlayerPerformanceTrend]:
        """Get player performance trends over time"""
        try:
            end_date = datetime.utcnow()
            
            # Calculate period boundaries
            if period_type == "monthly":
                delta = timedelta(days=30)
            elif period_type == "quarterly":
                delta = timedelta(days=90)
            elif period_type == "yearly":
                delta = timedelta(days=365)
            else:
                delta = timedelta(days=30)
            
            trends = []
            
            for i in range(periods):
                period_end = end_date - (delta * i)
                period_start = period_end - delta
                
                # Get or create trend for this period
                trend = await self._calculate_period_trend(
                    user_id, period_type, period_start, period_end
                )
                if trend:
                    trends.append(trend)
            
            return sorted(trends, key=lambda x: x.period_start, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            raise InternalServerError("get performance trends")

    async def _calculate_period_trend(
        self,
        user_id: str,
        period_type: str,
        period_start: datetime,
        period_end: datetime
    ) -> Optional[PlayerPerformanceTrend]:
        """Calculate performance trend for a specific period"""
        try:
            # Check if trend already exists
            existing = await self.db.execute(
                select(PlayerPerformanceTrend).where(
                    and_(
                        PlayerPerformanceTrend.user_id == user_id,
                        PlayerPerformanceTrend.period_type == period_type,
                        PlayerPerformanceTrend.period_start == period_start
                    )
                )
            )
            
            if existing.scalar_one_or_none():
                return existing.scalar_one()
            
            # Get match performances for the period
            performances = await self.db.execute(
                select(PlayerMatchPerformance).where(
                    and_(
                        PlayerMatchPerformance.user_id == user_id,
                        PlayerMatchPerformance.match_date >= period_start,
                        PlayerMatchPerformance.match_date < period_end
                    )
                )
            )
            
            performance_list = list(performances.scalars().all())
            
            if not performance_list:
                return None
            
            # Calculate aggregated statistics
            total_matches = len(performance_list)
            total_runs = sum(p.runs_scored for p in performance_list)
            total_wickets = sum(p.wickets_taken for p in performance_list)
            total_balls_faced = sum(p.balls_faced for p in performance_list)
            total_dismissals = sum(1 for p in performance_list if p.dismissal_type)
            
            # Calculate averages
            batting_avg = Decimal(total_runs / total_dismissals) if total_dismissals > 0 else Decimal(0)
            strike_rate = Decimal((total_runs / total_balls_faced) * 100) if total_balls_faced > 0 else Decimal(0)
            
            # Calculate form rating (0-10 based on recent performance)
            form_rating = self._calculate_form_rating(performance_list)
            
            # Create trend object
            trend = PlayerPerformanceTrend(
                user_id=user_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                matches_played=total_matches,
                runs_scored=total_runs,
                wickets_taken=total_wickets,
                batting_average=batting_avg,
                strike_rate=strike_rate,
                form_rating=form_rating,
                consistency_score=self._calculate_consistency_score(performance_list)
            )
            
            self.db.add(trend)
            await self.db.commit()
            
            return trend
            
        except Exception as e:
            logger.error(f"Error calculating period trend: {e}")
            return None

    def _calculate_form_rating(self, performances: List[PlayerMatchPerformance]) -> Decimal:
        """Calculate form rating based on recent performances"""
        if not performances:
            return Decimal(0)
        
        # Weight recent performances more heavily
        total_weight = 0
        weighted_score = 0
        
        for i, performance in enumerate(sorted(performances, key=lambda x: x.match_date, reverse=True)):
            weight = 1.0 / (i + 1)  # More recent gets higher weight
            score = float(performance.overall_rating)
            
            weighted_score += score * weight
            total_weight += weight
        
        return Decimal(weighted_score / total_weight).quantize(Decimal('0.01'))

    def _calculate_consistency_score(self, performances: List[PlayerMatchPerformance]) -> Decimal:
        """Calculate consistency score based on performance variance"""
        if len(performances) < 2:
            return Decimal(0)
        
        ratings = [float(p.overall_rating) for p in performances]
        mean_rating = sum(ratings) / len(ratings)
        variance = sum((r - mean_rating) ** 2 for r in ratings) / len(ratings)
        
        # Convert variance to consistency score (lower variance = higher consistency)
        consistency = max(0, 10 - (variance / 2))
        return Decimal(consistency).quantize(Decimal('0.01'))

    async def compare_players(
        self,
        player1_id: str,
        player2_id: str,
        comparison_type: str = "career",
        scope_id: Optional[str] = None
    ) -> PlayerComparison:
        """Compare two players' performance"""
        try:
            # Get existing comparison or create new one
            existing = await self.db.execute(
                select(PlayerComparison).where(
                    and_(
                        or_(
                            and_(
                                PlayerComparison.player1_id == player1_id,
                                PlayerComparison.player2_id == player2_id
                            ),
                            and_(
                                PlayerComparison.player1_id == player2_id,
                                PlayerComparison.player2_id == player1_id
                            )
                        ),
                        PlayerComparison.comparison_type == comparison_type,
                        PlayerComparison.scope_id == scope_id if scope_id else PlayerComparison.scope_id.is_(None)
                    )
                )
            )
            
            comparison = existing.scalar_one_or_none()
            
            if not comparison:
                comparison = await self._create_player_comparison(
                    player1_id, player2_id, comparison_type, scope_id
                )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing players: {e}")
            raise InternalServerError("compare players")

    async def _create_player_comparison(
        self,
        player1_id: str,
        player2_id: str,
        comparison_type: str,
        scope_id: Optional[str]
    ) -> PlayerComparison:
        """Create a new player comparison"""
        # Get career stats for both players
        stats1 = await self.get_player_career_stats(player1_id)
        stats2 = await self.get_player_career_stats(player2_id)
        
        if not stats1 or not stats2:
            raise ValidationError("player_stats", "Career stats not found for one or both players")
        
        # Calculate comparison metrics
        player1_avg = float(stats1.batting_average)
        player2_avg = float(stats2.batting_average)
        
        dominance_factor = Decimal(
            (player1_avg - player2_avg) / max(player1_avg, player2_avg) * 100
        ).quantize(Decimal('0.01'))
        
        performance_gap = Decimal(abs(player1_avg - player2_avg)).quantize(Decimal('0.01'))
        
        comparison = PlayerComparison(
            player1_id=player1_id,
            player2_id=player2_id,
            comparison_type=comparison_type,
            scope_id=scope_id,
            player1_avg_score=stats1.batting_average,
            player2_avg_score=stats2.batting_average,
            player1_avg_wickets=Decimal(stats1.wickets_taken / max(1, stats1.total_matches)),
            player2_avg_wickets=Decimal(stats2.wickets_taken / max(1, stats2.total_matches)),
            dominance_factor=dominance_factor,
            performance_gap=performance_gap
        )
        
        self.db.add(comparison)
        await self.db.commit()
        
        return comparison

    async def get_player_career_summary(self, user_id: str) -> PlayerCareerSummary:
        """Get comprehensive career summary for a player"""
        try:
            # Get career stats
            career_stats = await self.get_player_career_stats(user_id)
            if not career_stats:
                raise ValidationError("user_id", "Career stats not found")
            
            # Get recent form (last 5 matches)
            recent_performances = await self.db.execute(
                select(PlayerMatchPerformance)
                .where(PlayerMatchPerformance.user_id == user_id)
                .order_by(PlayerMatchPerformance.match_date.desc())
                .limit(5)
            )
            
            # Get performance trends
            trends = await self.get_player_performance_trends(user_id, "monthly", 6)
            
            # Get current rankings
            rankings = []
            for category in ['batting_avg', 'runs', 'wickets']:
                leaderboard = await self.get_leaderboard(category, 'all_time', limit=100)
                user_entry = next((entry for entry in leaderboard if str(entry.user_id) == user_id), None)
                if user_entry:
                    rankings.append(user_entry)
            
            # Get milestones (simplified - can be enhanced)
            milestones = self._get_career_milestones(career_stats)
            
            return PlayerCareerSummary(
                user_id=user_id,
                user=career_stats.user,
                career_stats=career_stats,
                recent_form=list(recent_performances.scalars().all()),
                performance_trends=trends,
                milestones=milestones,
                rankings=rankings
            )
            
        except Exception as e:
            logger.error(f"Error getting career summary: {e}")
            raise InternalServerError("get career summary")

    def _get_career_milestones(self, stats: PlayerCareerStats) -> List[CareerMilestone]:
        """Generate career milestones based on statistics"""
        milestones = []
        
        # Batting milestones
        if stats.runs_scored >= 1000:
            milestones.append(CareerMilestone(
                milestone_type="batting",
                description=f"{stats.runs_scored} career runs",
                achieved_date=stats.created_at,  # Simplified
                value=stats.runs_scored
            ))
        
        # Bowling milestones
        if stats.wickets_taken >= 50:
            milestones.append(CareerMilestone(
                milestone_type="bowling", 
                description=f"{stats.wickets_taken} career wickets",
                achieved_date=stats.created_at,  # Simplified
                value=stats.wickets_taken
            ))
        
        return milestones
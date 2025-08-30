"""
CloudWatch Metrics Service for Kreeda Backend
Custom metrics for cricket operations and performance monitoring
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudWatchMetricsService:
    """Service for publishing custom metrics to CloudWatch"""

    def __init__(self):
        self.cloudwatch = None
        self.namespace = "Kreeda/Cricket"
        self.enabled = not settings.DEBUG  # Only enable in production

        if self.enabled:
            try:
                self.cloudwatch = boto3.client('cloudwatch', region_name=settings.AWS_REGION)
                logger.info("✅ CloudWatch metrics enabled")
            except Exception as e:
                logger.warning(f"⚠️  CloudWatch metrics initialization failed: {e}")
                self.enabled = False

    def _put_metric(self, metric_name: str, value: float, unit: str = 'Count',
                   dimensions: Optional[Dict[str, str]] = None):
        """Put a metric to CloudWatch"""
        if not self.enabled or not self.cloudwatch:
            return

        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.now(timezone.utc)
            }

            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]

            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )

        except ClientError as e:
            logger.error(f"Failed to publish metric {metric_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error publishing metric {metric_name}: {e}")

    # Cricket-specific metrics
    def record_match_created(self, match_id: str, team1: str, team2: str):
        """Record match creation"""
        self._put_metric('MatchesCreated', 1, dimensions={
            'Team1': team1,
            'Team2': team2
        })

    def record_ball_scored(self, match_id: str, runs: int, ball_type: str):
        """Record ball scoring"""
        self._put_metric('BallsScored', 1, dimensions={
            'Runs': str(runs),
            'BallType': ball_type
        })

    def record_player_stats(self, player_id: str, action: str, value: float = 1):
        """Record player statistics"""
        self._put_metric(f'Player{action}', value, dimensions={
            'PlayerId': player_id
        })

    def record_api_call(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record API call metrics"""
        self._put_metric('APICalls', 1, dimensions={
            'Endpoint': endpoint,
            'Method': method,
            'StatusCode': str(status_code)
        })

        # Record response time
        self._put_metric('APIResponseTime', duration, 'Milliseconds', dimensions={
            'Endpoint': endpoint,
            'Method': method
        })

    def record_error(self, error_type: str, endpoint: str):
        """Record error metrics"""
        self._put_metric('Errors', 1, dimensions={
            'ErrorType': error_type,
            'Endpoint': endpoint
        })

    def record_dynamodb_operation(self, operation: str, table_name: str, duration: float):
        """Record DynamoDB operation metrics"""
        self._put_metric('DynamoDBOperations', 1, dimensions={
            'Operation': operation,
            'TableName': table_name
        })

        self._put_metric('DynamoDBLatency', duration, 'Milliseconds', dimensions={
            'Operation': operation,
            'TableName': table_name
        })

    def record_user_activity(self, user_id: str, action: str):
        """Record user activity"""
        self._put_metric('UserActivity', 1, dimensions={
            'UserId': user_id,
            'Action': action
        })

    def record_performance_metric(self, metric_name: str, value: float, unit: str = 'Count'):
        """Record general performance metrics"""
        self._put_metric(metric_name, value, unit)


# Global metrics service instance
metrics_service = CloudWatchMetricsService()


def get_metrics_service() -> CloudWatchMetricsService:
    """Get the global metrics service instance"""
    return metrics_service

"""
DynamoDB Migration Service for Kreeda Backend
Handles schema evolution and data transformations for DynamoDB
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

from app.core.config import settings

logger = logging.getLogger(__name__)


class DynamoDBMigrationService:
    """Service for managing DynamoDB schema evolution and data migrations"""

    def __init__(self, table_name: Optional[str] = None):
        self.table_name = table_name or settings.DYNAMODB_TABLE
        self.dynamodb: Optional[Any] = None  # DynamoDB resource
        self.table: Optional[Any] = None  # DynamoDB table
        self.migration_history_table = f"{self.table_name}-migrations"

        # Initialize DynamoDB client
        self._init_dynamodb()

    def _init_dynamodb(self):
        """Initialize DynamoDB client and table references"""
        try:
            if settings.DYNAMODB_ENDPOINT_URL:
                # Local DynamoDB
                self.dynamodb = boto3.resource(
                    'dynamodb',
                    endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
                    aws_access_key_id='dummy',
                    aws_secret_access_key='dummy',
                    region_name=settings.AWS_REGION
                )
            else:
                # AWS DynamoDB
                self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)

            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"✅ DynamoDB migration service initialized for table: {self.table_name}")

        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB migration service: {e}")
            raise

    def create_migration_history_table(self):
        """Create migration history table if it doesn't exist"""
        try:
            # Check if migration history table exists
            migration_table = self.dynamodb.Table(self.migration_history_table)
            migration_table.table_status
            logger.info("✅ Migration history table already exists")
            return
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create migration history table
                table = self.dynamodb.create_table(
                    TableName=self.migration_history_table,
                    KeySchema=[
                        {'AttributeName': 'migration_id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'migration_id', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )

                # Wait for table to be created
                table.wait_until_exists()
                logger.info("✅ Migration history table created")
            else:
                raise

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration IDs"""
        try:
            migration_table = self.dynamodb.Table(self.migration_history_table)
            response = migration_table.scan()
            return [item['migration_id'] for item in response.get('Items', [])]
        except Exception as e:
            logger.warning(f"Could not retrieve migration history: {e}")
            return []

    def record_migration(self, migration_id: str, description: str):
        """Record a completed migration"""
        try:
            migration_table = self.dynamodb.Table(self.migration_history_table)
            migration_table.put_item(Item={
                'migration_id': migration_id,
                'description': description,
                'applied_at': datetime.now(timezone.utc).isoformat(),
                'status': 'completed'
            })
            logger.info(f"✅ Migration recorded: {migration_id}")
        except Exception as e:
            logger.error(f"Failed to record migration {migration_id}: {e}")

    def run_migration(self, migration_id: str, description: str, migration_func):
        """Run a migration with proper error handling and recording"""
        applied_migrations = self.get_applied_migrations()

        if migration_id in applied_migrations:
            logger.info(f"⏭️  Migration {migration_id} already applied, skipping")
            return True

        logger.info(f"🚀 Running migration: {migration_id} - {description}")

        try:
            # Run the migration
            migration_func()

            # Record successful migration
            self.record_migration(migration_id, description)

            logger.info(f"✅ Migration {migration_id} completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Migration {migration_id} failed: {e}")
            # Record failed migration
            try:
                migration_table = self.dynamodb.Table(self.migration_history_table)
                migration_table.put_item(Item={
                    'migration_id': migration_id,
                    'description': description,
                    'applied_at': datetime.now(timezone.utc).isoformat(),
                    'status': 'failed',
                    'error': str(e)
                })
            except Exception:
                pass  # Don't fail if we can't record the failure

            return False

    def migrate_user_profiles(self):
        """Migration: Add profile fields to existing users"""
        def migration():
            # Scan for all users
            response = self.table.scan(
                FilterExpression=Attr('entity_type').eq('USER')
            )

            for item in response.get('Items', []):
                # Add new profile fields if they don't exist
                update_expression = []
                expression_attribute_names = {}
                expression_attribute_values = {}

                if 'phone_number' not in item:
                    update_expression.append('#phone = :phone')
                    expression_attribute_names['#phone'] = 'phone_number'
                    expression_attribute_values[':phone'] = None

                if 'date_of_birth' not in item:
                    update_expression.append('#dob = :dob')
                    expression_attribute_names['#dob'] = 'date_of_birth'
                    expression_attribute_values[':dob'] = None

                if 'preferred_batting_position' not in item:
                    update_expression.append('#pos = :pos')
                    expression_attribute_names['#pos'] = 'preferred_batting_position'
                    expression_attribute_values[':pos'] = None

                if update_expression:
                    self.table.update_item(
                        Key={'PK': item['PK'], 'SK': item['SK']},
                        UpdateExpression='SET ' + ', '.join(update_expression),
                        ExpressionAttributeNames=expression_attribute_names,
                        ExpressionAttributeValues=expression_attribute_values
                    )

        return migration

    def migrate_match_statistics(self):
        """Migration: Add statistics fields to matches"""
        def migration():
            # Scan for all matches
            response = self.table.scan(
                FilterExpression=Attr('entity_type').eq('MATCH')
            )

            for item in response.get('Items', []):
                # Add statistics fields
                update_expression = []
                expression_attribute_names = {}
                expression_attribute_values = {}

                if 'total_runs' not in item:
                    update_expression.append('#runs = :runs')
                    expression_attribute_names['#runs'] = 'total_runs'
                    expression_attribute_values[':runs'] = 0

                if 'total_wickets' not in item:
                    update_expression.append('#wickets = :wickets')
                    expression_attribute_names['#wickets'] = 'total_wickets'
                    expression_attribute_values[':wickets'] = 0

                if 'match_duration_minutes' not in item:
                    update_expression.append('#duration = :duration')
                    expression_attribute_names['#duration'] = 'match_duration_minutes'
                    expression_attribute_values[':duration'] = None

                if update_expression:
                    self.table.update_item(
                        Key={'PK': item['PK'], 'SK': item['SK']},
                        UpdateExpression='SET ' + ', '.join(update_expression),
                        ExpressionAttributeNames=expression_attribute_names,
                        ExpressionAttributeValues=expression_attribute_values
                    )

        return migration

    def migrate_team_metadata(self):
        """Migration: Add metadata fields to teams"""
        def migration():
            # Scan for all teams
            response = self.table.scan(
                FilterExpression=Attr('entity_type').eq('TEAM')
            )

            for item in response.get('Items', []):
                # Add metadata fields
                update_expression = []
                expression_attribute_names = {}
                expression_attribute_values = {}

                if 'founded_year' not in item:
                    update_expression.append('#founded = :founded')
                    expression_attribute_names['#founded'] = 'founded_year'
                    expression_attribute_values[':founded'] = None

                if 'team_colors' not in item:
                    update_expression.append('#colors = :colors')
                    expression_attribute_names['#colors'] = 'team_colors'
                    expression_attribute_values[':colors'] = {}

                if 'social_media' not in item:
                    update_expression.append('#social = :social')
                    expression_attribute_names['#social'] = 'social_media'
                    expression_attribute_values[':social'] = {}

                if update_expression:
                    self.table.update_item(
                        Key={'PK': item['PK'], 'SK': item['SK']},
                        UpdateExpression='SET ' + ', '.join(update_expression),
                        ExpressionAttributeNames=expression_attribute_names,
                        ExpressionAttributeValues=expression_attribute_values
                    )

        return migration

    def run_all_migrations(self):
        """Run all available migrations in order"""
        logger.info("🚀 Starting DynamoDB migrations...")

        # Ensure migration history table exists
        self.create_migration_history_table()

        migrations = [
            ('user_profile_fields_v1', 'Add profile fields to user entities', self.migrate_user_profiles),
            ('match_statistics_v1', 'Add statistics fields to match entities', self.migrate_match_statistics),
            ('team_metadata_v1', 'Add metadata fields to team entities', self.migrate_team_metadata),
        ]

        success_count = 0
        for migration_id, description, migration_func in migrations:
            if self.run_migration(migration_id, description, migration_func()):
                success_count += 1

        logger.info(f"✅ Migration process completed: {success_count}/{len(migrations)} successful")
        return success_count == len(migrations)


# Global migration service instance
migration_service = DynamoDBMigrationService()


def run_database_migrations():
    """Run all database migrations - call this during application startup"""
    try:
        success = migration_service.run_all_migrations()
        return success
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False

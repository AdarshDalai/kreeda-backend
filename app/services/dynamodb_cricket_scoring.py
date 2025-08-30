"""
Complete DynamoDB Service for Kreeda Cricket Scoring
Single Table Design - NoSQL Optimized for Cricket Operations
"""
import os
import json
import uuid
import boto3
from botocore.config import Config
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from app.schemas.cricket import BallCreate, LiveScore, BatsmanStats, BowlerStats, InningsStats
from app.schemas.auth import UserCreate, UserResponse
from app.core.aws_error_handler import dynamodb_error_handler, DynamoDBErrorHandler
from app.services.cloudwatch_metrics import get_metrics_service


class DynamoDBService:
    """Complete DynamoDB service with single table design"""

    def __init__(self, table_name: Optional[str] = None, region_name: Optional[str] = None):
        self.table_name = table_name or os.environ.get('DYNAMODB_TABLE', 'kreeda-cricket-data')
        self.dynamodb: Any = None  # DynamoDB resource
        self.error_handler = DynamoDBErrorHandler(max_retries=3, base_delay=1.0, max_delay=30.0)
        self.metrics = get_metrics_service()  # CloudWatch metrics service
        region = region_name or os.environ.get('AWS_REGION', 'us-east-1')

        # Support for DynamoDB Local in development
        endpoint_url = os.environ.get('DYNAMODB_ENDPOINT_URL')
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

        # Configure DynamoDB client with connection pooling
        if endpoint_url:  # Local DynamoDB
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=endpoint_url,
                aws_access_key_id=aws_access_key or 'dummy',
                aws_secret_access_key=aws_secret_key or 'dummy',
                region_name=region,
                # Connection pooling configuration
                config=Config(
                    max_pool_connections=20,  # Maximum number of connections to keep in the pool
                    retries={'max_attempts': 3},  # Retry configuration
                    region_name=region
                )
            )
        else:  # AWS DynamoDB
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=region,
                # Connection pooling configuration
                config=Config(
                    max_pool_connections=20,  # Maximum number of connections to keep in the pool
                    retries={'max_attempts': 3},  # Retry configuration
                    region_name=region
                )
            )

        # Initialize table reference lazily
        self._table = None

    @property
    def table(self):
        """Lazy table initialization"""
        if self._table is None:
            self._table = self.dynamodb.Table(self.table_name)
            # Ensure table exists (for local development and testing)
            self.create_table_if_not_exists()
        return self._table

    def create_table_if_not_exists(self):
        """Create DynamoDB table if it doesn't exist (for local development)"""
        try:
            # Check if table exists
            self.table.table_status
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create table with single table design
                table = self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'PK',
                            'KeyType': 'HASH'  # Partition key
                        },
                        {
                            'AttributeName': 'SK',
                            'KeyType': 'RANGE'  # Sort key
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'PK',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'SK',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'GSI1PK',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'GSI1SK',
                            'AttributeType': 'S'
                        }
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'GSI1',
                            'KeySchema': [
                                {
                                    'AttributeName': 'GSI1PK',
                                    'KeyType': 'HASH'
                                },
                                {
                                    'AttributeName': 'GSI1SK',
                                    'KeyType': 'RANGE'
                                }
                            ],
                            'Projection': {
                                'ProjectionType': 'ALL'
                            }
                            # Remove ProvisionedThroughput for GSI when using PAY_PER_REQUEST
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST',  # Use PAY_PER_REQUEST to stay in free tier
                    # Remove ProvisionedThroughput for main table when using PAY_PER_REQUEST
                )

                # Wait for table to be created
                table.wait_until_exists()
                self._table = table

    # User Management
    @dynamodb_error_handler()
    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        item = {
            'PK': f'USER#{user_id}',
            'SK': f'USER#{user_id}',
            'GSI1PK': 'USER',
            'GSI1SK': f'USER#{user_data.username}',
            'id': user_id,
            'username': user_data.username,
            'email': user_data.email,
            'hashed_password': user_data.password,  # Password should already be hashed by caller
            'full_name': user_data.full_name,
            'created_at': now,
            'entity_type': 'USER'
        }

        self.table.put_item(Item=item)
        return item

    @dynamodb_error_handler()
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username using GSI"""
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq('USER') & Key('GSI1SK').eq(f'USER#{username}')
        )

        if response['Items']:
            return response['Items'][0]
        return None

    @dynamodb_error_handler()
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        response = self.table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'USER#{user_id}'
            }
        )
        return response.get('Item')

    # Team Management
    @dynamodb_error_handler()
    def create_team(self, team_data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        """Create a new team"""
        team_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        item = {
            'PK': f'TEAM#{team_id}',
            'SK': f'TEAM#{team_id}',
            'GSI1PK': f'USER#{created_by}',
            'GSI1SK': f'TEAM#{team_id}',
            'id': team_id,
            'name': team_data['name'],
            'short_name': team_data['short_name'],
            'created_by': created_by,
            'created_at': now,
            'entity_type': 'TEAM'
        }

        self.table.put_item(Item=item)
        return item

    @dynamodb_error_handler()
    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team by ID"""
        response = self.table.get_item(
            Key={
                'PK': f'TEAM#{team_id}',
                'SK': f'TEAM#{team_id}'
            }
        )
        return response.get('Item')

    @dynamodb_error_handler()
    def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all teams created by a user"""
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(f'USER#{user_id}'),
            FilterExpression=Attr('entity_type').eq('TEAM')
        )
        return response.get('Items', [])

    # Player Management
    @dynamodb_error_handler()
    def add_player_to_team(self, team_id: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a player to a team"""
        player_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        item = {
            'PK': f'TEAM#{team_id}',
            'SK': f'PLAYER#{player_id}',
            'GSI1PK': f'TEAM#{team_id}',
            'GSI1SK': f'PLAYER#{player_id}',
            'id': player_id,
            'team_id': team_id,
            'name': player_data['name'],
            'jersey_number': player_data['jersey_number'],
            'created_at': now,
            'entity_type': 'PLAYER'
        }

        self.table.put_item(Item=item)
        return item

    @dynamodb_error_handler()
    def get_team_players(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all players for a team"""
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(f'TEAM#{team_id}'),
            FilterExpression=Attr('entity_type').eq('PLAYER')
        )
        return response.get('Items', [])

    @dynamodb_error_handler()
    def update_player(self, player_id: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update player details"""
        # First get the current player to get the team_id
        current_player = self.get_player(player_id)
        if not current_player:
            return {}

        # Build update expression dynamically based on provided fields
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}

        if 'name' in player_data and player_data['name'] is not None:
            update_expression += "#name = :name, "
            expression_attribute_values[':name'] = player_data['name']
            expression_attribute_names['#name'] = 'name'

        if 'jersey_number' in player_data and player_data['jersey_number'] is not None:
            update_expression += "jersey_number = :jersey_number, "
            expression_attribute_values[':jersey_number'] = player_data['jersey_number']

        if 'batting_order' in player_data and player_data['batting_order'] is not None:
            update_expression += "batting_order = :batting_order, "
            expression_attribute_values[':batting_order'] = player_data['batting_order']

        if 'is_captain' in player_data and player_data['is_captain'] is not None:
            update_expression += "is_captain = :is_captain, "
            expression_attribute_values[':is_captain'] = player_data['is_captain']

        if 'is_wicket_keeper' in player_data and player_data['is_wicket_keeper'] is not None:
            update_expression += "is_wicket_keeper = :is_wicket_keeper, "
            expression_attribute_values[':is_wicket_keeper'] = player_data['is_wicket_keeper']

        # Remove trailing comma and space
        update_expression = update_expression.rstrip(', ')

        response = self.table.update_item(
            Key={
                'PK': f'TEAM#{current_player["team_id"]}',
                'SK': f'PLAYER#{player_id}'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None,
            ReturnValues='ALL_NEW'
        )

        return response.get('Attributes', {})

    @dynamodb_error_handler()
    def get_player(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get player by ID"""
        # We need to find the player by scanning since we don't have a GSI for player lookup
        response = self.table.scan(
            FilterExpression=Attr('entity_type').eq('PLAYER') & Attr('id').eq(player_id)
        )
        items = response.get('Items', [])
        return items[0] if items else None

    # Match Management
    @dynamodb_error_handler()
    def create_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new match"""
        match_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        item = {
            'PK': f'MATCH#{match_id}',
            'SK': f'MATCH#{match_id}',
            'GSI1PK': f'TEAM#{match_data["team_a_id"]}',
            'GSI1SK': f'MATCH#{match_id}',
            'id': match_id,
            'team_a_id': match_data['team_a_id'],
            'team_b_id': match_data['team_b_id'],
            'overs_per_side': match_data['overs_per_side'],
            'venue': match_data['venue'],
            'status': 'scheduled',
            'created_at': now,
            'entity_type': 'MATCH'
        }

        self.table.put_item(Item=item)

        # Record CloudWatch metrics
        try:
            team_a_name = self.get_team(match_data['team_a_id']).get('name', 'Unknown')
            team_b_name = self.get_team(match_data['team_b_id']).get('name', 'Unknown')
            self.metrics.record_match_created(match_id, team_a_name, team_b_name)
        except Exception as e:
            # Don't fail the operation if metrics recording fails
            pass

        return item

    @dynamodb_error_handler()
    def update_match_toss(self, match_id: str, toss_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update match with toss result"""
        response = self.table.update_item(
            Key={
                'PK': f'MATCH#{match_id}',
                'SK': f'MATCH#{match_id}'
            },
            UpdateExpression='SET toss_winner = :tw, batting_first = :bf',
            ExpressionAttributeValues={
                ':tw': toss_data.get('toss_winner'),
                ':bf': toss_data.get('batting_first')
            },
            ReturnValues='ALL_NEW'
        )
        return response['Attributes']

    @dynamodb_error_handler()
    def update_match_status(self, match_id: str, status: str) -> Dict[str, Any]:
        """Update match status"""
        response = self.table.update_item(
            Key={
                'PK': f'MATCH#{match_id}',
                'SK': f'MATCH#{match_id}'
            },
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': status
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes', {})

    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get match by ID"""
        try:
            # Check if table exists first
            try:
                self.table.table_status
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Table doesn't exist, return None
                    return None
                raise

            response = self.table.get_item(
                Key={
                    'PK': f'MATCH#{match_id}',
                    'SK': f'MATCH#{match_id}'
                }
            )
            return response.get('Item')
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, return None
                return None
            raise

    # Cricket Scoring Operations
    @dynamodb_error_handler()
    def record_ball(self, match_id: str, innings_number: int, ball_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a ball in the match with transaction support"""
        ball_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # Generate ball number with proper sequencing
        ball_number = self._get_next_ball_number(match_id, innings_number)

        item = {
            'PK': f'MATCH#{match_id}',
            'SK': f'BALL#{innings_number}#{ball_number:06d}',
            'GSI1PK': f'INNINGS#{match_id}#{innings_number}',
            'GSI1SK': f'BALL#{ball_number:06d}',
            'id': ball_id,
            'match_id': match_id,
            'innings_number': innings_number,
            'ball_number': ball_number,
            'batsman_id': ball_data.get('batsman_id'),
            'bowler_id': ball_data.get('bowler_id'),
            'runs_scored': ball_data.get('runs', 0),
            'is_wicket': ball_data.get('is_wicket', False),
            'wicket_type': ball_data.get('wicket_type'),
            'extras': ball_data.get('extras', 0),
            'extra_type': ball_data.get('extra_type'),
            'created_at': now,
            'entity_type': 'BALL'
        }

        # Use conditional write to ensure data consistency
        self.table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
        )

        # Record CloudWatch metrics
        try:
            runs = ball_data.get('runs', 0)
            ball_type = 'wicket' if ball_data.get('is_wicket', False) else 'normal'
            if ball_data.get('extras', 0) > 0:
                ball_type = 'extra'

            self.metrics.record_ball_scored(match_id, runs, ball_type)

            # Record player stats
            if ball_data.get('batsman_id'):
                self.metrics.record_player_stats(ball_data['batsman_id'], 'Runs', runs)
            if ball_data.get('bowler_id'):
                self.metrics.record_player_stats(ball_data['bowler_id'], 'BallsBowled', 1)
                if ball_data.get('is_wicket', False):
                    self.metrics.record_player_stats(ball_data['bowler_id'], 'Wickets', 1)

        except Exception as e:
            # Don't fail the operation if metrics recording fails
            pass

        return item

    @dynamodb_error_handler()
    def _get_next_ball_number(self, match_id: str, innings_number: int) -> int:
        """Get the next ball number for proper sequencing"""
        # Query for existing balls in this innings
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(f'INNINGS#{match_id}#{innings_number}'),
            ScanIndexForward=False,  # Get latest first
            Limit=1
        )

        if response['Items']:
            # Extract ball number from the latest ball
            latest_sk = response['Items'][0]['GSI1SK']
            latest_ball_num = int(latest_sk.replace('BALL#', ''))
            return latest_ball_num + 1
        else:
            return 1  # First ball of innings

    @dynamodb_error_handler()
    def get_live_score(self, match_id: str) -> LiveScore:
        """Get live score for a match"""
        # Get match details
        match = self.get_match(match_id)
        if not match:
            # Return a minimal LiveScore object for non-existent match
            return LiveScore(
                match_id=match_id,
                match_status="not_found",
                current_innings=InningsStats(
                    innings_id=f"{match_id}_1",
                    innings_number=1,
                    batting_team="",
                    bowling_team="",
                    total_runs=0,
                    wickets_lost=0,
                    overs_completed="0.0",
                    run_rate=0.0,
                    required_rate=None,
                    balls_remaining=None
                ),
                current_batsmen=[],
                current_bowler=BowlerStats(
                    player_id="",
                    name="Unknown",
                    overs="0.0",
                    runs_conceded=0,
                    wickets=0,
                    economy_rate=0.0
                ),
                recent_balls=[],
                target=None
            )

        # Get balls for current innings
        balls = self.get_match_balls(match_id, 1)  # First innings

        # Calculate basic stats
        total_runs = sum(int(ball.get('runs_scored', 0)) for ball in balls)
        wickets = sum(1 for ball in balls if ball.get('is_wicket', False))
        balls_count = len(balls)
        overs_completed = balls_count // 6 + (balls_count % 6) / 10

        # Get recent balls (last 6)
        recent_balls = balls[-6:] if balls else []

        # Create InningsStats object
        innings_stats = InningsStats(
            innings_id=f"{match_id}_1",
            innings_number=1,
            batting_team=match.get('team_a_id', ''),
            bowling_team=match.get('team_b_id', ''),
            total_runs=total_runs,
            wickets_lost=wickets,
            overs_completed=f"{int(overs_completed)}.{balls_count % 6}",
            run_rate=total_runs / max(overs_completed, 0.1),
            required_rate=None,
            balls_remaining=None
        )

        # Calculate batsman statistics
        batsman_stats = {}
        bowler_stats = {}

        for ball in balls:
            batsman_id = ball.get('batsman_id')
            bowler_id = ball.get('bowler_id')
            runs = int(ball.get('runs_scored', 0))
            is_wicket = ball.get('is_wicket', False)

            # Update batsman stats
            if batsman_id:
                if batsman_id not in batsman_stats:
                    batsman_stats[batsman_id] = {
                        'runs': 0,
                        'balls_faced': 0,
                        'fours': 0,
                        'sixes': 0
                    }
                batsman_stats[batsman_id]['runs'] += runs
                batsman_stats[batsman_id]['balls_faced'] += 1
                if runs == 4:
                    batsman_stats[batsman_id]['fours'] += 1
                elif runs == 6:
                    batsman_stats[batsman_id]['sixes'] += 1

            # Update bowler stats
            if bowler_id:
                if bowler_id not in bowler_stats:
                    bowler_stats[bowler_id] = {
                        'balls_bowled': 0,
                        'runs_conceded': 0,
                        'wickets': 0
                    }
                bowler_stats[bowler_id]['balls_bowled'] += 1
                bowler_stats[bowler_id]['runs_conceded'] += runs
                if is_wicket:
                    bowler_stats[bowler_id]['wickets'] += 1

        # Convert to schema objects
        current_batsmen = []
        for batsman_id, stats in batsman_stats.items():
            # Get player name (simplified - in real implementation, you'd fetch from players table)
            player_name = f"Player {batsman_id[:8]}"  # Use first 8 chars of ID as name
            strike_rate = (stats['runs'] / max(stats['balls_faced'], 1)) * 100

            current_batsmen.append(BatsmanStats(
                player_id=batsman_id,
                name=player_name,
                runs=stats['runs'],
                balls_faced=stats['balls_faced'],
                fours=stats['fours'],
                sixes=stats['sixes'],
                strike_rate=round(strike_rate, 2)
            ))

        # Get current bowler (last bowler who bowled)
        current_bowler = BowlerStats(
            player_id="",
            name="Unknown",
            overs="0.0",
            runs_conceded=0,
            wickets=0,
            economy_rate=0.0
        )

        if bowler_stats:
            # Find the bowler with most recent activity (simplified)
            latest_bowler_id = list(bowler_stats.keys())[-1]
            stats = bowler_stats[latest_bowler_id]
            overs = stats['balls_bowled'] // 6 + (stats['balls_bowled'] % 6) / 10
            economy_rate = stats['runs_conceded'] / max(overs, 0.1)

            bowler_name = f"Bowler {latest_bowler_id[:8]}"
            current_bowler = BowlerStats(
                player_id=latest_bowler_id,
                name=bowler_name,
                overs=f"{int(overs)}.{stats['balls_bowled'] % 6}",
                runs_conceded=stats['runs_conceded'],
                wickets=stats['wickets'],
                economy_rate=round(economy_rate, 2)
            )

        return LiveScore(
            match_id=match_id,
            match_status=match.get('status', 'unknown'),
            current_innings=innings_stats,
            current_batsmen=current_batsmen,
            current_bowler=current_bowler,
            recent_balls=recent_balls,
            target=None
        )

    @dynamodb_error_handler()
    def get_match_balls(self, match_id: str, innings_number: int) -> List[Dict[str, Any]]:
        """Get all balls for a specific innings"""
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(f'INNINGS#{match_id}#{innings_number}'),
            ScanIndexForward=True  # Sort ascending by ball number
        )
        return response.get('Items', [])

    @dynamodb_error_handler()
    def undo_last_ball(self, match_id: str, innings_number: int = 1) -> bool:
        """Delete the last ball recorded for a match innings"""
        # Get all balls for the innings
        balls = self.get_match_balls(match_id, innings_number)
        if not balls:
            return False

        # Find the last ball (highest ball number)
        last_ball = max(balls, key=lambda b: b.get('ball_number', 0))

        # Ensure ball_number is an integer for formatting
        ball_number = int(last_ball.get('ball_number', 0))

        # Delete the ball
        self.table.delete_item(
            Key={
                'PK': f'MATCH#{match_id}',
                'SK': f'BALL#{innings_number}#{ball_number:06d}'
            }
        )
        return True


# Legacy class name for backward compatibility
class DynamoDBCricketService(DynamoDBService):
    """Alias for backward compatibility"""
    pass

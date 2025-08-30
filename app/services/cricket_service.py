"""
Complete DynamoDB Service for Kreeda Cricket Scoring
Single Table Design - NoSQL Optimized for Cricket Operations
"""
import os
import json
import boto3
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from app.schemas.cricket import BallCreate, LiveScore, BatsmanStats, BowlerStats, InningsStats
from app.schemas.auth import UserCreate, UserResponse


class DynamoDBService:
    """Complete DynamoDB service with single table design"""

    def __init__(self, table_name: Optional[str] = None, region_name: Optional[str] = None):
        self.table_name = table_name or os.environ.get('DYNAMODB_TABLE', 'kreeda-cricket-data')
        region = region_name or os.environ.get('AWS_REGION', 'us-east-1')

        # Support for DynamoDB Local in development
        endpoint_url = os.environ.get('DYNAMODB_ENDPOINT_URL')
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

        if endpoint_url:  # DynamoDB Local
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=endpoint_url,
                aws_access_key_id=aws_access_key or 'dummy',
                aws_secret_access_key=aws_secret_key or 'dummy',
                region_name=region
            )
        else:  # AWS DynamoDB
            self.dynamodb = boto3.resource('dynamodb', region_name=region)

        self.table = self.dynamodb.Table(self.table_name)  # type: ignore

    def create_table_if_not_exists(self):
        """Create DynamoDB table if it doesn't exist (for local development)"""
        try:
            # Check if table exists
            self.table.table_status
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create table
                table = self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {'AttributeName': 'pk', 'KeyType': 'HASH'},
                        {'AttributeName': 'sk', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'pk', 'AttributeType': 'S'},
                        {'AttributeName': 'sk', 'AttributeType': 'S'},
                        {'AttributeName': 'gsi1_pk', 'AttributeType': 'S'},
                        {'AttributeName': 'gsi1_sk', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'GSI1',
                            'KeySchema': [
                                {'AttributeName': 'gsi1_pk', 'KeyType': 'HASH'},
                                {'AttributeName': 'gsi1_sk', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'BillingMode': 'PAY_PER_REQUEST'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                # Wait for table to be created
                table.wait_until_exists()
                print(f"Created DynamoDB table: {self.table_name}")
            else:
                raise

    # ===== USER MANAGEMENT =====

    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user in DynamoDB"""
        user_id = str(hash(user_data.username + user_data.email))  # Simple ID generation

        user_item = {
            'pk': f'USER#{user_id}',
            'sk': 'PROFILE',
            'gsi1_pk': f'USERNAME#{user_data.username}',
            'gsi1_sk': 'PROFILE',
            'username': user_data.username,
            'email': user_data.email,
            'full_name': user_data.full_name,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'item_type': 'USER'
        }

        # Add password hash if provided
        if hasattr(user_data, 'password') and user_data.password:
            from app.core.auth import get_password_hash
            user_item['hashed_password'] = get_password_hash(user_data.password)

        self.table.put_item(Item=user_item)
        return user_item

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            response = self.table.get_item(
                Key={
                    'pk': f'USERNAME#{username}',
                    'sk': 'PROFILE'
                }
            )
            return response.get('Item')
        except ClientError:
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            response = self.table.get_item(
                Key={
                    'pk': f'USER#{user_id}',
                    'sk': 'PROFILE'
                }
            )
            return response.get('Item')
        except ClientError:
            return None

    # ===== TEAM MANAGEMENT =====

    def create_team(self, team_data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        """Create a new team in DynamoDB"""
        team_id = str(hash(team_data['name'] + str(datetime.utcnow())))  # Simple ID generation

        team_item = {
            'pk': f'TEAM#{team_id}',
            'sk': 'PROFILE',
            'gsi1_pk': f'USER#{created_by}',
            'gsi1_sk': f'TEAM#{team_id}',
            'team_id': team_id,
            'name': team_data['name'],
            'short_name': team_data.get('short_name', ''),
            'created_by': created_by,
            'created_at': datetime.utcnow().isoformat(),
            'item_type': 'TEAM'
        }

        self.table.put_item(Item=team_item)
        return team_item

    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team by ID"""
        try:
            response = self.table.get_item(
                Key={
                    'pk': f'TEAM#{team_id}',
                    'sk': 'PROFILE'
                }
            )
            return response.get('Item')
        except ClientError:
            return None

    def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all teams created by a user"""
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('gsi1_pk').eq(f'USER#{user_id}') & Key('gsi1_sk').begins_with('TEAM#')
            )
            return response.get('Items', [])
        except ClientError:
            return []

    # ===== PLAYER MANAGEMENT =====

    def add_player_to_team(self, team_id: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a player to a team"""
        player_id = str(hash(player_data['name'] + team_id + str(datetime.utcnow())))

        player_item = {
            'pk': f'TEAM#{team_id}',
            'sk': f'PLAYER#{player_id}',
            'gsi1_pk': f'PLAYER#{player_id}',
            'gsi1_sk': 'PROFILE',
            'player_id': player_id,
            'team_id': team_id,
            'name': player_data['name'],
            'jersey_number': player_data.get('jersey_number'),
            'batting_order': player_data.get('batting_order'),
            'is_captain': player_data.get('is_captain', False),
            'is_wicket_keeper': player_data.get('is_wicket_keeper', False),
            'created_at': datetime.utcnow().isoformat(),
            'item_type': 'PLAYER'
        }

        self.table.put_item(Item=player_item)
        return player_item

    def get_team_players(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all players in a team"""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(f'TEAM#{team_id}') & Key('sk').begins_with('PLAYER#')
            )
            return response.get('Items', [])
        except ClientError:
            return []

    # ===== MATCH MANAGEMENT =====

    def create_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new match"""
        match_id = str(hash(str(match_data) + str(datetime.utcnow())))

        match_item = {
            'pk': f'MATCH#{match_id}',
            'sk': 'PROFILE',
            'gsi1_pk': f'TEAM#{match_data["team_a_id"]}',
            'gsi1_sk': f'MATCH#{match_id}',
            'match_id': match_id,
            'team_a_id': match_data['team_a_id'],
            'team_b_id': match_data['team_b_id'],
            'overs_per_side': match_data['overs_per_side'],
            'venue': match_data.get('venue'),
            'match_date': match_data.get('match_date'),
            'status': 'not_started',
            'current_innings': 1,
            'created_at': datetime.utcnow().isoformat(),
            'item_type': 'MATCH'
        }

        self.table.put_item(Item=match_item)
        return match_item

    def update_match_toss(self, match_id: str, toss_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update match with toss result"""
        update_expression = "SET toss_winner_id = :tw, batting_first_id = :bf, #s = :s"
        expression_attribute_values = {
            ':tw': toss_data['toss_winner_id'],
            ':bf': toss_data['batting_first_id'],
            ':s': 'innings_1'
        }
        expression_attribute_names = {'#s': 'status'}

        response = self.table.update_item(
            Key={
                'pk': f'MATCH#{match_id}',
                'sk': 'PROFILE'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes', {})

    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get match by ID"""
        try:
            response = self.table.get_item(
                Key={
                    'pk': f'MATCH#{match_id}',
                    'sk': 'PROFILE'
                }
            )
            return response.get('Item')
        except ClientError:
            return None

    def record_ball(self, innings_id: int, ball_data: BallCreate) -> Dict[str, Any]:
        """Record a cricket ball in DynamoDB"""
        match_id = self._get_match_id_from_innings(innings_id)

        # Calculate ball position
        current_over, current_ball = self._get_next_ball_position(innings_id)

        # Create ball record
        ball = {
            'pk': f'MATCH#{match_id}',
            'sk': f'BALL#{innings_id}#{current_over}#{current_ball}',
            'gsi1_pk': f'INNINGS#{innings_id}',
            'gsi1_sk': f'BALL#{current_over}#{current_ball}',
            'innings_id': innings_id,
            'over_number': current_over,
            'ball_number': current_ball,
            'batsman_id': ball_data.batsman_id,
            'bowler_id': ball_data.bowler_id,
            'non_striker_id': ball_data.non_striker_id,
            'runs': ball_data.runs,
            'extras': ball_data.extras,
            'extra_type': ball_data.extra_type,
            'is_wicket': ball_data.is_wicket,
            'wicket_type': ball_data.wicket_type,
            'wicket_player_id': ball_data.wicket_player_id,
            'fielder_id': ball_data.fielder_id,
            'is_valid_ball': ball_data.extra_type not in ['wide', 'noball'],
            'created_at': datetime.utcnow().isoformat()
        }

        # Store ball
        self.table.put_item(Item=ball)

        # Update innings statistics
        self._update_innings_stats(innings_id, ball)

        # Check innings completion
        self._check_innings_completion(match_id, innings_id)

        # Return live score
        return self.get_live_score(match_id)

    def get_live_score(self, match_id: int) -> Dict[str, Any]:
        """Get live score from DynamoDB"""
        try:
            # Get match info
            match_response = self.table.get_item(
                Key={'pk': f'MATCH#{match_id}', 'sk': 'METADATA'}
            )

            if 'Item' not in match_response:
                raise ValueError(f"Match {match_id} not found")

            match = match_response['Item']

            # Get current innings
            current_innings_id = match.get('current_innings')
            if not current_innings_id:
                raise ValueError("No active innings")

            # Get innings data
            innings_response = self.table.get_item(
                Key={'pk': f'MATCH#{match_id}', 'sk': f'INNINGS#{current_innings_id}'}
            )

            if 'Item' not in innings_response:
                raise ValueError(f"Innings {current_innings_id} not found")

            innings = innings_response['Item']

            # Get current batsmen stats
            batsmen_stats = self._get_current_batsmen_stats(current_innings_id)

            # Get current bowler stats
            bowler_stats = self._get_current_bowler_stats(current_innings_id)

            # Get recent balls
            recent_balls = self._get_recent_balls(current_innings_id, limit=6)

            # Calculate target
            target = None
            if current_innings_id == 2:
                first_innings = self._get_innings(match_id, 1)
                if first_innings:
                    target = first_innings.get('total_runs', 0) + 1

            return {
                'match_id': match_id,
                'match_status': match.get('status', 'unknown'),
                'current_innings': {
                    'innings_id': current_innings_id,
                    'innings_number': innings.get('innings_number'),
                    'batting_team': innings.get('batting_team_name', 'Unknown'),
                    'bowling_team': innings.get('bowling_team_name', 'Unknown'),
                    'total_runs': innings.get('total_runs', 0),
                    'wickets_lost': innings.get('wickets_lost', 0),
                    'overs_completed': f"{int(innings.get('overs_completed', 0))}.{int((innings.get('overs_completed', 0) % 1) * 10)}",
                    'run_rate': round(innings.get('total_runs', 0) / max(innings.get('overs_completed', 0), 0.1), 2),
                    'required_rate': None,  # Calculate if needed
                    'balls_remaining': None  # Calculate if needed
                },
                'current_batsmen': batsmen_stats,
                'current_bowler': bowler_stats,
                'recent_balls': recent_balls,
                'target': target
            }

        except ClientError as e:
            raise ValueError(f"DynamoDB error: {str(e)}")

    def _get_next_ball_position(self, innings_id: int) -> tuple[int, int]:
        """Calculate next ball position"""
        try:
            # Query for last ball in innings
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('gsi1_pk').eq(f'INNINGS#{innings_id}'),
                ScanIndexForward=False,  # Get latest first
                Limit=1
            )

            if response['Items']:
                last_ball = response['Items'][0]
                over = last_ball['over_number']
                ball = last_ball['ball_number']

                # If last ball was invalid, same position
                if not last_ball.get('is_valid_ball', True):
                    return over, ball

                # Normal progression
                if ball < 6:
                    return over, ball + 1
                else:
                    return over + 1, 1
            else:
                return 1, 1  # First ball

        except ClientError:
            return 1, 1

    def _update_innings_stats(self, innings_id: int, ball: Dict[str, Any]):
        """Update innings statistics"""
        match_id = self._get_match_id_from_innings(innings_id)

        # Get current innings stats
        innings_key = {'pk': f'MATCH#{match_id}', 'sk': f'INNINGS#{innings_id}'}
        innings_response = self.table.get_item(Key=innings_key)

        if 'Item' not in innings_response:
            return

        innings = innings_response['Item']

        # Update stats
        total_runs = innings.get('total_runs', 0) + ball['runs'] + ball['extras']
        wickets_lost = innings.get('wickets_lost', 0) + (1 if ball['is_wicket'] else 0)
        extras = innings.get('extras', 0) + ball['extras']

        # Update overs
        if ball['is_valid_ball']:
            valid_balls = self._count_valid_balls(innings_id) + 1
            overs_completed = valid_balls // 6 + (valid_balls % 6) / 10
        else:
            overs_completed = innings.get('overs_completed', 0)

        # Update innings
        self.table.update_item(
            Key=innings_key,
            UpdateExpression="""
                SET total_runs = :runs,
                    wickets_lost = :wickets,
                    extras = :extras,
                    overs_completed = :overs
            """,
            ExpressionAttributeValues={
                ':runs': total_runs,
                ':wickets': wickets_lost,
                ':extras': extras,
                ':overs': Decimal(str(overs_completed))
            }
        )

    def _count_valid_balls(self, innings_id: int) -> int:
        """Count valid balls in innings"""
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('gsi1_pk').eq(f'INNINGS#{innings_id}'),
                FilterExpression=Attr('is_valid_ball').eq(True)
            )
            return response['Count']
        except ClientError:
            return 0

    def _get_match_id_from_innings(self, innings_id: int) -> int:
        """Get match ID from innings ID"""
        # This would need to be stored or queried
        # For now, assume innings_id contains match_id
        return innings_id // 1000  # Simple mapping

    def _get_current_batsmen_stats(self, innings_id: int) -> List[Dict[str, Any]]:
        """Get current batsmen statistics"""
        try:
            # Get last ball to find current batsmen
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('gsi1_pk').eq(f'INNINGS#{innings_id}'),
                ScanIndexForward=False,
                Limit=1
            )

            if not response['Items']:
                return []

            last_ball = response['Items'][0]
            batsman_ids = [
                last_ball.get('batsman_id'),
                last_ball.get('non_striker_id')
            ]

            stats = []
            for batsman_id in batsman_ids:
                if batsman_id:
                    batsman_stats = self._calculate_batsman_stats(innings_id, batsman_id)
                    if batsman_stats:
                        stats.append(batsman_stats)

            return stats

        except ClientError:
            return []

    def _calculate_batsman_stats(self, innings_id: int, batsman_id: int) -> Optional[Dict[str, Any]]:
        """Calculate batsman statistics"""
        try:
            # Query all balls for this batsman in innings
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('gsi1_pk').eq(f'INNINGS#{innings_id}'),
                FilterExpression=Attr('batsman_id').eq(batsman_id)
            )

            runs = 0
            balls_faced = 0
            fours = 0
            sixes = 0

            for ball in response['Items']:
                if ball.get('is_valid_ball', True):
                    runs += ball.get('runs', 0)
                    balls_faced += 1
                    if ball.get('runs') == 4:
                        fours += 1
                    elif ball.get('runs') == 6:
                        sixes += 1

            strike_rate = (runs / balls_faced * 100) if balls_faced > 0 else 0.0

            return {
                'player_id': batsman_id,
                'name': f'Player {batsman_id}',  # Would need player lookup
                'runs': runs,
                'balls_faced': balls_faced,
                'fours': fours,
                'sixes': sixes,
                'strike_rate': round(strike_rate, 2)
            }

        except ClientError:
            return None

    def _get_current_bowler_stats(self, innings_id: int) -> Dict[str, Any]:
        """Get current bowler statistics"""
        try:
            # Get last ball to find current bowler
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('gsi1_pk').eq(f'INNINGS#{innings_id}'),
                ScanIndexForward=False,
                Limit=1
            )

            if not response['Items']:
                return self._empty_bowler_stats()

            last_ball = response['Items'][0]
            bowler_id = last_ball.get('bowler_id')

            if not bowler_id:
                return self._empty_bowler_stats()

            return self._calculate_bowler_stats(innings_id, bowler_id)

        except ClientError:
            return self._empty_bowler_stats()

    def _calculate_bowler_stats(self, innings_id: int, bowler_id: int) -> Dict[str, Any]:
        """Calculate bowler statistics"""
        try:
            # Query all balls for this bowler in innings
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('gsi1_pk').eq(f'INNINGS#{innings_id}'),
                FilterExpression=Attr('bowler_id').eq(bowler_id)
            )

            runs_conceded = 0
            balls_bowled = 0
            wickets = 0

            for ball in response['Items']:
                runs_conceded += ball.get('runs', 0) + ball.get('extras', 0)
                if ball.get('is_valid_ball', True):
                    balls_bowled += 1
                if ball.get('is_wicket', False):
                    wickets += 1

            overs = f"{balls_bowled // 6}.{balls_bowled % 6}"
            economy_rate = (runs_conceded * 6) / balls_bowled if balls_bowled > 0 else 0.0

            return {
                'player_id': bowler_id,
                'name': f'Bowler {bowler_id}',  # Would need player lookup
                'overs': overs,
                'runs_conceded': runs_conceded,
                'wickets': wickets,
                'economy_rate': round(economy_rate, 2)
            }

        except ClientError:
            return self._empty_bowler_stats()

    def _empty_bowler_stats(self) -> Dict[str, Any]:
        """Return empty bowler stats"""
        return {
            'player_id': 0,
            'name': 'No bowler',
            'overs': '0.0',
            'runs_conceded': 0,
            'wickets': 0,
            'economy_rate': 0.0
        }

    def _get_recent_balls(self, innings_id: int, limit: int = 6) -> List[Dict[str, Any]]:
        """Get recent balls"""
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('gsi1_pk').eq(f'INNINGS#{innings_id}'),
                ScanIndexForward=False,  # Latest first
                Limit=limit
            )

            return [{
                'id': ball.get('id', 0),
                'over_number': ball['over_number'],
                'ball_number': ball['ball_number'],
                'runs': ball.get('runs', 0),
                'extras': ball.get('extras', 0),
                'extra_type': ball.get('extra_type'),
                'is_wicket': ball.get('is_wicket', False),
                'wicket_type': ball.get('wicket_type'),
                'batsman_id': ball.get('batsman_id'),
                'bowler_id': ball.get('bowler_id')
            } for ball in response['Items']]

        except ClientError:
            return []

    def _get_innings(self, match_id: int, innings_number: int) -> Optional[Dict[str, Any]]:
        """Get innings data"""
        try:
            response = self.table.get_item(
                Key={'pk': f'MATCH#{match_id}', 'sk': f'INNINGS#{innings_number}'}
            )
            return response.get('Item')
        except ClientError:
            return None

    def _check_innings_completion(self, match_id: int, innings_id: int):
        """Check if innings is complete and update match status"""
        # Implementation for innings completion logic
        pass

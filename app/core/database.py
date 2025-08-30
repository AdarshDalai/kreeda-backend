"""
DynamoDB table management and initialization
NoSQL database setup for Kreeda Cricket Scoring
"""
import os
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings


def create_dynamodb_table_if_not_exists():
    """Create DynamoDB table if it doesn't exist (for local development)"""
    table_name = os.environ.get('DYNAMODB_TABLE', 'kreeda-cricket-data')
    region = os.environ.get('AWS_REGION', 'us-east-1')

    # Support for DynamoDB Local in development
    endpoint_url = os.environ.get('DYNAMODB_ENDPOINT_URL')
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

    if endpoint_url:  # DynamoDB Local
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key or 'dummy',
            aws_secret_access_key=aws_secret_key or 'dummy',
            region_name=region
        )
    else:  # AWS DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=region)

    try:
        # Check if table exists
        table = dynamodb.Table(table_name)
        table.table_status
        print(f"Table {table_name} already exists")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Creating table {table_name}...")

            # Create table with single table design
            table = dynamodb.create_table(
                TableName=table_name,
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
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST' if not endpoint_url else 'PROVISIONED',
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                } if endpoint_url else None
            )

            # Wait for table to be created
            table.wait_until_exists()
            print(f"Table {table_name} created successfully")
        else:
            raise e


def init_database():
    """Initialize database connection and create tables if needed"""
    try:
        create_dynamodb_table_if_not_exists()
        print("Database initialization completed successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise


# For backward compatibility with tests
def get_db():
    """Mock database dependency for tests - returns None since DynamoDB doesn't use sessions"""
    return None


# Mock Base class for backward compatibility
class Base:
    """Mock Base class for SQLAlchemy compatibility"""
    pass

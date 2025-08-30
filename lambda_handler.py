"""
AWS Lambda Handler for Kreeda Cricket Scoring
Serverless-optimized with DynamoDB (Always Free tier)
Optimized for cold start performance
"""
import json
import os
from typing import Dict, Any
import boto3
from mangum import Mangum

# Pre-import heavy dependencies at module level to reduce cold start time
from app.main import app

# Global variables for connection reuse - properly initialized
_dynamodb_service = None
_dynamodb_client = None

def get_dynamodb_service():
    """Create or reuse DynamoDB service for Lambda container reuse with proper error handling"""
    global _dynamodb_service
    if _dynamodb_service is None:
        try:
            table_name = os.environ.get('DYNAMODB_TABLE', 'kreeda-cricket-data')
            region_name = os.environ.get('AWS_REGION', 'us-east-1')

            # Use global DynamoDB client for connection reuse
            global _dynamodb_client
            if _dynamodb_client is None:
                endpoint_url = os.environ.get('DYNAMODB_ENDPOINT_URL')
                if endpoint_url:
                    # Local DynamoDB
                    _dynamodb_client = boto3.resource(
                        'dynamodb',
                        endpoint_url=endpoint_url,
                        aws_access_key_id='dummy',
                        aws_secret_access_key='dummy',
                        region_name=region_name
                    )
                else:
                    # AWS DynamoDB
                    _dynamodb_client = boto3.resource('dynamodb', region_name=region_name)

            from app.services.dynamodb_cricket_scoring import DynamoDBService
            _dynamodb_service = DynamoDBService(table_name=table_name, region_name=region_name)
            _dynamodb_service.dynamodb = _dynamodb_client  # Reuse connection

        except Exception as e:
            print(f"Failed to initialize DynamoDB service: {str(e)}")
            raise

    return _dynamodb_service


def cleanup_connections():
    """Clean up connections for Lambda container reuse"""
    global _dynamodb_service, _dynamodb_client

    try:
        # Close any open connections in the service
        if _dynamodb_service and hasattr(_dynamodb_service, 'dynamodb'):
            # Force garbage collection to clean up connections
            import gc
            gc.collect()

        # Reset global variables to force recreation on next invocation
        _dynamodb_service = None
        _dynamodb_client = None

        print("✅ Lambda connections cleaned up successfully")
    except Exception as e:
        print(f"⚠️  Warning: Connection cleanup failed: {str(e)}")
        # Don't raise exception during cleanup

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for API Gateway integration
    Optimized for serverless deployment with DynamoDB
    """
    try:
        # Initialize DynamoDB service
        service = get_dynamodb_service()

        # Create Mangum handler for FastAPI
        handler = Mangum(app, lifespan="off")

        # Process the event
        response = handler(event, context)

        # Add CORS headers for web deployment
        if 'headers' not in response:
            response['headers'] = {}

        response['headers'].update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Credentials': 'true'
        })

        return response

    except Exception as e:
        print(f"Lambda handler error: {str(e)}")

        # Clean up connections on error
        cleanup_connections()

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
    finally:
        # Clean up connections after successful execution
        # This ensures connections don't accumulate in Lambda container
        try:
            cleanup_connections()
        except Exception as cleanup_error:
            print(f"Warning: Final cleanup failed: {str(cleanup_error)}")

# Health check endpoint for CloudWatch monitoring
def health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Health check endpoint for monitoring"""
    try:
        service = get_dynamodb_service()

        # Test DynamoDB connection
        response = service.table.table_status

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'healthy',
                'service': 'kreeda-backend',
                'database': 'dynamodb',
                'table_status': response
            })
        }
    except Exception as e:
        return {
            'statusCode': 503,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'unhealthy',
                'error': str(e)
            })
        }

# Kreeda Backend API Documentation

## Overview

Kreeda Backend is a comprehensive cricket scoring API built with FastAPI, deployed on AWS Lambda with API Gateway, and using DynamoDB for data storage. The API supports user authentication via AWS Cognito and provides complete cricket match management functionality.

## Architecture

- **Framework**: FastAPI (Python 3.11)
- **Deployment**: AWS Lambda + API Gateway
- **Database**: Amazon DynamoDB (Single-table design)
- **Authentication**: AWS Cognito + JWT
- **CDN**: Amazon CloudFront
- **Monitoring**: CloudWatch

## Base URLs

- **Production**: `https://hz15ybpwbk.execute-api.us-east-1.amazonaws.com/prod`
- **Local Development**: `http://localhost:8000`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Most endpoints require a valid Bearer token in the Authorization header.

### Authentication Flow

1. **Register**: Create a new user account
2. **Login**: Obtain access token
3. **Use Token**: Include token in subsequent requests

### Token Usage

```bash
Authorization: Bearer <your_access_token>
```

## API Endpoints Overview

### 🔓 Public Endpoints (No Authentication Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API root information |
| `/health` | GET | Basic health check |
| `/health/detailed` | GET | Detailed health check with metrics |
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/auth/config` | GET | Authentication configuration |
| `/api/auth/oauth/*` | Various | OAuth2 authentication endpoints |
| `/api/cricket/health` | GET | Cricket API health check |
| `/api/v1/auth/config` | GET | V1 auth configuration |
| `/api/v1/cricket/health` | GET | V1 cricket API health check |

### 🔒 Protected Endpoints (Authentication Required)

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Authentication** | `/api/auth/me` | GET | Get current user profile |
| | `/api/auth/verify-token` | POST | Verify token validity |
| | `/api/auth/oauth/me` | GET | Get OAuth user info |
| | `/api/auth/oauth/logout` | POST | OAuth logout |
| **Teams** | `/api/cricket/teams` | POST | Create new team |
| | `/api/cricket/teams` | GET | List all teams |
| | `/api/cricket/teams/{team_id}` | GET | Get team details with players |
| **Players** | `/api/cricket/teams/{team_id}/players` | POST | Add player to team |
| | `/api/cricket/players/{player_id}` | PUT | Update player information |
| **Matches** | `/api/cricket/matches` | POST | Create new match |
| | `/api/cricket/matches/{match_id}` | GET | Get match details |
| | `/api/cricket/matches/{match_id}/toss` | POST | Perform coin toss |
| | `/api/cricket/matches/{match_id}/start` | POST | Start match |
| **Scoring** | `/api/cricket/matches/{match_id}/ball` | POST | Record ball |
| | `/api/cricket/matches/{match_id}/live` | GET | Get live score |
| | `/api/cricket/matches/{match_id}/last-ball` | DELETE | Undo last ball |
| **Live Updates** | `/api/cricket/matches/{match_id}/updates` | GET | Get match updates (polling) |

## Request/Response Schemas

### Authentication

#### User Registration

```json
{
  "username": "testuser",
  "email": "testuser@example.com",
  "password": "TestPass123!",
  "full_name": "Test User"
}
```

#### User Login

```json
{
  "username": "testuser",
  "password": "TestPass123!"
}
```

#### Token Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Teams

#### Create Team

```json
{
  "name": "Test Team",
  "short_name": "TT",
  "city": "Test City",
  "coach": "Test Coach",
  "home_ground": "Test Ground"
}
```

#### Team Response

```json
{
  "id": "uuid-string",
  "name": "Test Team",
  "short_name": "TT",
  "created_by": "user-uuid",
  "created_at": "2025-08-30T15:00:00.000000"
}
```

### Players

#### Create Player

```json
{
  "name": "Test Player",
  "jersey_number": 10
}
```

#### Update Player

```json
{
  "name": "Updated Player Name",
  "jersey_number": 11,
  "batting_order": 1,
  "is_captain": true,
  "is_wicket_keeper": false
}
```

### Matches

#### Create Match

```json
{
  "team_a_id": "team-uuid-1",
  "team_b_id": "team-uuid-2",
  "overs_per_side": 20,
  "venue": "Test Stadium",
  "match_type": "Limited Overs"
}
```

#### Toss Result

```json
{
  "toss_winner_id": "team-uuid",
  "batting_first_id": "team-uuid"
}
```

### Ball Scoring

#### Record Ball

```json
{
  "match_id": "match-uuid",
  "innings": 1,
  "over": 0,
  "ball": 1,
  "batsman_id": "player-uuid",
  "bowler_id": "player-uuid",
  "runs": 4,
  "is_wicket": false,
  "is_extra": false,
  "extra_runs": 0
}
```

## Error Responses

All endpoints return standardized error responses:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Authenticated requests**: 100 requests per minute
- **Unauthenticated requests**: 10 requests per minute
- Rate limits are enforced via Redis (production) or DynamoDB (fallback)

## Data Validation

All endpoints include comprehensive input validation:
- String length limits
- Numeric range validation
- Email format validation
- UUID format validation
- Required field validation

## Postman Collection

### Import Instructions

1. **Download the collection file**: `Kreeda_Backend_API.postman_collection.json`
2. **Download the environment file**: `Kreeda_Backend_Environment.postman_environment.json`
3. **Import into Postman**:
   - Open Postman
   - Click "Import" button
   - Select "File"
   - Choose both JSON files
4. **Select Environment**:
   - Click the environment dropdown (top-right)
   - Select "Kreeda Backend Environment"

### Using the Collection

1. **Set Environment Variables**:
   - Update `base_url` to match your environment
   - The collection will automatically store tokens and IDs

2. **Authentication Flow**:
   - Run "Register User" or "Login User"
   - The `access_token` will be automatically saved
   - All subsequent requests will use the token

3. **Testing Workflow**:

   ```
   3. **Testing Workflow**:

   ```text
   1. Register/Login → Get token
   2. Create Team → Get team_id
   3. Add Player → Get player_id
   4. Create Match → Get match_id
   5. Start Match → Begin scoring
   6. Record Balls → Update live score
   ```

### Environment Variables

| Variable | Description | Auto-updated |
|----------|-------------|--------------|
| `base_url` | API base URL | Manual |
| `access_token` | JWT access token | Auto |
| `user_id` | Current user ID | Auto |
| `team_id` | Selected team ID | Manual |
| `player_id` | Selected player ID | Manual |
| `match_id` | Selected match ID | Manual |

## Development Setup

### Local Development

1. **Clone repository**
2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run locally**:

   ```bash
   python -m uvicorn app.main:app --reload
   ```

4. **Access API**:
   - API: `http://localhost:8000`
   - Docs: `http://localhost:8000/docs`

### Environment Configuration

Create a `.env` file with:

```env
# AWS Configuration
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=your_pool_id
COGNITO_CLIENT_ID=your_client_id

# Database
DYNAMODB_TABLE=kreeda-cricket-data

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
APP_NAME=Kreeda Backend
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
```

## Deployment

The API is deployed using AWS SAM (Serverless Application Model):

```bash
# Build
sam build --template sam.yaml

# Deploy
sam deploy --stack-name kreeda-backend --template .aws-sam/build/template.yaml --resolve-s3 --capabilities CAPABILITY_IAM
```

## Monitoring

### Health Checks

- **Basic Health**: `/health`
- **Detailed Health**: `/health/detailed`
- **Cricket API Health**: `/api/cricket/health`

### CloudWatch Metrics

- Lambda duration and errors
- DynamoDB throttling
- API Gateway metrics
- Custom dashboards

## Security Features

- **JWT Authentication**: Secure token-based auth
- **CORS Protection**: Configured origins only
- **Rate Limiting**: Prevents abuse
- **Input Validation**: Comprehensive validation
- **HTTPS Only**: All traffic encrypted
- **Security Headers**: OWASP recommended headers

## Support

For issues or questions:

- Check the API documentation at `/docs`
- Review CloudWatch logs for errors
- Test with the provided Postman collection

## Version History

- **v1.0.0**: Initial release with full cricket scoring functionality
- AWS Cognito integration
- Complete match management
- Real-time scoring
- Live score updates
   ```

### Environment Variables

| Variable | Description | Auto-updated |
|----------|-------------|--------------|
| `base_url` | API base URL | Manual |
| `access_token` | JWT access token | Auto |
| `user_id` | Current user ID | Auto |
| `team_id` | Selected team ID | Manual |
| `player_id` | Selected player ID | Manual |
| `match_id` | Selected match ID | Manual |

## Development Setup

### Local Development

1. **Clone repository**
2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run locally**:

   ```bash
   python -m uvicorn app.main:app --reload
   ```

4. **Access API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

### Environment Variables

Create a `.env` file with:

```env
# AWS Configuration
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=your_pool_id
COGNITO_CLIENT_ID=your_client_id

# Database
DYNAMODB_TABLE=kreeda-cricket-data

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
APP_NAME=Kreeda Backend
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
```

## Deployment

The API is deployed using AWS SAM (Serverless Application Model):

```bash
# Build
sam build --template sam.yaml

# Deploy
sam deploy --stack-name kreeda-backend --template .aws-sam/build/template.yaml --resolve-s3 --capabilities CAPABILITY_IAM
```

## Monitoring

### Health Checks

- **Basic Health**: `/health`
- **Detailed Health**: `/health/detailed`
- **Cricket API Health**: `/api/cricket/health`

### CloudWatch Metrics

- Lambda duration and errors
- DynamoDB throttling
- API Gateway metrics
- Custom dashboards

## Security Features

- **JWT Authentication**: Secure token-based auth
- **CORS Protection**: Configured origins only
- **Rate Limiting**: Prevents abuse
- **Input Validation**: Comprehensive validation
- **HTTPS Only**: All traffic encrypted
- **Security Headers**: OWASP recommended headers

## Support

For issues or questions:

- Check the API documentation at `/docs`
- Review CloudWatch logs for errors
- Test with the provided Postman collection

## Version History

- **v1.0.0**: Initial release with full cricket scoring functionality
- AWS Cognito integration
- Complete match management
- Real-time scoring
- Live score updates

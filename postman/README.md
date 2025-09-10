# Kreeda API - Postman Test Automation Suite

Comprehensive test automation for the Kreeda Digital Cricket Scorekeeping Platform API. This suite validates all endpoints before production deployment.

## 🎯 Overview

This test automation covers:
- **29+ API endpoints** across all services
- **Authentication & Security** validation
- **Cricket Match Lifecycle** testing
- **Scoring Integrity System** verification
- **Statistics Engine** validation
- **Error Handling** verification
- **Data Cleanup** automation

## 📁 Files

### Collections
- `Kreeda_API_Complete_Tests.postman_collection.json` - **NEW**: Complete test automation suite
- `Kreeda_API.postman_collection.json` - Original collection (legacy)

### Environments
- `Kreeda_Development_TestAutomation.postman_environment.json` - **NEW**: Auto-configuring dev environment
- `Kreeda_Production_TestAutomation.postman_environment.json` - **NEW**: Production environment template
- `Kreeda_Development.postman_environment.json` - Original dev environment (legacy)
- `Kreeda_Production.postman_environment.json` - Original prod environment (legacy)

### Documentation
- `TEST_AUTOMATION_GUIDE.md` - **NEW**: Comprehensive testing guide
- `TESTING_WORKFLOW.md` - Original testing workflow
- `COLLECTION_SUMMARY.md` - Collection overview

## 🚀 Quick Start

### Option 1: Using Postman GUI (Recommended)

1. **Import Collection and Environment**:
   ```
   - Open Postman
   - Click "Import" → "Choose Files"
   - Select: Kreeda_API_Complete_Tests.postman_collection.json
   - Select: Kreeda_Development_TestAutomation.postman_environment.json
   ```

2. **Select Environment**:
   - Top-right dropdown → "Kreeda Development - Test Automation"

3. **Run Complete Test Suite**:
   - Click collection → "Run Collection" button
   - Click "Run Kreeda API - Complete Test Automation"
   - Monitor results in real-time

### Option 2: Using Command Line (CI/CD)

1. **Install Newman**:
   ```bash
   npm install -g newman
   ```

2. **Run Tests**:
   ```bash
   # Development tests
   ./scripts/run-tests.sh development

   # Production tests  
   ./scripts/run-tests.sh production

   # Generate HTML report
   ./scripts/run-tests.sh development html
   ```

## 📊 Test Results

### Success Criteria
- ✅ **Response Times**: < 5 seconds
- ✅ **Status Codes**: Proper HTTP responses
- ✅ **Authentication**: JWT tokens working
- ✅ **Data Validation**: All schemas match
- ✅ **Error Handling**: Proper error responses

### Test Categories
1. **🏥 Health Checks (5 tests)** - Service availability
2. **🔐 Authentication (3 tests)** - User registration/login/security
3. **👥 Teams Management (5 tests)** - CRUD operations
4. **🏏 Cricket Matches (5 tests)** - Match lifecycle
5. **🛡️ Integrity System (6 tests)** - Multi-scorer verification
6. **📊 Statistics (4 tests)** - Analytics engine
7. **🚨 Error Handling (3 tests)** - Security validation
8. **🧹 Cleanup (3 tests)** - Resource cleanup

**Total: 34 comprehensive tests**

## 🔧 Environment Variables

### Auto-Generated (No manual setup required)
The test suite automatically generates:
- `test_email` - Unique email using timestamp
- `test_username` - Unique username using timestamp  
- `test_team_name` - Unique team name using timestamp
- `access_token` - JWT token from authentication
- `team_a_id`, `team_b_id` - Team UUIDs
- `match_id`, `integrity_match_id` - Match UUIDs
- `captain_id` - User UUID

### Manual Configuration (Production Only)
For production testing, set these manually:
- `test_email` - Valid production test email
- `test_username` - Valid production test username
- `test_password` - Valid production test password

## 🎯 What Gets Tested

### Core API Functionality
✅ User registration and authentication  
✅ JWT token management and security  
✅ Team creation and management  
✅ Cricket match creation and lifecycle  
✅ Ball-by-ball scoring with validation  
✅ Match scorecard generation  

### Advanced Features  
✅ **NEW**: Multi-scorer integrity verification  
✅ **NEW**: Real-time match updates via WebSocket  
✅ **NEW**: Comprehensive statistics engine  
✅ **NEW**: Player career analytics  
✅ **NEW**: Team performance metrics  
✅ **NEW**: Match insights and commentary  

### System Reliability
✅ Health checks for all services  
✅ Error handling and validation  
✅ Unauthorized access prevention  
✅ Data format validation  
✅ Resource cleanup and management  

## 🔄 Automated Test Flow

1. **🏥 Health Checks**: Verify all services operational
2. **🔐 Registration**: Create test user with auto-generated data
3. **🔐 Authentication**: Login and obtain JWT token
4. **👥 Team Setup**: Create two teams for match testing
5. **🏏 Standard Match**: Create and test basic cricket match
6. **📊 Statistics**: Validate analytics engine
7. **🛡️ Integrity Match**: Test advanced scoring features
8. **🚨 Error Tests**: Validate security and error handling
9. **🧹 Cleanup**: Remove test data

## 📈 Production Readiness Validation

Before deploying to production, this suite ensures:

- [ ] All health endpoints responding (5/5)
- [ ] Authentication system secure (3/3) 
- [ ] CRUD operations functional (15+ tests)
- [ ] Cricket scoring accurate (10+ tests)
- [ ] Statistics engine working (4/4)
- [ ] Error handling proper (3/3)
- [ ] No test data remaining (cleanup working)

## 🔧 CI/CD Integration

### GitHub Actions Example
```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '16'
      - name: Install Newman
        run: npm install -g newman
      - name: Run API Tests
        run: ./scripts/run-tests.sh development junit
      - name: Upload Test Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test-results/
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    stages {
        stage('API Tests') {
            steps {
                sh 'npm install -g newman'
                sh './scripts/run-tests.sh development html'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'test-results',
                    reportFiles: 'kreeda-api-test-report.html',
                    reportName: 'API Test Report'
                ])
            }
        }
    }
}
```

## 🚨 Troubleshooting

### Common Issues
1. **Tests Fail at Health Checks**: Ensure Docker services are running
2. **Authentication Errors**: Check if test user already exists  
3. **Network Timeouts**: Verify base_url is accessible
4. **Environment Variables Missing**: Check if auto-generation worked

### Debug Steps
1. Run health checks individually
2. Check Postman console for detailed errors
3. Verify environment variable values
4. Test single requests manually
5. Check Docker logs: `docker-compose logs app`

## 📞 Support

For issues:
1. Check the comprehensive `TEST_AUTOMATION_GUIDE.md`
2. Review Postman console for error details
3. Verify Docker services: `docker-compose ps`
4. Check API docs: `http://localhost:8000/docs`

## 🎉 Benefits

This test automation provides:
- **Confidence**: 34 comprehensive tests validate functionality
- **Speed**: Automated execution in minutes vs hours of manual testing
- **Coverage**: Tests all endpoints including new features
- **Reliability**: Consistent, repeatable validation
- **CI/CD Ready**: Integrates with build pipelines
- **Documentation**: Self-documenting test cases

Perfect for ensuring your Kreeda API is production-ready! 🏏
- `GET /api/v1/teams/{team_id}/members` - Get team members
- `POST /api/v1/teams/{team_id}/join` - Join team

### Cricket Matches
- `GET /api/v1/matches/cricket` - Get all matches
- `POST /api/v1/matches/cricket` - Create new match
- `GET /api/v1/matches/cricket/{match_id}` - Get match details
- `POST /api/v1/matches/cricket/{match_id}/balls` - Record ball
- `GET /api/v1/matches/cricket/{match_id}/scorecard` - Get scorecard

## Environment Variables

### Authentication Variables (Auto-managed)
- `access_token` - JWT token (auto-populated after login)
- `token_type` - Token type ("bearer")
- `token_expiry` - Token expiration timestamp
- `user_id` - Current user ID

### Test Data Variables
- `test_email` - Test user email
- `test_username` - Test username  
- `test_full_name` - Test user full name
- `test_password` - Test user password

### Team Variables
- `team_name` - Team name for creation
- `team_short_name` - Team short name
- `team_logo_url` - Team logo URL
- `team_id` - Team ID (auto-populated)
- `captain_id` - Captain user ID

### Match Variables
- `match_id` - Match ID (auto-populated)
- `team_a_id` - First team ID
- `team_b_id` - Second team ID
- `venue` - Match venue
- `match_date` - Match date (ISO format)
- `overs_per_innings` - Overs per innings

### Ball Recording Variables
- `over_number` - Current over (1-20 for T20)
- `ball_number` - Ball in over (1-6)
- `bowler_id` - Bowler player ID
- `batsman_striker_id` - Striker batsman ID
- `batsman_non_striker_id` - Non-striker batsman ID
- `runs_scored` - Runs scored (0-6)
- `extras` - Extra runs
- `ball_type` - Ball type (legal, wide, no_ball, bye, leg_bye)
- `is_wicket` - Whether ball resulted in wicket
- `wicket_type` - Wicket type (bowled, caught, lbw, run_out, stumped)
- `dismissed_player_id` - Dismissed player ID
- `is_boundary` - Whether ball was boundary
- `boundary_type` - Boundary type (four, six)

## Usage Tips

### 1. Automatic Token Management
- The collection automatically handles JWT token storage and refresh
- Tokens are saved after successful login/registration
- Pre-request scripts check token expiry
- Use "Get Current User" to verify authentication status

### 2. Variable Auto-Population  
- Many variables are automatically populated from API responses
- Team IDs, Match IDs, User IDs are saved after creation
- This enables easy testing of dependent endpoints

### 3. Testing Workflow
1. Start with health checks to verify services are running
2. Register/Login to get authentication token
3. Create teams and save their IDs
4. Create matches using team IDs
5. Record balls and check scorecards

### 4. Error Handling
- Collection includes validation for common errors
- Check response status codes and error messages
- Refer to API documentation for detailed error codes

### 5. Data Validation
The API enforces strict validation:
- **Email**: Must be valid email format
- **Username**: 3-20 characters, alphanumeric + underscore
- **Password**: Minimum 8 characters
- **Team Names**: 1-100 characters
- **Ball Numbers**: 1-6 per over
- **Runs**: 0-6 per ball
- **UUIDs**: Valid UUID format for all ID fields

## Schema Validation

All requests validate against OpenAPI 3.1.0 schema:
- Request bodies validated against defined schemas
- Response formats match documented structures
- Field constraints enforced (min/max lengths, patterns, etc.)

## Production Usage

For production environment:
1. Update `base_url` in production environment to actual API URL
2. Use real credentials (not test data)
3. Be cautious with DELETE operations
4. Monitor rate limits and authentication expiry

## Support

For issues or questions:
1. Check API documentation at `/docs` endpoint
2. Verify environment variables are correctly set
3. Check authentication token validity
4. Review request/response payloads for validation errors

## Security Notes

- Never commit real passwords or tokens to version control
- Use environment-specific credentials
- Tokens expire and need renewal
- Production environment template has empty sensitive fields

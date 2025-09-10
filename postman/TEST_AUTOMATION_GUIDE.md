# Kreeda API Test Automation - Production Validation

This comprehensive test suite validates all Kreeda API endpoints before production deployment. The test automation covers authentication, team management, cricket matches, scoring integrity, and statistics.

## 🚀 Quick Start

### 1. Import Collections and Environments
1. Open Postman
2. Click **Import** → **Choose Files**
3. Select all files from the `postman/` directory:
   - `Kreeda_API_Complete_Tests.postman_collection.json`
   - `Kreeda_Development_TestAutomation.postman_environment.json`
   - `Kreeda_Production_TestAutomation.postman_environment.json`

### 2. Configure Environment
- **Development**: Select "Kreeda Development - Test Automation" environment
- **Production**: Select "Kreeda Production - Test Automation" environment

### 3. Run Complete Test Suite
1. Open **Kreeda API - Complete Test Automation** collection
2. Click **Run Collection** button
3. Select environment and click **Run**
4. Monitor results in real-time

## 📋 Test Categories

### 🏥 Health Checks (5 tests)
**Purpose**: Verify all services are operational before running main tests

- **Global Health Check**: Tests main application health endpoint
- **Users Service Health**: Validates user management service
- **Teams Service Health**: Validates team management service  
- **Cricket Service Health**: Validates cricket match service
- **Statistics Service Health**: Validates new statistics engine

**Success Criteria**: All services return healthy status with proper response format

### 🔐 Authentication (3 tests)
**Purpose**: Validate user registration, login, and security

- **Register New User**: Creates test user with auto-generated credentials
- **Login User**: Tests authentication with created credentials
- **Invalid Login Test**: Ensures unauthorized access is properly blocked

**Success Criteria**: JWT tokens generated, stored automatically, invalid access rejected

### 👥 Teams Management (5 tests)
**Purpose**: Test team creation, retrieval, and member management

- **Get User Teams**: Initially empty teams list
- **Create Team A**: Creates first test team with auto-generated name
- **Create Team B**: Creates second test team for match testing
- **Get Team Details**: Retrieves specific team information
- **Get Team Members**: Lists team members (captain included)

**Success Criteria**: Teams created with valid UUIDs, data persisted correctly

### 🏏 Cricket Matches - Standard (5 tests)
**Purpose**: Test basic cricket match functionality

- **Get All Matches**: Lists existing matches (initially empty)
- **Create Cricket Match**: Creates T20 match between Team A and B
- **Get Match Details**: Retrieves specific match information
- **Record First Ball**: Records boundary ball with proper validation
- **Get Match Scorecard**: Retrieves formatted scorecard

**Success Criteria**: Matches created, balls recorded, scorecard calculated correctly

### 🛡️ Cricket Integrity System (6 tests)
**Purpose**: Test enhanced scoring integrity features

- **Create Match with Integrity**: Creates match with integrity checking enabled
- **Assign Scorers**: Assigns scorer role to user
- **Get Scoring Status**: Retrieves scorer assignments and status
- **Record Ball with Integrity**: Records ball with multi-scorer verification
- **Get Integrity Match Scorecard**: Retrieves verified scorecard
- **Get Live Updates**: Tests real-time match updates

**Success Criteria**: Integrity features working, multi-scorer verification active

### 📊 Statistics Service (4 tests)
**Purpose**: Test comprehensive statistics engine

- **Get Player Statistics**: Retrieves batting/bowling career stats
- **Get Team Statistics**: Retrieves team performance metrics
- **Get Team Form**: Analyzes recent team performance
- **Get Match Insights**: Generates match analytics and key moments

**Success Criteria**: Statistics calculated correctly, insights generated

### 🚨 Error Handling Tests (3 tests)
**Purpose**: Validate proper error handling and security

- **Invalid Team ID Test**: Tests 404 handling for non-existent resources
- **Unauthorized Access Test**: Ensures endpoints require authentication
- **Invalid JSON Format Test**: Tests request validation

**Success Criteria**: Proper HTTP status codes, error messages formatted correctly

### 🧹 Cleanup (3 tests)
**Purpose**: Clean up test data after validation

- **Delete Team A**: Removes created test team
- **Delete Team B**: Removes second test team  
- **Clear Test Environment**: Cleans environment variables

**Success Criteria**: Resources cleaned up, environment reset

## 🔧 Environment Variables

### Auto-Generated Variables
These are automatically set during test execution:
- `test_email` - Unique test email using timestamp
- `test_username` - Unique username using timestamp
- `test_team_name` - Unique team name using timestamp
- `access_token` - JWT token from authentication
- `team_a_id`, `team_b_id` - Team UUIDs from creation
- `match_id`, `integrity_match_id` - Match UUIDs
- `captain_id` - User UUID

### Manual Configuration (Production Only)
For production testing, set these manually:
- `test_email` - Valid production test email
- `test_username` - Valid production test username  
- `test_password` - Valid production test password

## 📊 Test Results Analysis

### Success Metrics
- **Response Times**: All requests under 5 seconds
- **Status Codes**: 200/201/204 for successful operations, 400/401/404/422 for errors
- **Data Validation**: All response schemas match API specification
- **Authentication**: JWT tokens valid and properly managed
- **CRUD Operations**: Create, read, update, delete all functional

### Key Performance Indicators
- **Health Checks**: 100% pass rate indicates system ready
- **Authentication**: 100% pass rate indicates security working
- **Data Integrity**: All created resources have valid UUIDs
- **Error Handling**: Proper status codes for invalid requests
- **Statistics**: Analytics data calculated correctly

## 🚀 CI/CD Integration

### Newman Command Line
Run tests programmatically:

```bash
# Install Newman
npm install -g newman

# Run development tests
newman run "Kreeda_API_Complete_Tests.postman_collection.json" \
  -e "Kreeda_Development_TestAutomation.postman_environment.json" \
  --reporters html,cli \
  --reporter-html-export results.html

# Run production tests  
newman run "Kreeda_API_Complete_Tests.postman_collection.json" \
  -e "Kreeda_Production_TestAutomation.postman_environment.json" \
  --reporters junit,cli \
  --reporter-junit-export results.xml
```

### GitHub Actions Integration
```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run API Tests
        run: |
          npm install -g newman
          newman run postman/Kreeda_API_Complete_Tests.postman_collection.json \
            -e postman/Kreeda_Development_TestAutomation.postman_environment.json
```

## 🔍 Debugging Failed Tests

### Common Issues
1. **Service Not Running**: Check health endpoints first
2. **Authentication Failures**: Verify registration/login sequence
3. **Data Dependencies**: Ensure previous tests created required data
4. **Environment Variables**: Check auto-populated IDs are set
5. **Network Issues**: Verify base_url is accessible

### Troubleshooting Steps
1. Run health checks individually
2. Check Postman console for error details
3. Verify environment variable values
4. Test endpoints manually in Postman
5. Check API logs for server-side errors

## 📈 Test Coverage

### API Endpoints Covered
✅ **Authentication**: `/api/v1/auth/*` (3/3 endpoints)  
✅ **Teams**: `/api/v1/teams/*` (5/5 endpoints)  
✅ **Cricket Matches**: `/api/v1/matches/cricket/*` (5/5 endpoints)  
✅ **Cricket Integrity**: `/api/v1/matches/matches/*` (7/7 endpoints)  
✅ **Statistics**: `/api/v1/stats/*` (4/4 endpoints)  
✅ **Health Checks**: All service health endpoints  

**Total Coverage**: 29+ endpoints across all services

### Feature Coverage
✅ User registration and authentication  
✅ Team creation and management  
✅ Cricket match lifecycle  
✅ Ball-by-ball scoring  
✅ Multi-scorer verification  
✅ Real-time match updates  
✅ Statistics and analytics  
✅ Error handling and validation  
✅ Data cleanup and resource management  

## 🏆 Production Readiness Checklist

Before deploying to production, ensure:

- [ ] All health checks pass (5/5)
- [ ] Authentication system secure (3/3 tests pass)
- [ ] CRUD operations functional (10+ tests pass)
- [ ] Error handling proper (3/3 tests pass)
- [ ] Performance acceptable (< 5s response times)
- [ ] Data validation working (UUID formats, required fields)
- [ ] Security measures active (unauthorized access blocked)
- [ ] Statistics engine operational (4/4 tests pass)
- [ ] Integrity system functional (6/6 tests pass)
- [ ] Cleanup working (no test data left behind)

## 📞 Support

For test failures or questions:
1. Check the Postman console for detailed error messages
2. Verify environment configuration
3. Review API documentation at `/docs` endpoint
4. Check server logs for backend issues
5. Ensure Docker services are running for development tests

## 🔄 Continuous Testing

Run this test suite:
- **Before each deployment** to production
- **After API changes** to verify functionality
- **During development** to catch regressions
- **As part of CI/CD pipeline** for automated validation

This comprehensive test automation ensures the Kreeda API is production-ready with all features working correctly before deployment.

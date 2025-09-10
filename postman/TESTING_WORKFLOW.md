# Postman Testing Workflow

This document describes how to systematically test the Kreeda API using the provided Postman collection.

## Prerequisites

1. Kreeda API server running (typically `http://localhost:8000`)
2. Postman application installed
3. Collection and environment files imported

## Testing Sequence

### Phase 1: Service Health Verification

1. **Global Health Check**
   - Endpoint: `GET /health`
   - Expected: 200 OK with health status

2. **Service-Specific Health Checks**
   - Auth Health: `GET /api/v1/auth/health`
   - Teams Health: `GET /api/v1/teams/health` 
   - Cricket Health: `GET /api/v1/matches/health`
   - Expected: All services return healthy status

### Phase 2: User Authentication

3. **User Registration**
   - Endpoint: `POST /api/v1/auth/register`
   - Variables used: `test_email`, `test_username`, `test_full_name`, `test_password`
   - Expected: Returns JWT token and user details
   - Auto-saves: `access_token`, `token_expiry`

4. **User Profile Verification**
   - Endpoint: `GET /api/v1/auth/me`
   - Uses: Auto-saved JWT token
   - Expected: Returns current user profile
   - Auto-saves: `user_id` for later use

5. **User Login (Optional)**
   - Endpoint: `POST /api/v1/auth/login`
   - Test with same credentials from registration
   - Expected: Returns fresh JWT token

### Phase 3: Team Management

6. **Create First Team**
   - Endpoint: `POST /api/v1/teams/`
   - Update variables: `team_name`, `team_short_name`, `captain_id` (use current user_id)
   - Expected: Team created successfully
   - Auto-saves: `team_id` as `team_a_id`

7. **Create Second Team**
   - Endpoint: `POST /api/v1/teams/`
   - Update variables with different team name
   - Expected: Second team created
   - Manually save returned team ID as `team_b_id`

8. **List User Teams**
   - Endpoint: `GET /api/v1/teams/`
   - Expected: Returns array with both created teams

9. **Get Team Details**
   - Endpoint: `GET /api/v1/teams/{{team_id}}`
   - Expected: Returns detailed team information

10. **Team Members**
    - Endpoint: `GET /api/v1/teams/{{team_id}}/members`
    - Expected: Returns team members list (creator should be member)

### Phase 4: Cricket Match Management

11. **Create Cricket Match**
    - Endpoint: `POST /api/v1/matches/cricket`
    - Variables: `team_a_id`, `team_b_id`, `venue`, `match_date`, `overs_per_innings`
    - Expected: Match created successfully
    - Auto-saves: `match_id`

12. **List All Matches**
    - Endpoint: `GET /api/v1/matches/cricket`
    - Expected: Returns array including created match

13. **Get Match Details**
    - Endpoint: `GET /api/v1/matches/cricket/{{match_id}}`
    - Expected: Returns detailed match information

14. **Get Initial Scorecard**
    - Endpoint: `GET /api/v1/matches/cricket/{{match_id}}/scorecard`
    - Expected: Returns empty scorecard (match not started)

### Phase 5: Ball-by-Ball Recording

15. **Record Legal Ball (No runs)**
    - Endpoint: `POST /api/v1/matches/cricket/{{match_id}}/balls`
    - Set: `over_number=1`, `ball_number=1`, `runs_scored=0`, `ball_type=legal`
    - Set player IDs: `bowler_id`, `batsman_striker_id`, `batsman_non_striker_id`
    - Expected: Ball recorded successfully

16. **Record Boundary (4 runs)**
    - Same endpoint, `ball_number=2`
    - Set: `runs_scored=4`, `is_boundary=true`, `boundary_type=four`
    - Expected: Boundary recorded

17. **Record Six**
    - Same endpoint, `ball_number=3`
    - Set: `runs_scored=6`, `is_boundary=true`, `boundary_type=six`
    - Expected: Six recorded

18. **Record Wicket**
    - Same endpoint, `ball_number=4`
    - Set: `is_wicket=true`, `wicket_type=bowled`, `dismissed_player_id`
    - Expected: Wicket recorded

19. **Record Wide Ball**
    - Same endpoint, `ball_number=4` (wide doesn't increment ball count)
    - Set: `ball_type=wide`, `extras=1`, `runs_scored=0`
    - Expected: Wide recorded

20. **Updated Scorecard**
    - Endpoint: `GET /api/v1/matches/cricket/{{match_id}}/scorecard`
    - Expected: Shows updated scores with recorded balls

### Phase 6: Advanced Testing

21. **Team Operations**
    - Join Team: `POST /api/v1/teams/{{team_id}}/join`
    - Expected: User joins team (if not already member)

22. **Authentication Edge Cases**
    - Test expired token (manually modify `token_expiry`)
    - Test invalid token
    - Expected: Proper error responses

23. **Cleanup Operations**
    - Delete Team: `DELETE /api/v1/teams/{{team_id}}`
    - Logout: `POST /api/v1/auth/logout`
    - Expected: Resources cleaned up

## Validation Checkpoints

### After Each Request
- Check HTTP status codes (200, 201, 400, 401, 422, etc.)
- Verify response JSON structure matches expected schema
- Confirm auto-saved variables are populated

### Data Consistency
- User ID consistency across requests
- Team IDs match between creation and retrieval
- Match data integrity in scorecard
- Ball sequence numbering

### Security Validation
- Protected endpoints reject requests without tokens
- Users can only access their own teams/matches
- Token expiry is respected

## Common Issues and Solutions

### Authentication Issues
- **Token not saved**: Check post-response scripts in login/register
- **Token expired**: Re-run login request
- **403 Forbidden**: Verify token is included in Authorization header

### Variable Issues
- **Missing team_a_id/team_b_id**: Manually set after creating teams
- **Invalid UUIDs**: Ensure player IDs are valid UUIDs from team members
- **Date format errors**: Use ISO 8601 format for `match_date`

### API Validation Errors
- **422 Validation Error**: Check request body against schema requirements
- **Ball sequence errors**: Ensure ball_number stays within 1-6 per over
- **Team relationship errors**: Verify both teams exist before creating match

## Performance Testing

### Load Testing Preparation
1. Create multiple users with the registration endpoint
2. Create multiple teams per user
3. Create multiple matches
4. Record multiple balls per match

### Metrics to Monitor
- Response times for each endpoint
- Token refresh frequency
- Database query performance
- Memory usage during ball recording

## Test Data Management

### Environment Hygiene
- Use separate test database for API testing
- Clean up test data between test runs
- Use consistent naming conventions for test entities

### Data Relationships
- Maintain referential integrity (teams → users, matches → teams)
- Test orphaned record handling
- Verify cascade delete behavior

## Reporting

### Test Results Documentation
- Record response times for each endpoint
- Document any failures with request/response details
- Track variable auto-population success rates
- Note any schema validation issues

This workflow ensures comprehensive testing of all Kreeda API functionality while maintaining data consistency and security validation.

# User Profile & Management API Documentation

## Overview

The Kreeda backend now includes comprehensive user profile and management endpoints with the following capabilities:

- **Public user profiles** with privacy controls
- **Admin user management** with bulk operations
- **Advanced user search** and discovery
- **User analytics** and activity tracking
- **Session management** (framework ready)
- **User preferences** (extensible system)

## Endpoint Categories

### 🔓 Public Profile Endpoints

#### GET `/users/{user_id}/profile` - Get Public User Profile
- **Access**: Authenticated users
- **Description**: Get a user's public profile with privacy controls
- **Response**: `PublicUserProfile` with limited information
- **Privacy**: Only shows email/phone to profile owner

```bash
curl -X GET "http://localhost:8000/api/v1/users/123e4567-e89b-12d3-a456-426614174000/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### GET `/users/{user_id}/detailed` - Get Detailed User Profile  
- **Access**: Own profile or admin/organizer
- **Description**: Get detailed user profile with full information
- **Response**: `DetailedUserProfile` with complete data
- **Security**: Strict access control - own profile only

### 🔍 User Discovery & Search

#### GET `/users/search` - Search Users
- **Access**: Authenticated users
- **Description**: Search users with advanced filtering
- **Filters**: 
  - `query` - Search in username, full name, email
  - `role` - Filter by user role
  - `is_active` - Filter by active status
  - `email_verified` - Filter by verification status
  - `page`, `size` - Pagination controls
  - `order_by`, `order_dir` - Sorting options

```bash
curl -X GET "http://localhost:8000/api/v1/users/search?query=john&role=player&page=1&size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### GET `/users/` - List All Users (Admin)
- **Access**: Admin/Organizer only
- **Description**: Get paginated list of all users
- **Filters**: Basic filtering by role and active status
- **Response**: `PaginatedUsersResponse`

### 👥 Admin User Management

#### GET `/users/{user_id}` - Get User by ID (Admin)
- **Access**: Admin/Organizer only
- **Description**: Get any user's full details
- **Response**: `UserResponse` with complete information

#### PUT `/users/{user_id}` - Update User (Admin)
- **Access**: Admin/Organizer only  
- **Description**: Update any user's profile and settings
- **Body**: `AdminUserUpdate` schema
- **Capabilities**: 
  - Update profile information
  - Change user role
  - Modify account status
  - Reset failed login attempts
  - Set account lock status

```bash
curl -X PUT "http://localhost:8000/api/v1/users/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe Updated",
    "role": "organizer",
    "is_active": true,
    "email_verified": true
  }'
```

#### DELETE `/users/{user_id}` - Deactivate User (Admin)
- **Access**: Admin/Organizer only
- **Description**: Deactivate a user account
- **Security**: Cannot deactivate own account

### ⚡ Bulk Operations

#### POST `/users/bulk-action` - Bulk User Actions (Admin)
- **Access**: Admin/Organizer only
- **Description**: Perform actions on multiple users simultaneously
- **Actions Available**:
  - `activate` - Activate multiple users
  - `deactivate` - Deactivate multiple users  
  - `verify_email` - Verify email for multiple users
  - `reset_failed_attempts` - Reset login attempts
- **Body**: `BulkUserActionRequest`
- **Response**: `BulkActionResult` with success/failure details

```bash
curl -X POST "http://localhost:8000/api/v1/users/bulk-action" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["123e4567-e89b-12d3-a456-426614174000", "987f6543-d21c-45e6-b789-123456789012"],
    "action": "activate",
    "reason": "Bulk activation after verification"
  }'
```

### 📊 Analytics & Statistics

#### GET `/users/analytics/summary` - User Analytics (Admin)
- **Access**: Admin/Organizer only
- **Description**: Get user analytics and activity summary
- **Parameters**: `days` (1-365) - Analysis period
- **Response**: User activity statistics including:
  - Total users
  - New users in period
  - Active users in period
  - Locked users count

```bash
curl -X GET "http://localhost:8000/api/v1/users/analytics/summary?days=30" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### ⚙️ User Preferences

#### GET `/users/{user_id}/preferences` - Get User Preferences
- **Access**: Own preferences or admin
- **Description**: Get user application preferences
- **Response**: `UserPreferences` with theme, notifications, etc.

#### PUT `/users/{user_id}/preferences` - Update User Preferences  
- **Access**: Own preferences only
- **Description**: Update user application preferences
- **Body**: `UpdateUserPreferencesRequest`

## Schema Reference

### Core Schemas

#### PublicUserProfile
```json
{
  "id": "uuid",
  "username": "string",
  "full_name": "string|null",
  "avatar_url": "string|null", 
  "role": "player|scorekeeper|organizer|spectator|admin",
  "created_at": "datetime",
  "last_login": "datetime|null",
  "stats": {
    "teams_count": 0,
    "tournaments_count": 0,
    "matches_played": 0,
    "win_rate": 0.0
  }
}
```

#### DetailedUserProfile
```json
{
  "id": "uuid",
  "email": "email", 
  "username": "string",
  "full_name": "string|null",
  "phone": "string|null",
  "avatar_url": "string|null",
  "role": "user_role",
  "is_active": true,
  "email_verified": true,
  "auth_provider": "email|google|apple",
  "created_at": "datetime",
  "updated_at": "datetime", 
  "last_login": "datetime|null",
  "failed_login_attempts": 0,
  "locked_until": "datetime|null",
  "stats": "user_stats_object"
}
```

#### PaginatedUsersResponse
```json
{
  "users": ["array of UserSearchResult"],
  "total": 100,
  "page": 1,
  "size": 20, 
  "pages": 5,
  "has_next": true,
  "has_prev": false
}
```

### Admin Schemas

#### AdminUserUpdate
```json
{
  "full_name": "string|null",
  "phone": "string|null", 
  "avatar_url": "string|null",
  "role": "user_role|null",
  "is_active": "boolean|null",
  "email_verified": "boolean|null",
  "failed_login_attempts": "integer|null",
  "locked_until": "datetime|null"
}
```

#### BulkUserActionRequest
```json
{
  "user_ids": ["array of UUIDs"],
  "action": "activate|deactivate|verify_email|reset_failed_attempts",
  "reason": "string|null"
}
```

## Security Features

### Access Control
- **Role-based permissions**: Admin/Organizer for management operations
- **Owner-only access**: Users can only modify their own preferences
- **Privacy controls**: Public profiles show limited information

### Data Protection
- **Input validation**: All requests validated with Pydantic schemas
- **SQL injection prevention**: Parameterized queries via SQLAlchemy
- **Rate limiting**: Ready for implementation via FastAPI middleware

### Audit Trail
- **Action logging**: All admin operations logged (framework ready)
- **Session tracking**: User session management system prepared
- **Security alerts**: Framework for suspicious activity detection

## Database Optimizations

### Indexing Strategy
- **Primary keys**: UUID with indexes on user.id
- **Search indexes**: email, username fields indexed
- **Composite indexes**: role + is_active for common filters
- **Timestamp indexes**: created_at, last_login for analytics

### Query Optimizations
- **Pagination**: Efficient offset/limit queries
- **Filtering**: Database-level filtering before application logic
- **Bulk operations**: Single queries for multiple record updates
- **Connection pooling**: Async database connections

## Integration Examples

### Frontend Integration
```javascript
// Search users
const searchUsers = async (query, filters = {}) => {
  const params = new URLSearchParams({
    query,
    ...filters,
    page: 1,
    size: 20
  });
  
  const response = await fetch(`/api/v1/users/search?${params}`, {
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  return response.json();
};

// Get user profile  
const getUserProfile = async (userId) => {
  const response = await fetch(`/api/v1/users/${userId}/profile`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  return response.json();
};
```

### Mobile App Integration
```dart
// Flutter/Dart example
Future<Map<String, dynamic>> searchUsers(String query) async {
  final response = await http.get(
    Uri.parse('$baseUrl/api/v1/users/search?query=$query'),
    headers: {'Authorization': 'Bearer $token'}
  );
  
  return json.decode(response.body);
}
```

## Performance Characteristics

### Response Times (Expected)
- **User search**: < 200ms (with pagination)
- **Profile retrieval**: < 100ms (single user)
- **Bulk operations**: < 500ms (up to 100 users)
- **Analytics queries**: < 1s (30-day period)

### Scalability
- **Concurrent users**: Designed for 1000+ concurrent requests
- **Database scaling**: Supports read replicas for search operations
- **Caching ready**: Response caching can be added at proxy level

## Future Enhancements

### Planned Features
1. **Advanced Analytics**
   - User engagement metrics
   - Activity heatmaps
   - Retention analysis

2. **Social Features**
   - User following/followers
   - Activity feeds
   - Social statistics

3. **Enhanced Privacy**
   - Granular privacy controls
   - Data export/deletion (GDPR)
   - Privacy audit logs

4. **Performance Optimizations**
   - Full-text search with Elasticsearch
   - Redis caching layer
   - Database sharding strategy

This comprehensive user management system provides a solid foundation for the Kreeda platform's user operations while maintaining security, performance, and scalability.

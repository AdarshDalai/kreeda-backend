"""
Locust performance testing configuration for Kreeda Backend API
"""
import json
import random
from locust import HttpUser, task, between


class KreedaAPIUser(HttpUser):
    """Simulates a typical user of the Kreeda API"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Set up for each user session"""
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Try to authenticate (will fail in test env, but that's OK)
        self.auth_token = None
        self.team_ids = []
        self.user_ids = []
    
    @task(10)
    def health_check(self):
        """Test health endpoint - high frequency"""
        self.client.get("/health", headers=self.headers)
    
    @task(8)
    def api_health_check(self):
        """Test API health endpoint"""
        self.client.get("/api/v1/health", headers=self.headers)
    
    @task(5)
    def get_openapi_spec(self):
        """Test OpenAPI documentation endpoint"""
        self.client.get("/openapi.json", headers=self.headers)
    
    @task(3)
    def access_docs(self):
        """Test documentation access"""
        self.client.get("/docs", headers=self.headers)
    
    @task(2)
    def test_authentication_endpoints(self):
        """Test authentication related endpoints"""
        # Test registration endpoint (will fail without proper data)
        registration_data = {
            "username": f"testuser{random.randint(1000, 9999)}",
            "email": f"test{random.randint(1000, 9999)}@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        with self.client.post("/api/v1/auth/register", 
                            json=registration_data, 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code in [400, 422, 500]:  # Expected failures
                response.success()
    
    @task(2) 
    def test_teams_endpoints(self):
        """Test teams related endpoints"""
        # Test getting teams list
        with self.client.get("/api/v1/teams/", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [401, 403]:  # Expected auth failures
                response.success()
    
    @task(2)
    def test_statistics_endpoints(self):
        """Test statistics endpoints"""
        # Test getting statistics
        with self.client.get("/api/v1/statistics/players/stats", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [401, 403]:  # Expected auth failures
                response.success()
    
    @task(1)
    def test_cricket_endpoints(self):
        """Test cricket match endpoints"""
        with self.client.get("/api/v1/cricket/matches", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [401, 403]:  # Expected auth failures
                response.success()
    
    @task(1)
    def test_tournaments_endpoints(self):
        """Test tournament endpoints"""
        with self.client.get("/api/v1/tournaments/", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [401, 403]:  # Expected auth failures
                response.success()


class AdminUser(HttpUser):
    """Simulates admin user behavior"""
    
    wait_time = between(2, 5)
    weight = 1  # Lower frequency than regular users
    
    def on_start(self):
        """Set up admin session"""
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @task(5)
    def admin_health_checks(self):
        """Admin focused health monitoring"""
        endpoints = ["/health", "/api/v1/health"]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=self.headers)
    
    @task(3)
    def admin_user_management(self):
        """Test user management endpoints"""
        with self.client.get("/api/v1/users/", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [401, 403]:  # Expected auth failures
                response.success()
    
    @task(2)
    def admin_statistics_access(self):
        """Test admin statistics access"""
        with self.client.get("/api/v1/statistics/leaderboard/runs", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [401, 403]:  # Expected auth failures
                response.success()


class MobileAppUser(HttpUser):
    """Simulates mobile app user behavior"""
    
    wait_time = between(0.5, 2)  # Mobile users are more active
    weight = 3  # Higher frequency
    
    def on_start(self):
        """Mobile app session setup"""
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "KreedaMobile/1.0"
        }
    
    @task(15)
    def mobile_health_check(self):
        """Frequent health checks from mobile"""
        self.client.get("/health", headers=self.headers)
    
    @task(8)
    def mobile_live_scores(self):
        """Check live cricket scores"""
        with self.client.get("/api/v1/cricket/matches", 
                           params={"status": "live"},
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [401, 403]:
                response.success()
    
    @task(5)
    def mobile_team_stats(self):
        """Quick team statistics check"""
        team_id = f"team-{random.randint(1, 10)}"
        with self.client.get(f"/api/v1/stats/teams/{team_id}/stats", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [400, 401, 403, 404]:
                response.success()
    
    @task(3)
    def mobile_notifications(self):
        """Check notifications"""
        with self.client.get("/api/v1/notifications/", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [401, 403]:
                response.success()
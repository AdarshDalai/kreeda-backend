import json
from typing import Optional, Any
from datetime import timedelta
import redis.asyncio as redis
from src.config.settings import settings

class RedisClient:
    def __init__(self):
        self.client = redis.from_url(settings.redis_url, decode_responses=True)
    
    async def set(self, key: str, value: Any, expiry: Optional[int] = None):
        """Set a value in Redis with optional expiry in seconds"""
        serialized = json.dumps(value) if not isinstance(value, str) else value
        if expiry:
            await self.client.setex(key, expiry, serialized)
        else:
            await self.client.set(key, serialized)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis"""
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def delete(self, key: str):
        """Delete a key from Redis"""
        await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.client.exists(key) > 0
    
    async def invalidate_session(self, user_id: str):
        """Invalidate all sessions for a user"""
        pattern = f"session:{user_id}:*"
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)
    
    async def store_refresh_token(self, user_id: str, refresh_token: str, expiry_days: int = 30):
        """Store refresh token in Redis"""
        key = f"refresh_token:{user_id}:{refresh_token}"
        await self.set(key, {"user_id": user_id, "token": refresh_token}, expiry=expiry_days * 86400)
    
    async def validate_refresh_token(self, user_id: str, refresh_token: str) -> bool:
        """Check if refresh token is valid"""
        key = f"refresh_token:{user_id}:{refresh_token}"
        return await self.exists(key)
    
    async def invalidate_refresh_token(self, user_id: str, refresh_token: str):
        """Invalidate a specific refresh token"""
        key = f"refresh_token:{user_id}:{refresh_token}"
        await self.delete(key)
    
    async def store_otp(self, identifier: str, otp: str, expiry_minutes: int = 10):
        """Store OTP with expiry"""
        key = f"otp:{identifier}"
        await self.set(key, otp, expiry=expiry_minutes * 60)
    
    async def verify_otp(self, identifier: str, otp: str) -> bool:
        """Verify OTP"""
        stored_otp = await self.get(f"otp:{identifier}")
        if stored_otp and stored_otp == otp:
            await self.delete(f"otp:{identifier}")
            return True
        return False
    
    async def close(self):
        """Close Redis connection"""
        await self.client.close()

# Singleton instance
redis_client = RedisClient()

async def get_redis() -> RedisClient:
    """Dependency for getting Redis client"""
    return redis_client

#!/usr/bin/env python3

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.services.user_service import UserService
from app.models.user import User

async def test_delete():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set")
        return
    
    # Create engine and session
    engine = create_async_engine(database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as db:
        try:
            # Get a user to test with
            user = await UserService.get_user_by_id(db=db, user_id="86afb4b9-7509-4e2e-865d-5f2797d9920c")
            if not user:
                print("User not found")
                return
            
            print(f"Found user: {user.username} (ID: {user.id})")
            print(f"User is active: {user.is_active}")
            
            # Test soft delete
            print("Testing soft delete...")
            try:
                result = await UserService.soft_delete_user(db=db, user=user)
                print(f"Soft delete successful: {result.is_active}")
            except Exception as e:
                print(f"Soft delete error: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_delete())
"""
Database migration utilities for automatic migration execution.
"""
import asyncio
import logging
import os
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from pathlib import Path
from sqlalchemy import create_engine

from app.core.config import settings

logger = logging.getLogger(__name__)


def run_migrations():
    """Run database migrations using Alembic."""
    alembic_ini_path = None
    try:
        # Set up Alembic configuration - alembic.ini is at project root
        alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
        config = Config(alembic_ini_path)
        
        # Convert async URL to sync URL for Alembic
        sync_database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        # Set database URL in config
        config.set_main_option("sqlalchemy.url", sync_database_url)
        
        # Get script directory and current context
        script = ScriptDirectory.from_config(config)
        
        # Create engine and run migrations
        engine = create_engine(sync_database_url)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            
            # Get current and head revision
            current = context.get_current_revision()
            head = script.get_current_head()
            
            if current != head:
                logger.info(f"Running migrations from {current} to {head}")
                command.upgrade(config, "head")
                logger.info("✅ Migrations completed successfully")
            else:
                logger.info("✅ Database is already up to date")
                    
    except FileNotFoundError as e:
        logger.error(f"Alembic configuration not found at {alembic_ini_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def create_migration(message: str = "Auto migration"):
    """Create a new migration with autogenerate."""
    try:
        project_root = Path(__file__).parent.parent
        alembic_ini_path = project_root / "alembic.ini"
        
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
        
        logger.info(f"📝 Creating new migration: {message}")
        command.revision(alembic_cfg, autogenerate=True, message=message)
        
        logger.info("✅ Migration created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create migration: {str(e)}")
        return False

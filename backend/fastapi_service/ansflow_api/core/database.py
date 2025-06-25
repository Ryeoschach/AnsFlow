"""
Database connection and session management
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from ..config.settings import settings


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# Create async engine
engine = create_async_engine(
    settings.database.database_url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    echo=settings.debug,
    future=True,
    # For SQLite, use StaticPool to handle async operations
    poolclass=StaticPool if "sqlite" in settings.database.database_url else None,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Keep the old function name for backward compatibility
get_db = get_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session (alias for compatibility)
    """
    async for session in get_db():
        yield session


async def create_tables():
    """Create all database tables"""
    from ..models.database import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Import all models to ensure they are registered with the Base
    from ..models.database import (
        User, Project, Pipeline, PipelineRun, WebhookEvent, 
        Notification, ApiKey, SystemMetric, AuditLog
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

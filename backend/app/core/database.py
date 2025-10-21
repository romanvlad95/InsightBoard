"""
Database connection and session management.

This module sets up the asynchronous database engine and session management
for the application using SQLAlchemy. It provides a dependency `get_db`
for use in FastAPI routes to obtain a database session.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create an asynchronous engine based on the DATABASE_URL from settings.
# SQL statements are logged in the development environment.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    future=True,
)

# Create a configured "Session" class for use in the application.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# A sessionmaker instance for creating sessions outside the request-response cycle.
async_session_maker = AsyncSessionLocal

# Base class for declarative class definitions in SQLAlchemy models.
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get a database session.

    This is an asynchronous generator that creates and yields a new SQLAlchemy
    AsyncSession for each request. It ensures that the session is properly
    committed after the request is handled, or rolled back in case of an
    exception. The session is always closed at the end.

    Yields:
        An active and transactional SQLAlchemy AsyncSession.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

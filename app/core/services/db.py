# app/core/db.py

"""
Database + Redis core configuration
----------------------------------
Contains:
- SQLAlchemy async engine
- Session factory
- Base metadata (schema-aware)
- Database initialization helper
- Redis client & helpers
"""

from typing import AsyncGenerator

from sqlalchemy import MetaData, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)



from config import settings


# -----------------------------------------------------------------------------
# SQLAlchemy Base / Metadata
# -----------------------------------------------------------------------------
metadata = MetaData(schema="PropCare")
Base = declarative_base(metadata=metadata)


# -----------------------------------------------------------------------------
# Async Database Engine
# -----------------------------------------------------------------------------
DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=True,                           # log SQL statements (disable in prod)
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_timeout=settings.POOL_TIME_OUT,
    pool_pre_ping=True,                  # checks if connection is alive
)


# Session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes.
    Yields an async DB session.
    """
    async with AsyncSessionLocal() as session:
        yield session


# -----------------------------------------------------------------------------
# Database Initialization (Run on startup)
# -----------------------------------------------------------------------------
async def init_models():
    """
    Initialize database tables under schema "PropCare".
    Creates schema and all SQLAlchemy models.
    """
    async with engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "PropCare"'))
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully.")


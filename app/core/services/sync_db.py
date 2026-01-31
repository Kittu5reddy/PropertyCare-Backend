from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

# Sync engine (used ONLY by Celery)
sync_engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Sync session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

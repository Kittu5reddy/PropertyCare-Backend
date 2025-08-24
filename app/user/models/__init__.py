from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData
from config import settings
from typing import AsyncGenerator
from sqlalchemy import text
metadata = MetaData(schema="PropCare")
Base = declarative_base(metadata=metadata)

from app.user.models.users import User,UserNameUpdate
from app.user.models.personal_details import PersonalDetails,PersonalDetailsHistory
from app.user.models.property_details import PropertyHistory,PropertyDetails
from app.user.models.usersubscriptiontransaction import UserSubscriptionTransaction,UserSubscriptionTransactionHistory
from app.user.models.documents import PropertyDocuments,DocumentHistory,UserDocuments
from app.admin.models.admins import Admin
from app.admin.models.subscriptions import Subscription,SubscriptionHistory
from app.admin.models.admin_details import AdminDetails
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# from sqlalchemy.orm import declarative_base
# from app.user.models import Base

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_timeout=settings.POOL_TIME_OUT,
    pool_pre_ping=True
)





async def init_models():
    async with engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "PropCare"'))
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully.")

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

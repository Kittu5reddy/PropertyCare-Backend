from sqlalchemy.orm import declarative_base
from config import Config
Base=declarative_base()
from .users import User
from .personal_details import PCUser
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.models import Base

DATABASE_URL = "postgresql+asyncpg://postgres:kaushik@localhost:5432/Propertycare"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=Config.POOL_SIZE,
    max_overflow=Config.MAX_OVERFLOW,
    pool_timeout=Config.POOL_TIME_OUT,
)

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully.")

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

from sqlalchemy.orm import declarative_base
from typing import Any
from sqlalchemy import MetaData
from config import settings
from typing import AsyncGenerator
from sqlalchemy import text
metadata = MetaData(schema="PropCare")
Base = declarative_base(metadata=metadata)
from fastapi import Depends
import json
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import redis.asyncio as redis
# from sqlalchemy.orm import declarative_base
# from app.user.models import Base
REDIS_EXPIRE_TIME=settings.REDIS_EXPIRE_TIME
DATABASE_URL = settings.DATABASE_URL

# Create a global Redis client
pool = redis.ConnectionPool(
    host="localhost",
    port=6379,
    # password="YOUR_STRONG_PASSWORD",
    max_connections=50,   # prevents too many open sockets
    decode_responses=True,
    socket_connect_timeout=5,  # fail fast
    socket_timeout=5
)
redis_client = redis.Redis.from_pool(pool)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_timeout=settings.POOL_TIME_OUT,
    pool_pre_ping=True
)


from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)



async def init_models():
    async with engine.begin() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "PropCare"'))
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully.")

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# print(redis_client)
async def get_redis():
    yield redis_client




async def redis_set_data(cache_key: str, data: Any,time:int=REDIS_EXPIRE_TIME):

    value = json.dumps(data)  # serialize
    await redis_client.setex(
        name=cache_key,
        time=REDIS_EXPIRE_TIME,
        value=value
    )


async def redis_get_data(cache_key: str):

    value = await redis_client.get(cache_key)
    if value is None:
        return {}
    return json.loads(value)  # deserialize



async def redis_update_data(
    cache_key: str,
    data: Any,
    redis_client: redis.Redis = Depends(get_redis)
):
    value = json.dumps(data)
    # Overwrites old value with new one & resets TTL
    await redis_client.setex(
        name=cache_key,
        time=REDIS_EXPIRE_TIME,
        value=value
    )
    return True



async def redis_delete_data(
    cache_key: list
):
    result = await redis_client.delete(cache_key)
    return result > 0   # returns True if key was deleted

async def redis_delete_pattern(pattern: str):
    # scan_iter returns an async iterator over keys matching the pattern
    async for key in redis_client.scan_iter(match=pattern):
        await redis_client.delete(key)

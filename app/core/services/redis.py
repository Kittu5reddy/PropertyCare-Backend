
import json
from fastapi import Depends
import redis.asyncio as redis
from typing import Any
from config import settings



# -----------------------------------------------------------------------------
# Redis Configuration
# -----------------------------------------------------------------------------
REDIS_EXPIRE_TIME = settings.REDIS_EXPIRE_TIME

redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST or "localhost",
    port=settings.REDIS_PORT or 6379,
    max_connections=50,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)

redis_client = redis.Redis.from_pool(redis_pool)


async def get_redis():
    """Dependency for FastAPI routes."""
    yield redis_client


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
    
    print("deleted")
    result = await redis_client.delete(cache_key)
    return result > 0   # returns True if key was deleted

async def redis_delete_pattern(pattern: str):
    # scan_iter returns an async iterator over keys matching the pattern
    async for key in redis_client.scan_iter(match=pattern):
        await redis_client.delete(key)

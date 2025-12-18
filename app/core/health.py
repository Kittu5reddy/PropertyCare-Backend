# app/core/health.py
from sqlalchemy import text
from app.core.services.db import engine

async def check_postgres():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True


# app/core/health.py
from app.core.services.redis import redis_client

async def check_redis():
    pong = await redis_client.ping()
    if pong is not True:
        raise Exception("Redis PING failed")
    return True

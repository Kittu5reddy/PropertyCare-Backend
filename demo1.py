import asyncio
import asyncpg

async def test_connection():
    conn = await asyncpg.connect("postgresql://kaushik_user:9wEDihstcFS4ytxyqOpQofJo8JpiehM2@dpg-d1l6ofemcj7s73brmicg-a.oregon-postgres.render.com:5432/kaushik")
    print("Connected successfully!")
    await conn.close()

asyncio.run(test_connection())

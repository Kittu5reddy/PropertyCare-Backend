from app import create_app
import uvicorn

app=create_app()
from app.controllers.auth.utils import create_access_token

import asyncio
from app.models import engine, Base


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created.")



if __name__=="__main__":
    asyncio.run(init_models())
    uvicorn.run("run:app", host= "127.0.0.1", port= 8000,reload=True)
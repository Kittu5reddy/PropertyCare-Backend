from app import create_app
from app.user.models import engine, Base
import uvicorn
from app.user.models import init_models

app=create_app()
import asyncio



if __name__=="__main__":
    asyncio.run(init_models())
    uvicorn.run("run:app", host= "0.0.0.0", port= 8000,reload=True)
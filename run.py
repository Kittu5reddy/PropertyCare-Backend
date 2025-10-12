from app import create_app
from app.core.models import engine, Base
import uvicorn
from app.core.models import init_models
import logging
import time
from fastapi import Request
from logging_config import logger, error_logger
import asyncio
import traceback
from fastapi.responses import JSONResponse
app=create_app()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Log detailed traceback in error log
        error_details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        error_logger.error(
            f"500 Error on {request.method} {request.url.path}\n"
            f"Exception: {exc}\n"
            f"Traceback:\n{error_details}"
        )
        print(f"500 ERROR: {exc}")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    duration = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {duration:.2f}ms")
    return response

if __name__=="__main__":
    asyncio.run(init_models())
    uvicorn.run("run:app", host= "0.0.0.0", port= 8000)
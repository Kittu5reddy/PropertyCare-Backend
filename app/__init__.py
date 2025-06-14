from fastapi import FastAPI
from app.controllers.auth.main import auth

def create_app():
    app=FastAPI()
    app.include_router(auth)
    return app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.auth.main import auth
from app.controllers.forms.main import form

def create_app():
    app = FastAPI()
    allow_origins=["http://localhost:5173"]

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,  # Change to specific domains in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth)
    app.include_router(form)
    return app

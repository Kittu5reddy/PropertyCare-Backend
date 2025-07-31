from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.user.controllers.auth.main import auth
from app.user.controllers.forms.main import form
from app.user.controllers.dashboard.main import dash

def create_app():
    app = FastAPI()
    allow_origins=["http://localhost:3000","https://propertycare-nine.vercel.app"]

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,  # Change to specific domains in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth)
    app.include_router(dash)
    app.include_router(form)
    return app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.user.controllers.auth.main import auth
from app.user.controllers.forms.main import form
from app.user.controllers.surveillance.main import surveillance
from app.user.controllers.subscrptions.main import sub
from app.user.controllers.dashboard.main import dash
from app.admin.controllers.auth import admin
from app.admin.controllers.user import admin_user
from app.user.controllers.properties.main import prop

def create_app():
    app = FastAPI()
    allow_origins=["http://localhost:3000",
                   "http://localhost:5173",
                   "https://user.vibhoospropcare.com",
                   "https://admin.vibhoospropcare.com",
                   "https://propertycare-nine.vercel.app"]

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,  # Change to specific domains in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth)
    app.include_router(sub)
    app.include_router(admin) 
    app.include_router(admin_user) 
    app.include_router(dash)
    app.include_router(form)
    app.include_router(prop)
    app.include_router(surveillance)
    return app

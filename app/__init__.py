from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.controllers.auth.main import auth
from app.user.controllers.forms.main import form
from app.user.controllers.surveillance.main import surveillance
from app.user.controllers.subscrptions.main import sub
from app.user.controllers.dashboard.main import dash
from app.admin.controllers.auth.main import admin_auth
from app.admin.controllers.services.main import admin_services
from app.user.controllers.properties.main import prop
from app.user.controllers.services.main import services
from app.core.controllers.emails.main import email

def create_app():
    app = FastAPI()
    allow_origins=["http://localhost:3000",
                   "http://localhost:5173",
                   "https://user.vibhoospropcare.com",
                   "https://admin.vibhoospropcare.com",
                   "https://vibhoospropcare.com",
                   "https://www.vibhoospropcare.com",
                   "https://propertycare-nine.vercel.app"]

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth)
    app.include_router(sub)
    app.include_router(services)
    app.include_router(admin_auth) 
    app.include_router(admin_services) 
    app.include_router(dash)
    app.include_router(form)
    app.include_router(prop)
    app.include_router(email)
    app.include_router(surveillance)
    return app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.controllers.auth.main import auth
from app.user.controllers.forms.main import form
from app.user.controllers.subscriptions.main import subscriptions
from app.user.controllers.surveillance.main import surveillance
from app.user.controllers.dashboard.main import dash
from app.admin.controllers.auth.main import admin_auth
from app.admin.controllers.subscriptions.main import admin_subscriptions

from app.user.controllers.properties.main import prop
from app.user.controllers.services.main import services
from app.core.controllers.emails.main import email
from app.user.controllers.feedback.main import feedback
from app.admin.controllers.dashboard.main import admin_dash
from config import settings


ALLOW_ORIGINS=settings.allow_origins

def create_app():
    app = FastAPI(title="Vibhoos PropCare")

    allow_origins=ALLOW_ORIGINS

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth)
    app.include_router(services)
    app.include_router(admin_auth) 
    app.include_router(admin_dash) 
    app.include_router(dash)
    app.include_router(subscriptions)
    app.include_router(admin_subscriptions)
    app.include_router(form)
    app.include_router(prop)
    app.include_router(feedback)
    app.include_router(email)
    app.include_router(surveillance)
    return app

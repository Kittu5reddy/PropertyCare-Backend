from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware









#===============================================
#          user API ROUTES
#===============================================
from app.user.controllers.auth.main import auth
# from app.user.controllers.auth.google.main import google_auth
# from app.user.controllers.forms.main import form
# from app.user.controllers.subscriptions.main import subscriptions
# from app.user.controllers.surveillance.main import surveillance
from app.user.controllers.dashboard.main import dash
from app.user.controllers.property.main import prop
# from app.user.controllers.services.main import services
from app.user.controllers.emails.main import email
from app.user.controllers.feedback.main import feedback
from app.user.controllers.profile.main import profile
from config import settings

ALLOW_ORIGINS = settings.allow_origins


def create_app(docs_url="/docs", redoc_url="/redocs", openapi_url="/openapi.json"):
    app = FastAPI(
        title="Vibhoos PropCare",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url
    )



    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth)
    # app.include_router(google_auth)
    # app.include_router(services)
    # app.include_router(admin_auth)
    # app.include_router(admin_dash)
    app.include_router(dash)
    # app.include_router(subscriptions)
    # app.include_router(admin_subscriptions)
    # app.include_router(form)
    app.include_router(prop)
    app.include_router(feedback)
    app.include_router(profile)
    app.include_router(email)
    # app.include_router(surveillance)

    return app

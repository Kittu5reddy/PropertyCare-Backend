from fastapi import APIRouter,Depends
from app.user.controllers.auth.main import oauth2_scheme,get_current_user,get_db



sub=APIRouter(prefix='/subscrptions',tags=['subscrptions'])



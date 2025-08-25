from fastapi import APIRouter,Depends
from app.user.controllers.auth.main import oauth2_scheme
from app.user.controllers.forms.utils import get_image
from app.user.controllers.auth.main import get_current_user
from app.user.models.property_details import PropertyDetails
from .utils import get_property_details
from app.user.models import AsyncSession,get_db
from sqlalchemy import select
from app.user.controllers.forms.utils import list_s3_objects
dash=APIRouter(prefix='/dash',tags=['/dash'])


@dash.get("/property-details")
async def get_property_data(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user(token, db)
    data = await get_property_details(user.user_id, db)
    return {"properties": data}

@dash.get("/monthly-photos")
async def get_property_data(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user(token, db)
    data = await get_property_details(user.user_id, db)   
    return {"properties": data}




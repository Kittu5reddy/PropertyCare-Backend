from fastapi import APIRouter,Depends
from app.user.controllers.auth.main import oauth2_scheme
from app.user.controllers.forms.utils import get_image
from app.user.controllers.auth.main import get_current_user
from app.user.models.property_details import PropertyDetails
from .utils import get_property_details
from app.user.models import AsyncSession,get_db,redis_get_data,redis_set_data
from sqlalchemy import select
from app.user.controllers.forms.utils import list_s3_objects
dash=APIRouter(prefix='/dash',tags=['/dash'])


@dash.get("/property-details")
async def get_property_data(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user(token, db)
    cache_key=f"user:{user.user_id}:property-details"
    cache_data=await redis_get_data(cache_key)
    if cache_data:
        print('hit')
        return cache_data
    data = await get_property_details(user.user_id, db,5)
    # print(data)
    data={"data":data}
    await redis_set_data(cache_key,data)
    print('miss')
    return data

@dash.get("/monthly-photos")
async def get_property_data(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user(token, db)
    cache_key=f"user:{user.user_id}:property-details"
    cache_data=await redis_get_data(cache_key)
    if cache_data:
        print('hit')
        return cache_data
    data = await get_property_details(user.user_id, db,5)
    # print(data)
    data={"data":data}
    await redis_set_data(cache_key,data)
    print('miss')
    return data






from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.core.models import redis_get_data, redis_set_data ,get_db # adjust import
from app.core.models.services import Services

services = APIRouter(prefix='/services',tags=['services'])

@services.get('/get-services-list')
async def get_services_list(db: AsyncSession = Depends(get_db)):
    try:
        cache_key = "services:list"

        cached_data = await redis_get_data(cache_key)
        if cached_data:
            return cached_data


        result = await db.execute(
            select(Services).where(Services.is_active == True)
        )
        services_list = result.scalars().all() 

        from datetime import datetime

        data = []
        for service in services_list:
            data.append({
        "id": service.id,
        "service_id": service.service_id,
        "service_name": service.service_name,
        "services": service.services,
        "is_active": service.is_active,
        "approx_cost_usd": service.approx_cost_usd,
        "approx_cost_inr": service.approx_cost_inr,
        "durations": service.durations,
        "applicable_to": service.applicable_to,
        "comments": service.comments,
        "created_by": service.created_by,
        "created_at": service.created_at.isoformat() if service.created_at else None,
        "updated_at": service.updated_at.isoformat() if service.updated_at else None,
        })



        await redis_set_data(cache_key, data)

        return data

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

# @services.post('/add-services')
# async def add_services(payload:):

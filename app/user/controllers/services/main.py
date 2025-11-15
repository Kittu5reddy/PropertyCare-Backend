from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from app.core.models.property_details import PropertyDetails
from app.core.controllers.auth.main import oauth2_scheme,get_current_user
from app.core.models import redis_get_data, redis_set_data ,get_db,AsyncSession 
from app.core.models.services import Services

services = APIRouter(prefix='/services',tags=['services'])
@services.get('/get-services-list')
async def get_services_list(db: AsyncSession = Depends(get_db)):
    try:
        cache_key = "services:list"

        # 1️⃣ Return from cache if available
        cached_data = await redis_get_data(cache_key)
        if cached_data:
            return cached_data

        # 2️⃣ Fetch only required fields (faster)
        stmt = select(
            Services.service_id,
            Services.service_name,
            Services.category,
            Services.services,
            Services.starting_price,
            Services.short_comments,
            Services.is_active
        ).where(Services.is_active == True)

        result = await db.execute(stmt)
        rows = result.mappings().all()   # returns dict-like rows

        # Convert rows to list of dicts
        data = [
            {
                "service_id": row["service_id"],
                "service_name": row["service_name"],
                "service_category": row["category"],
                "services": row["services"],
                "starting_price": row["starting_price"],
                "short_comments": row["short_comments"],
                "is_active": row["is_active"],
                "image_url":"s3"
            }
            for row in rows
        ]

        # 3️⃣ Save to Redis
        await redis_set_data(cache_key, data)

        return data

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

@services.get("/get-suitable-services-property/{category}")
async def get_suitable_services_property(
    category: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Normalize category (for CASE-INSENSITIVE matching)
        category = category.upper()

        # Validate input
        valid_categories = {"FLAT", "PLOT"}
        if category not in valid_categories:
            raise HTTPException(status_code=400, detail="Invalid category. Use FLAT or PLOT")

        # Get authenticated user
        user = await get_current_user(token, db)

        # Fetch properties of this user & category
        stmt = select(
            PropertyDetails.property_id,
            PropertyDetails.property_name,
        ).where(
            PropertyDetails.user_id == user.user_id,
            PropertyDetails.type == category
        )

        result = await db.execute(stmt)
        rows = result.mappings().all()   # returns dict-like rows instead of tuples

        properties = [
            {
                "property_id": row["property_id"],
                "property_name": row["property_name"]
            }
            for row in rows
        ]

        return {
            "status": "success",
            "user_id": user.user_id,
            "category": category,
            "total_properties": len(properties),
            "properties": properties
        }

    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch property info: {str(e)}"
        )

@services.post('/add-services')
async def add_services():
    pass
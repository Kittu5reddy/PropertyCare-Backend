from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from app.core.models.property_details import PropertyDetails
from app.core.controllers.auth.main import oauth2_scheme,get_current_user
from app.core.models import redis_get_data, redis_set_data ,get_db,AsyncSession 
from app.core.models.services import Services
from config import settings

from app.user.controllers.forms.utils import generate_cloudfront_presigned_url,check_object_exists
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
        # Normalize input
        category = category.upper()
        valid_categories = {"FLAT", "PLOT"}

        if category not in valid_categories:
            raise HTTPException(status_code=400, detail="Invalid category. Use FLAT or PLOT")

        # Auth user
        user = await get_current_user(token, db)

        # Fetch user properties by category
        stmt = select(
            PropertyDetails.property_id,
            PropertyDetails.property_name,
            PropertyDetails.city
        ).where(
            PropertyDetails.user_id == user.user_id,
            PropertyDetails.type == category
        )

        result = await db.execute(stmt)
        rows = result.mappings().all()

        if not rows:
            return {
                "status": "success",
                "user_id": user.user_id,
                "category": category,
                "total_properties": 0,
                "properties": []
            }

        properties = []

        for row in rows:
            property_id = row["property_id"]

            # Correct S3 key
            s3_key = f"property/{property_id}/legal_documents/property_photo.png"

            # Check S3 file existence
            exists = await check_object_exists(s3_key)

            if exists:
                # Generate CloudFront signed URL
                image_url = await generate_cloudfront_presigned_url(s3_key)
            else:
                # Fallback image
                image_url = settings.DEFAULT_IMG_URL

            properties.append({
                "property_id": property_id,
                "property_name": row["property_name"],
                "property_image_url": image_url,
                "property_address": row["city"]
            })

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
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch property info: {e}")

@services.post('/add-services')
async def add_services():
    pass
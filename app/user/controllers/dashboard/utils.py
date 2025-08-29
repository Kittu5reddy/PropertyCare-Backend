from sqlalchemy import select
from app.user.models.property_details import PropertyDetails
from app.user.models import get_db,AsyncSession
from fastapi import Depends
from app.user.controllers.forms.utils import list_s3_objects,get_image,check_object_exists
from datetime import date
from config import settings
async def get_property_details(
    user_id: str,
    db: AsyncSession,
    limit: int = 3
) -> list[dict]:
    query = (
        select(
            PropertyDetails.property_id,
            PropertyDetails.property_name,
            PropertyDetails.size,
            PropertyDetails.type,
            PropertyDetails.city,

        )
        .where(PropertyDetails.user_id == user_id)
        .limit(limit)  # limit on properties
    )
    result = await db.execute(query)
    rows = result.all()

    data = []
    for row in rows:
        photos = await check_object_exists(f"property/{row.property_id}/legal_documents/property_image..png")
        data.append({
            "property_id": row.property_id,
            "location":row.city,
            "name": row.property_name,
            "size": row.size,
            "type": row.type,
             "subscription":str(date.today()) ,
            "status": 'active',
            "image_url": get_image(f"/property/{row.property_id}/legal_documents/property_image..png") if photos else settings.DEFAULT_IMG_URL
        })
    return data
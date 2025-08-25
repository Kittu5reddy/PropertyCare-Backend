from sqlalchemy import select
from app.user.models.property_details import PropertyDetails
from app.user.models import get_db,AsyncSession
from fastapi import Depends
from app.user.controllers.forms.utils import list_s3_objects,get_image

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
            PropertyDetails.type
        )
        .where(PropertyDetails.user_id == user_id)
        .limit(limit)  # limit on properties
    )
    result = await db.execute(query)
    rows = result.all()

    data = []
    for row in rows:
        images = await list_s3_objects(
            prefix=f"property/{row.property_id}/original_photos",
            limit=1 
        )
        if images:
            images=get_image("/"+images[0])
        else:
            images=None
        data.append({
            "property_id": row.property_id,
            "property_name": row.property_name,
            "size": row.size,
            "type": row.type,
            "images": images if images else """https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1075&q=80"""
        })
    return data
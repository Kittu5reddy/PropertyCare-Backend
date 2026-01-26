from app.core.models.property_details import PropertyDetails
from fastapi import APIRouter,HTTPException,Depends
from fastapi.security import OAuth2PasswordBearer
from app.admin.controllers.auth.utils import get_current_admin
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
from app.core.services.db import AsyncSession,get_db
admin_properties=APIRouter(prefix='/admin_properties',tags=['Admin Properties'])
from sqlalchemy import select
from app.core.services.s3 import get_image_cloudfront_signed_url


from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

@admin_properties.get("/get-properties")
async def get_properties(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    start: int = 0,
    limit: int = 10
):
    # 🔒 Auth check
    admin = await get_current_admin(token=token, db=db)


    stmt = (
        select(PropertyDetails)
        .order_by(PropertyDetails.id.desc())  # 👈 important
        .offset(start)
        .limit(limit)
    )

    result = await db.execute(stmt)
    properties = result.scalars().all()
    response = [
    {
        "image_url": await get_image_cloudfront_signed_url(f"/property/{record.property_id}/legal_documents/property_photo.png"),
        "is_active": record.active_sub,
        "property_id": record.property_id,
        "property_name": record.property_name,
        "user_id": record.user_id
    }
    for record in properties
]

    
    return {
        "start": start,
        "limit": limit,
        "count": len(properties),
        "data": response
    }


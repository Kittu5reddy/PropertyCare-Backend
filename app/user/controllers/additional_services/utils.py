from app.core.models.additional_services import AdditionalServices
from app.core.services.db import AsyncSession,get_db
from fastapi import Depends
from sqlalchemy import select
from app.core.services.s3 import generate_cloudfront_presigned_url, get_image_cloudfront_signed_url
from app.core.models.additional_services_transactions import AdditionalServiceTransaction
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models.property_details import PropertyDetails

from sqlalchemy import exists, select,func,desc
async def is_additional_services_available(
    service_id: str,
    category: str,
    db: AsyncSession
):
    result = await db.execute(
        select(AdditionalServices).where(
            AdditionalServices.service_id == service_id
        )
    )

    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if not service.is_active:
        raise HTTPException(status_code=400, detail="Service not available")

    if category not in service.applicable_to:
        raise HTTPException(
            status_code=400,
            detail="Service not allowed for this property type"
        )

    return service


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
async def has_existing_service(
    service_id: str,
    property_id: str,
    db: AsyncSession
) -> bool:
    stmt = select(
        exists().where(
            AdditionalServiceTransaction.service_id == service_id,
            AdditionalServiceTransaction.property_id == property_id,
            AdditionalServiceTransaction.service_status.in_(
                ["REQUESTED", "ASSIGNED"]
            )
        )
    )
    result = await db.execute(stmt)
    return result.scalar()


async def get_last_transaction_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(AdditionalServiceTransaction)
    )
    return result.scalar() or 0
async def get_property_by_id(
    property_id: str,
    user_id: str,
    db: AsyncSession
):
    result = await db.execute(
        select(PropertyDetails).where(
            PropertyDetails.property_id == property_id
        )
    )

    property = result.scalar_one_or_none()

    if not property:
        raise HTTPException(status_code=404, detail="Property Not Found")

    if property.user_id != user_id:
        raise HTTPException(status_code=403, detail="User Not Authorized")

    return property

    

import asyncio
from sqlalchemy import select

async def list_property_by_category(
    user_id: str,
    category: str,
    db: AsyncSession
):
    result = await db.execute(
        select(PropertyDetails).where(
            PropertyDetails.user_id == user_id,
            PropertyDetails.type == category
        )
    )

    records = result.scalars().all()

    image_tasks = [
         get_image_cloudfront_signed_url(
            f"property/{record.property_id}/legal_documents/property_photo.png"
        )
        for record in records
    ]

    image_urls = await asyncio.gather(*image_tasks)

    data = [
        {
            "property_id": record.property_id,
            "property_name": record.property_name,
            "property_category": record.type,
            "property_location": record.city,
            "property_img": image_urls[i]
        }
        for i, record in enumerate(records)
    ]

    return data





from sqlalchemy import func

async def list_all_bookings(
    user_id: str,
    db: AsyncSession ,
    start: int = 1,
    limit: int = 10,
):
    offset = (start - 1) * limit

    total_result = await db.execute(
        select(func.count())
        .where(AdditionalServiceTransaction.user_id == user_id)
    )
    total = total_result.scalar()

    data_result = await db.execute(
        select(AdditionalServiceTransaction)
        .where(AdditionalServiceTransaction.user_id == user_id)
        .order_by(desc(AdditionalServiceTransaction.created_at))
        .offset(offset)
        .limit(limit)
    )

    data = data_result.scalars().all()

    return {
        "page": start,
        "limit": limit,
        "total": total,
        "data": data
    }

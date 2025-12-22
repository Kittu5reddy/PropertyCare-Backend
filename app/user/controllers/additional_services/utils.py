from app.core.models.additional_services import AdditionalServices
from app.core.services.db import AsyncSession,get_db
from fastapi import Depends
from sqlalchemy import select

from app.core.models.additional_services_transactions import AdditionalServiceTransaction
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models.property_details import PropertyDetails
from sqlalchemy import select
from sqlalchemy import exists, select,func

async def is_additional_services_available(
    service_id: str,
    category: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(AdditionalServices).where(
                AdditionalServices.service_id == service_id
            )
        )

        service = result.scalar_one_or_none()

        #  Service not found
        if not service:
            raise HTTPException(
                status_code=404,
                detail="Service not found"
            )

        #  Service inactive
        if not service.is_active:
            raise HTTPException(
                status_code=400,
                detail="Service not available"
            )

        #  Category mismatch
        if service.category != category:
            raise HTTPException(
                status_code=400,
                detail="Service not allowed for this property type"
            )

        # ✅ Service is valid
        return service

    except HTTPException:
        raise  # IMPORTANT: re-raise HTTP exceptions

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while checking service availability"
        )


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


async def get_last_transaction_count(
    db: AsyncSession
) -> int:
    result = await db.execute(
        select(func.count()).select_from(AdditionalServiceTransaction)
    )
    return result.scalar()

async def get_property_by_id(property_id:str,
                             user_id:str,
                         db: AsyncSession = Depends(get_db)):
    try:
        smt=await db.execute(select(PropertyDetails).where(PropertyDetails.property_id==property_id))
        property=smt.scalar_one_or_none()
        if not property:
            raise HTTPException(status_code=404,detail="Property Not Found")
        if property.user_id!=user_id:
            raise HTTPException(status_code=403,detail="User Not Authorized")
        return property
    except HTTPException:
        raise  # IMPORTANT: re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking service availability: {str(e)}"
        )
    

async def list_property_by_category(
    user_id: str,
    category: str,
    db: AsyncSession
):
    result = await db.execute(
        select(PropertyDetails.property_name,PropertyDetails.type,
               ).where(
            PropertyDetails.user_id == user_id,
            PropertyDetails.type == category
        )
    )

    return result.scalars().all()


async def list_all_bookings(
    user_id: str,
    db: AsyncSession
):
    result = await db.execute(
        select(AdditionalServiceTransaction
               ).where(
            AdditionalServiceTransaction.user_id == user_id,
        )
    )

    return result.scalars().all()




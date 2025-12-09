

from datetime import datetime
from app.core.services.db import AsyncSession
from app.core.models.property_details import PropertyDetails
from app.core.models.property_documents import PropertyDocuments
from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


def check_property_access(property_obj, user_id: str):
    """
    Raise 403 HTTPException if the property does not belong to the user.
    """
    if property_obj.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this property")
    
async def get_user_documents(user_id:str,property_id:str,db:AsyncSession):
    smt=await db.execute(select(PropertyDocuments).where(PropertyDocuments.property_id==property_id,PropertyDocuments.user_id==user_id))
    documents=smt.scalar_one_or_none()
    return documents


async def is_user_authenticated_for_property(property_id: str, user_id: str, db: AsyncSession):
    try:
        # Fetch property
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()

        # Property does not exist
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # Property exists, but belongs to another user
        if property_obj.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this property")

        return property_obj

    except HTTPException:
        raise  # Let FastAPI handle HTTP errors

    except SQLAlchemyError as e:
        print("Database error:", e)
        raise HTTPException(status_code=500, detail="Database error while checking property authentication")

    except Exception as e:
        print("Unexpected error:", e)
        raise HTTPException(status_code=500, detail="Failed to authenticate property access")



async def is_property_details_changable(property_id: str, user_id: str, db: AsyncSession) -> bool:
    """
    Checks whether the given property details can be changed.
    A property can be changed only if it's not verified.
    """
    try:
        result = await db.execute(
            select(PropertyDetails)
            .where(
                PropertyDetails.property_id == property_id,
                PropertyDetails.user_id == user_id,
                PropertyDetails.is_verified == False
            )
            .limit(1)
        )
        property_obj = result.scalar_one_or_none()
        return bool(property_obj)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[is_property_details_changable] Error: {str(e)}")
        # Option 1: Raise an HTTP exception so FastAPI can handle it
        raise HTTPException(status_code=500, detail="Failed to check property status")
        # Option 2: (alternative) return False if you don’t want to break the flow
        # return False

def generate_document_id(id:int):
    return f'PC{datetime.utcnow().year}D{str(id).zfill(3)}'



async def get_current_property(property_id: str, user_id: str, db: AsyncSession):
    try:
        result = await db.execute(
            select(PropertyDetails).where(
                PropertyDetails.property_id == property_id,
                PropertyDetails.user_id == user_id
            )
        )

        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(
                status_code=404,
                detail="Property not found for this user"
            )

        return property_obj

    except Exception as e:
        print("Database Error:", e)
        raise HTTPException(
            status_code=500,
            detail="Internal database error while fetching property"
        )
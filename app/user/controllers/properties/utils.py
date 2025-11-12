from datetime import datetime
from app.core.models import get_db,AsyncSession
from app.core.models.property_details import PropertyDetails
from sqlalchemy import select
from fastapi import HTTPException


def check_property_access(property_obj, user_id: str):
    """
    Raise 403 HTTPException if the property does not belong to the user.
    """
    if property_obj.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this property")


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


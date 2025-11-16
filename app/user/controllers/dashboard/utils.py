from sqlalchemy import select
from app.core.models.property_details import PropertyDetails
from app.core.models import get_db,AsyncSession
from fastapi import Depends,HTTPException
from app.user.controllers.forms.utils import generate_cloudfront_presigned_url,check_object_exists
from datetime import date
from config import settings
from jose import JWTError
async def get_property_details(
    user_id: str,
    db: AsyncSession,
    limit: int = 3
) -> list[dict]:

    try:
        query = (
            select(
                PropertyDetails.property_id,
                PropertyDetails.property_name,
                PropertyDetails.size,
                PropertyDetails.type,
                PropertyDetails.city,
                PropertyDetails.scale,
                PropertyDetails.active_sub
            )
            .where(PropertyDetails.user_id == user_id)
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        data = []

        for row in rows:
            # Check if property image exists
            key = f"property/{row.property_id}/legal_documents/property_photo.png"
            exists = await check_object_exists(key)

            if exists:
                # IMPORTANT: must await signed URL
                signed_url = await generate_cloudfront_presigned_url(key)
            else:
                signed_url = settings.DEFAULT_IMG_URL

            data.append({
                "property_id": row.property_id,
                "location": row.city,
                "name": row.property_name,
                "size": f"{int(row.size)} {row.scale}",
                "type": row.type,
                "subscription": row.active_sub,
                "image_url": signed_url
            })

        return data

    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))



from datetime import date
from typing import Dict, Any, Optional



def create_subscription_action_data(
    property_id: str,
    sub_type: str,
    document_name: str,
    property_name: str,
    location:str,
    end_date: date
) -> Dict[str, Any]:
    """
    Create JSON structure for subscription-related required actions.
    Example: Subscription renewals or expiry reminders.
    """
    return {
        "property_id":property_id,
        "property_name":property_name,
        "location":location,
        "document_name": document_name,
        "subscription_type": sub_type,
        "end_date": end_date.isoformat()  # store date as string for JSON
    }


def create_property_document_action_data(
    document_name: str,
    property_name: str,
    property_id:str,
    location:str,
) -> Dict[str, Any]:
    """
    Create JSON structure for document-related required actions.
    Example: Verification or expiry tracking.
    """
    data = {
        "property_id":property_id,
        "property_name":property_name,
        "location":location,
        "document_name": document_name
    }
    return data

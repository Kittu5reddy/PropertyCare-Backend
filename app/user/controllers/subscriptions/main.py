from .utils import PropertyDetails
from fastapi import APIRouter,Depends,HTTPException
from app.core.models import AsyncSession,get_db
from app.core.controllers.auth.main import oauth2_scheme
from app.core.controllers.auth.utils import get_current_user
from sqlalchemy import select
from app.user.controllers.forms.utils import get_image
subscriptions=APIRouter(prefix='/subscriptions',tags=['subscriptions'])


@subscriptions.get("/get-properties")
async def get_properties(
    category: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Fetch properties of a specific category for the logged-in user."""

    try:
        user = await get_current_user(token, db)
        # Query all matching properties
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.type == category.lower())
        )
        properties = result.scalars().all()

        if not properties:
            raise HTTPException(
                status_code=404,
                detail=f"No properties found for category '{category}'."
            )

        return {
            "user_id": user.user_id,
            "count": len(properties),
            "properties": [
                {
                    "property_id": p.property_id,
                    "property_name": p.property_name,
                    "type": p.type,
                    "city": p.city,
                    "state": p.state,
                    "property_image_url":get_image(f'/property/{ p.property_id}/legal_documents/property_photo.png')
                }
                for p in properties
            ],
        }

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=401,
            detail=f"Failed to fetch properties: {str(e)}"
        )
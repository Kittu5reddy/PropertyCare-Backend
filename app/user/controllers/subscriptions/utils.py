from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.core.models.subscriptions_plans import SubscriptionPlans
from app.core.models.property_details import PropertyDetails

from config import settings
import httpx
from app.user.controllers.forms.utils import get_image
async def get_image_or_default(image_path: str) -> str:
    """Check if CloudFront image exists, else return fallback."""
    url = f"{settings.CLOUDFRONT_URL}{image_path}"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.head(url)  # HEAD request is lightweight
            if response.status_code == 200:
                return url
            else:
                print(f"⚠️ CloudFront returned {response.status_code} for {url}")
                return settings.DEFAULT_IMG_URL
    except Exception as e:
        print(f"❌ CloudFront check failed: {e}")
        return settings.DEFAULT_IMG_URL
    


async def get_current_sub(sub_id: str, db: AsyncSession):
    result = await db.execute(
        select(SubscriptionPlans).where(SubscriptionPlans.sub_id == sub_id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription



async def get_property_user(property_id: str, user_id: str, db: AsyncSession):
    """
    Fetch a property by its ID and user ID.
    Returns:
        PropertyDetails object or None.
    """
    try:
        query = (
            select(PropertyDetails)
            .where(
                PropertyDetails.property_id == property_id,
                PropertyDetails.user_id == user_id
            )
        )

        result = await db.execute(query)
        property_obj = result.scalar_one_or_none()

        return property_obj

    except Exception as e:
        print(f"❌ Error in get_property_user: {e}")
        return None
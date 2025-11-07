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
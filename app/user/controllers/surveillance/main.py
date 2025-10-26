from fastapi import APIRouter, Depends, HTTPException
from app.core.controllers.auth.main import oauth2_scheme, get_db, AsyncSession, JWTError
from app.core.controllers.auth.utils import get_current_user
from app.user.controllers.forms.utils import list_s3_objects, get_image
from datetime import date
import botocore.exceptions
from sqlalchemy.exc import SQLAlchemyError
from app.core.models import redis, get_redis, redis_set_data, redis_get_data, redis_delete_data

surveillance = APIRouter(prefix='/surveillance', tags=['surveillance'])

@surveillance.get('/get-month-details/{property_id}/{year}/{month}')
async def get_monthly_details(
    property_id: str,
    year: str,
    month: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    try:
        # Get current user
        user = await get_current_user(token, db)

        cache_key = f"property:{property_id}:monthly-photos:{year}:{month}"
        cache_data = await redis_get_data(cache_key)
        if cache_data:
            # Inline 403 check: only allow user to access own property
            if cache_data.get("user_id") != user.user_id:
                raise HTTPException(status_code=403, detail="You do not have access to this property")
            return cache_data

        # Construct S3 prefix
        object_key = f"property/{property_id}/monthly-photos/{year}/{month}/"

        # Get list of objects from S3
        objects = await list_s3_objects(prefix=object_key)
        objects = [get_image("/" + obj) for obj in objects]

        # Dummy structured data (replace with real logic if needed)
        data = {
            "user_id": user.user_id,  # store user_id for authorization checks
            "inspection_date": "2024-06-15",
            "inspector_id": "INS12345",
            "summary": "Property is well maintained. Minor repairs suggested.",
            "subscription_ends": "2024-12-31",
            "subscription_status": True,
            "physical_verification": True,
            "phases": [
                {
                    "phase": 1,
                    "total_photos": 3,
                    "total_videos": 1,
                    "photos": objects[:3],
                    "videos": ["https://www.w3schools.com/html/mov_bbb.mp4"],
                },
            ],
        }

        await redis_set_data(cache_key, data)
        return data

    except HTTPException:
        raise
    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=502, detail=f"S3 error: {str(e)}")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@surveillance.get('/get-current-month-photos/{property_id}')
async def get_current_month_photos(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        today = date.today()
        month_name = today.strftime("%B")
        object_key = f"property/{property_id}/monthly-photos/{today.year}/{month_name}/"
        cache_key = f"property:{property_id}:monthly-photos:{today.year}:{month_name}"

        cache_data = await redis_get_data(cache_key)
        if cache_data:
            return cache_data

        user = await get_current_user(token, db)
        # Get list of objects from S3
        objects = await list_s3_objects(prefix=object_key)
        objects = [get_image("/" + obj) for obj in objects]

        data = {"user_id": user.user_id, "photos": objects}
        await redis_set_data(cache_key, data)
        return data

    except HTTPException:
        raise
    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=502, detail=f"S3 error: {str(e)}")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@surveillance.get('/get-property-surveillance-data/{property_id}')
async def property_surveillance_data(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    try:
        user = await get_current_user(token, db)
        today = date.today()
        month_name = today.strftime("%B")
        object_key = f"property/{property_id}/monthly-photos/{today.year}/{month_name}/"

        # Get list of objects from S3
        objects = await list_s3_objects(prefix=object_key)
        objects = [get_image("/" + obj) for obj in objects]

        # Include user_id for authorization
        data = {"user_id": user.user_id, "photos": objects}

        # Inline 403 check
        if data.get("user_id") != user.user_id:
            raise HTTPException(status_code=403, detail="You do not have access to this property")

        return data

    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=502, detail=f"S3 error: {str(e)}")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

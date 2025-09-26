from fastapi import APIRouter,Depends,HTTPException
from app.user.controllers.auth.main import oauth2_scheme,get_db,AsyncSession,JWTError
from app.user.controllers.auth.utils import get_current_user
from app.user.controllers.forms.utils import list_s3_objects
from datetime import date
import botocore.exceptions
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
from app.user.models import redis,get_redis,redis_set_data,redis_get_data,redis_delete_data
from app.user.controllers.forms.utils import get_image 

surveillance=APIRouter(prefix='/surveillance',tags=['surveillance'])



@surveillance.get('/get-month-photos/{property_id}/{year}/{month}')
async def get_monthly_photos(
    property_id: str,
    year: str,
    month: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client:redis.Redis=Depends(get_redis)
):
    try:
        user = await get_current_user(token, db)
        cache_key=f"property:{property_id}:monthly-photos:{year}:{month}"
        # await redis_delete_data(cache_data)
        cache_data=await redis_get_data(cache_key)
        if cache_data:
            return cache_data
        # Construct S3 prefix
        object_key = f"property/{property_id}/monthly-photos/{year}/{month}/"

        # Get list of objects
        data = await list_s3_objects(prefix=object_key)
        data=list(map(get_image,map(lambda x:"/"+x,data)))
        # print(data)
        await redis_set_data(cache_key,data)
        return {"photos": data}

    except botocore.exceptions.ClientError as e:
        # AWS S3 error
        raise HTTPException(status_code=502, detail=f"S3 error: {str(e)}")

    except SQLAlchemyError as e:
        # Database-related error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except HTTPException:
        # Re-raise FastAPI HTTPExceptions (e.g., from get_current_user)
        raise

    except Exception as e:
        # Fallback for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    


@surveillance.get('/get-current-month-photos/{property_id}')
async def get_current_month_photos(
    property_id:str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client:redis.Redis=Depends(get_redis)
):
    try:
        today = date.today()
        month_name = today.strftime("%B") 
        object_key = f"property/{property_id}/monthly-photos/{today.year}/{month_name}/"
        cache_key=f"property:{property_id}:monthly-photos:{today.year}:{month_name}"
        cache_data=await redis_get_data(cache_key)
        if cache_data:
            return cache_data
        user = await get_current_user(token, db)
        # Construct S3 prefix
        # object_key = f"property/{property_id}/monthly-photos/{year}/{month}/"

        # Get list of objects
        data = await list_s3_objects(prefix=object_key)
        await redis_set_data(cache_key,data)
        return {"photos": data}

    except botocore.exceptions.ClientError as e:
        # AWS S3 error
        raise HTTPException(status_code=502, detail=f"S3 error: {str(e)}")

    except SQLAlchemyError as e:
        # Database-related error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except HTTPException:
        # Re-raise FastAPI HTTPExceptions (e.g., from get_current_user)
        raise

    except Exception as e:
        # Fallback for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")



@surveillance.get('/get-property-surveillance-data/{property_id}')
async def property_surveillance_data(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client:redis.Redis=Depends(get_redis)
):
    try:
        user = await get_current_user(token, db)

        today = date.today()
        month_name = today.strftime("%B") 
        object_key = f"property/{property_id}/monthly-photos/{today.year}/{month_name}/"
        print(object_key)
        # Get list of objects
        data = await list_s3_objects(prefix=object_key)

        return {"photos": data}

    except JWTError as e:
        raise HTTPException(status_code=401 ,details="Unauthorized")
    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=502, detail=f"S3 error: {str(e)}")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

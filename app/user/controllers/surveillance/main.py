from fastapi import APIRouter,Depends,HTTPException
from app.core.controllers.auth.main import oauth2_scheme,get_db,AsyncSession,JWTError
from app.core.controllers.auth.utils import get_current_user
from app.user.controllers.forms.utils import list_s3_objects
from datetime import date
import botocore.exceptions
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
from app.core.models import redis,get_redis,redis_set_data,redis_get_data,redis_delete_data
from app.user.controllers.forms.utils import get_image 

surveillance=APIRouter(prefix='/surveillance',tags=['surveillance'])



@surveillance.get('/get-month-details/{property_id}/{year}/{month}')
async def get_monthly_details(
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
        object_key = f"property/{property_id}/monthly-photos/{year}/{month}/"

        # Get list of objects
        data = await list_s3_objects(prefix=object_key)
        data=list(map(get_image,map(lambda x:"/"+x,data)))
        # print(data)
        data= {
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
              "photos": [
                "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=400&q=80%22",
                "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=400&q=80%22",
                "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80%22",
                "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80%22",
                "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80%22",
                "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80%22",
              ],
              "videos": ["https://www.w3schools.com/html/mov_bbb.mp4"],
            },
            {
              "phase": 2,
              "total_photos": 2,
              "total_videos": 2,
              "photos": [
                "https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80%22",
                "https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0?auto=format&fit=crop&w=400&q=80%22",
              ],
              "videos": [
                "https://www.w3schools.com/html/movie.mp4",
                "https://www.w3schools.com/html/mov_bbb.mp4",
              ],
            },
          ],
        };
 
        await redis_set_data(cache_key,data)
        return data

    except HTTPException:
        # Re-raise FastAPI HTTPExceptions (e.g., from get_current_user)
        raise
    except botocore.exceptions.ClientError as e:
        # AWS S3 error
        raise HTTPException(status_code=502, detail=f"S3 error: {str(e)}")

    except SQLAlchemyError as e:
        # Database-related error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


    except Exception as e:
        # Fallback for unexpected errors
        print(str(e))
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
        data=list(map(get_image,map(lambda x:"/"+x,data)))
        data = await list_s3_objects(prefix=object_key)
        data={"photos": data}
        await redis_set_data(cache_key, data)
        return data

    except HTTPException:
        # Re-raise FastAPI HTTPExceptions (e.g., from get_current_user)
        raise
    except botocore.exceptions.ClientError as e:
        # AWS S3 error
        raise HTTPException(status_code=502, detail=f"S3 error: {str(e)}")

    except SQLAlchemyError as e:
        # Database-related error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


    except Exception as e:
        # Fallback for unexpected errors
        print(str(e))
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

    except HTTPException:
        raise
    except JWTError as e:
        raise HTTPException(status_code=401 ,details="Unauthorized")
    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=502, detail=f"S3 error: {str(e)}")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

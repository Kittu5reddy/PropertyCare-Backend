from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,Form
from jose import JWTError
from app.core.controllers.auth.main import oauth2_scheme
from app.user.controllers.forms.utils import get_image
from app.core.controllers.auth.main import get_current_user
from app.core.models.property_details import PropertyDetails
from .utils import get_property_details
from app.core.models import AsyncSession,get_db,redis_get_data,redis_set_data
from sqlalchemy import select
from app.user.controllers.forms.utils import list_s3_objects
from app.user.models.required_actions import RequiredAction
from app.user.validators.required_actions import RequiredActions as RequiredActionSchema
dash=APIRouter(prefix='/dash',tags=['/dash'])


from app.user.controllers.forms.utils import property_upload_documents,upload_documents
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError
from app.core.controllers.auth.main import get_current_user, oauth2_scheme
from app.user.models.required_actions import RequiredAction


@dash.get("/get-required-actions")
async def get_required_actions(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        result = await db.execute(
            select(RequiredAction)
            .where(
                RequiredAction.user_id == user.user_id,
                RequiredAction.status.ilike("pending")  
            )
        )

        required_actions = result.scalars().all()

        return {"required_actions": required_actions}

    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    except Exception as e:
        print(f"Error fetching required actions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@dash.post("/upload-required-documents")
async def upload_required_documents(
    category: str = Form(...),
    file_name: str = Form(...),
    property_id: str | None = Form(None),
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user(token, db)

        if category.lower() == "user":
            contents = await file.read()
            file_data = {
                         "filename": file.filename,
                         "bytes": contents,
                         "content_type": file.content_type,
                     }
            await upload_documents(file=file_data, category=file_name, user_id=user.user_id)
            return {"users documents uploaded:":True}
        elif category.lower() == "property":   
            is_auth = await db.execute(
                select(PropertyDetails)
                .where(
                    PropertyDetails.user_id == user.user_id,
                    PropertyDetails.property_id == property_id
                )
            )
            is_auth = is_auth.scalar_one_or_none()

            if is_auth:
                contents = await file.read()
                file_data = {
                             "filename": file.filename,
                             "bytes": contents,
                             "content_type": file.content_type,
                         }
                await property_upload_documents(
                    file=file_data, category=file_name, property_id=property_id
                )
                return {"property documents uploaded:":True}
            else:
                raise HTTPException(status_code=403, detail="UnAuthorized")
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))
    



@dash.get("/property-details")
async def get_property_data(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)
        cache_key=f"user:{user.user_id}:property-details"
        cache_data=await redis_get_data(cache_key)
        if cache_data:
            print('hit')
            return cache_data
        data = await get_property_details(user.user_id, db,5)
        # print(data)
        data={"data":data}
        await redis_set_data(cache_key,data)
        print('miss')
        return data
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))
@dash.get("/monthly-photos")
async def get_property_data(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)
        cache_key=f"user:{user.user_id}:property-details"
        cache_data=await redis_get_data(cache_key)
        if cache_data:
            print('hit')
            return cache_data
        data = await get_property_details(user.user_id, db,5)
        # print(data)
        data={"data":data}
        await redis_set_data(cache_key,data)
        print('miss')
        return data
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))





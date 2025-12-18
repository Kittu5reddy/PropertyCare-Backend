from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.models.property_details import PropertyDetails
from app.core.services.s3 import property_upload_documents, upload_documents
from app.core.services.redis import redis_get_data, redis_set_data
from app.core.services.db import get_db
from app.user.controllers.auth.utils import get_current_user
from app.user.models.required_actions import RequiredAction
from .utils import get_property_details

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
dash=APIRouter(prefix='/dash',tags=['/dash'])
@dash.get("/get-required-actions")
async def get_required_actions(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)
        from sqlalchemy import case

        priority_order = case(
            (RequiredAction.priority.ilike("high"), 1),
            (RequiredAction.priority.ilike("medium"), 2),
            (RequiredAction.priority.ilike("low"), 3),
            else_=4
        )

        result = await db.execute(
            select(RequiredAction)
            .where(
                RequiredAction.user_id == user.user_id,
                RequiredAction.status.ilike("pending")
            )
            .order_by(priority_order)
        )


        required_actions = result.scalars().all()
        print(required_actions[0])

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

        # --- For user documents ---
        if category.lower() == "user":
            contents = await file.read()
            file_data = {
                "filename": file.filename,
                "bytes": contents,
                "content_type": file.content_type,
            }

            await upload_documents(
                file=file_data,
                category=file_name,
                user_id=user.user_id
            )

            # ✅ Fetch and update RequiredAction
            record = await db.execute(
                select(RequiredAction)
                .where(
                    RequiredAction.category == category,
                    RequiredAction.user_id == user.user_id
                )
                .limit(1)
            )
            record = record.scalar_one_or_none()

            if record:
                record.status = "completed"
                await db.commit()
                await db.refresh(record)
            else:
                raise HTTPException(status_code=404, detail="Required action not found")

            return {"user_documents_uploaded": True}

        # --- For property documents ---
        elif category.lower() == "property":
            is_auth = await db.execute(
                select(PropertyDetails)
                .where(
                    PropertyDetails.user_id == user.user_id,
                    PropertyDetails.property_id == property_id
                )
            )
            is_auth = is_auth.scalar_one_or_none()

            if not is_auth:
                raise HTTPException(status_code=403, detail="UnAuthorized")

            contents = await file.read()
            file_data = {
                "filename": file.filename,
                "bytes": contents,
                "content_type": file.content_type,
            }

            await property_upload_documents(
                file=file_data,
                category=file_name,
                property_id=property_id
            )

            # ✅ Update property RequiredAction
            record = await db.execute(
                select(RequiredAction)
                .where(
                    RequiredAction.information["property_id"].astext == property_id,
                    RequiredAction.category == category,
                    RequiredAction.user_id == user.user_id
                )
                .limit(1)
            )
            record = record.scalar_one_or_none()

            if record:
                record.status = "completed"
                await db.commit()
                await db.refresh(record)
            else:
                raise HTTPException(status_code=404, detail="Required action not found")

            return {"property_documents_uploaded": True}

        else:
            raise HTTPException(status_code=400, detail="Invalid category")

    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))



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
        data = await get_property_details(user.user_id, db,3)
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
        data = await get_property_details(user.user_id, db,3)
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





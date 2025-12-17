from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from jose import JWTError
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json
from app.core.services.s3 import  get_image_cloudfront_signed_url
# Import utils & models
from app.user.controllers.auth.utils import get_current_user
from app.core.services.db import get_db
from app.user.validators.propertydetails import PropertyDetailForm, UpdatePropertyNameRequest
from app.user.validators.changeproperty import PropertyDetailsUpdate as ChangePropertySchema
from app.user.models.users import User

from app.core.models.property_details import PropertyDetails
from app.core.models.property_documents import PropertyDocuments
from app.core.services.s3 import (
    property_upload_image_as_png,
    property_upload_documents,
    property_delete_document,
    property_delete_single_document,
    invalidate_files,
    list_s3_objects,
    generate_cloudfront_presigned_url,
    check_object_exists
)
from app.core.services.redis import (
    get_redis,
    redis_get_data,
    redis_set_data,
    redis_delete_data,
    redis_delete_pattern
)

from config import settings

from app.core.business_logic.ids import generate_property_id

prop = APIRouter(prefix="/property", tags=["property"])
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
# ======================================================
#                     P O S T
# ======================================================

@prop.post("/is-property-exists")
async def is_property_exist(
    form: PropertyDetailForm,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user(token, db)

        result = await db.execute(
            select(PropertyDetails).where(
                and_(
                    PropertyDetails.survey_number == form.survey_number,
                    PropertyDetails.plot_number == form.plot_number,
                    PropertyDetails.user_id == user.user_id,
                    PropertyDetails.house_number == form.house_number
                )
            )
        )
        return {"is_property_exist": result.first() is not None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

from .utils import get_user_documents
@prop.post("/upload-document/{property_id}")
async def upload_property_documents(
    property_id: str,
    category: str = Form(...),
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1. Validate user
        user = await get_current_user(token, db)

        # 2. Check whether user can still update documents
        user_docs = await get_user_documents( property_id,db)

        if not user_docs:
            raise HTTPException(status_code=404, detail="Property documents not found")

        # 3. Ensure the category exists in the model
        if not hasattr(user_docs, category):
            raise HTTPException(status_code=400, detail=f"Invalid document category: {category}")

        # 4. Block upload if already verified
        if getattr(user_docs, category):
            raise HTTPException(
                status_code=400,
                detail="Document already uploaded or property verified — contact admin team"
            )

        # 5. Read file contents
        contents = await file.read()
        file_data = {
            "filename": file.filename,
            "bytes": contents,
            "content_type": file.content_type,
        }

        # 6. Upload to storage (S3 / Cloud / local)
        result = await property_upload_documents(file_data, category, property_id)

        # 7. Cache invalidation
        await redis_delete_data(f"property:{property_id}:documents")

        # 8. Handle upload errors
        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "status": "success",
            "message": f"{category} uploaded successfully",
            "data": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")



@prop.post("/add-reference-image/{property_id}")
async def add_reference_photo(
    property_id: str,
    category: str = Form(...),
    files: list[UploadFile] = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1. Validate user
        user = await get_current_user(token, db)
        # 2. Validate document status for property
        user_docs = await get_user_documents( property_id,db)

        if not user_docs:
            raise HTTPException(status_code=404, detail="Property documents not found")

        # 3. Validate category exists on model
        if not hasattr(user_docs, category):
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        # 4. Block edits if this category is already verified or filled
        if getattr(user_docs, category):
            raise HTTPException(
                status_code=400,
                detail="This category is already uploaded or property is verified. Contact admin."
            )

        # 5. Validate at least 1 file
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")

        results = []

        # 6. Process each file
        for file in files:
            contents = await file.read()

            if not contents:
                raise HTTPException(status_code=400, detail=f"Empty file: {file.filename}")

            file_data = {
                "filename": file.filename,
                "bytes": contents,
                "content_type": file.content_type,
            }

            upload_res = await property_upload_image_as_png(
                file_data, category, property_id
            )

            if isinstance(upload_res, dict) and upload_res.get("error"):
                raise HTTPException(status_code=400, detail=upload_res["error"])

            results.append(upload_res)

        # 7. Invalidate property cache
        await redis_delete_pattern(f"property:{property_id}:*")

        return {
            "status": "success",
            "message": f"{len(results)} image(s) uploaded successfully",
            "files": results,
        }

    except HTTPException:
        raise  # Preserve correct HTTP codes
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")



from sqlalchemy.exc import IntegrityError

@prop.post("/add-property")
async def user_add_property(
    form: PropertyDetailForm,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user(token, db)

        # Generate next property ID
        result = await db.execute(select(func.max(PropertyDetails.id)))
        next_id = (result.scalar_one_or_none() or 0) + 1 + int(settings.PROPERTY_STARTING_NUMBER)
        property_id = generate_property_id(next_id)

        property_obj = PropertyDetails(
            property_id=property_id,
            user_id=user.user_id,
            **form.dict()
        )

        documents = PropertyDocuments(property_id=property_id)

        db.add(property_obj)
        db.add(documents)

        # Commit inside try–except for integrity errors
        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()

            # Detect duplicate user/property-specific errors
            if "unique constraint" in str(e).lower():
                raise HTTPException(
                    status_code=400,
                    detail="Property already exists or user has already added a property."
                )

            # Other DB errors
            raise HTTPException(status_code=400, detail="Database error: " + str(e))

        await redis_delete_pattern(f"user:{user.user_id}:*")

        return {
            "property_id": property_id,
            "message": "Property added successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ======================================================
#                     P U T
# ======================================================
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

@prop.put("/update-property-name/{property_id}")
async def update_property_name(
    property_id: str,
    payload: UpdatePropertyNameRequest,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Authenticate user
        user = await get_current_user(token, db)

        # Validate input BEFORE using len()
        if not payload.property_name:
            raise HTTPException(status_code=400, detail="Property name is required")

        property_name = payload.property_name.strip()

        if len(property_name) > 20:
            raise HTTPException(status_code=400, detail="Name must be <= 20 characters")

        # Strip extra spaces
        property_name = payload.property_name.strip()

        if property_name == "":
            raise HTTPException(
                status_code=400,
                detail="Property name cannot be empty"
            )

        # Validate length
        if len(property_name) > 20:
            raise HTTPException(
                status_code=400,
                detail="Name should be less than or equal to 20 characters"
            )

        # Fetch property
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # Update name
        property_obj.property_name = property_name

        # Commit transaction
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Duplicate property name is not allowed"
            )

        await db.refresh(property_obj)

        # Clear Redis cache safely
        try:
            await redis_delete_data(f"property:{property_id}:info")
        except Exception as e:
            print("Redis delete error:", e)

        return {"message": "Property name updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating property: {str(e)}"
        )

@prop.put("/change-property-photo/{property_id}")
async def change_property_photo(
    property_id: str,
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_current_user(token, db)

        content = await file.read()
        result = await property_upload_image_as_png({"bytes": content}, "property_photo", property_id)

        await invalidate_files([f"/property/{property_id}/legal_documents/property_photo.png"])
        await redis_delete_data(f"property:{property_id}:info")
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@prop.put("/update-property-details/{property_id}")
async def update_property_details(
    property_id: str,
    payload: ChangePropertySchema,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1️⃣ Authenticate user
        user = await get_current_user(token, db)

        # 2️⃣ Fetch property
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # 3️⃣ Authorization check (VERY IMPORTANT)
        if property_obj.user_id != user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this property")

        # 4️⃣ Extract only allowed fields
        update_data = payload.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        allowed_fields = set(PropertyDetails.__table__.columns.keys())

        for key, value in update_data.items():
            if key in allowed_fields:
                setattr(property_obj, key, value)

        # 5️⃣ Commit changes
        await db.commit()
        await db.refresh(property_obj)

        # 6️⃣ Clear Redis cache
        # cache_key = f"property:{property_id}:info"
        # await redis_delete_data(cache_key)

        return {
            "message": "Property details updated successfully",
            "property_id": property_id
        }

    except HTTPException:
        # 👈 Let FastAPI handle it properly
        raise

    except Exception as e:
        print(str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating property"
        )

# ======================================================
#                     D E L E T E
# ======================================================

@prop.delete("/delete-document/{property_id}")
async def delete_document(
    property_id: str,
    category: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user(token, db)

        # 2. Validate document status for property
        user_docs = await get_user_documents(property_id,db)
        if not user_docs:
            raise HTTPException(status_code=404, detail="Property documents not found")

        # 3. Validate category exists on model
        if not hasattr(user_docs, category):
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        # 4. Block edits if this category is already verified or filled
        if getattr(user_docs, category):
            raise HTTPException(
                status_code=400,
                detail="This category is already uploaded or property is verified. Contact admin."
            )    
        result = await property_delete_document(category, property_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        await redis_delete_data(f"property:{property_id}:documents")
        return {"message": "Document deleted"}
    except HTTPException:
        # 👈 Let FastAPI handle it properly
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting: {str(e)}")


@prop.delete("/delete-reference-image/{property_id}")
async def delete_reference_photo(
    property_id: str,
    payload: dict = Body(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        category="property_photos"
        user = await get_current_user(token, db)

        # 2. Validate document status for property
        user_docs = await get_user_documents(property_id,db)
        if not user_docs:
            raise HTTPException(status_code=404, detail="Property documents not found")

        # 3. Validate category exists on model
        if not hasattr(user_docs, category):
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        # 4. Block edits if this category is already verified or filled
        if getattr(user_docs, category):
            raise HTTPException(
                status_code=400,
                detail="This category is already uploaded or property is verified. Contact admin."
            )
        file_url = payload["property_photos"]
        filename = file_url.split("/")[-1].split("?")[0]

        result = await property_delete_single_document("property_photos", property_id, filename)

        await redis_delete_data(f"property:{property_id}:reference-images")
        return {"message": "Reference image deleted", "deleted": filename}
    except HTTPException:
        # 👈 Let FastAPI handle it properly
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    














# ======================================================
#                     G E T
# ======================================================

@prop.get("/properties-list/{user_id}")
async def get_property_list(
    user_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    user = await get_current_user(token, db)
    cache_key = f"user:{user_id}:property-list"

    cached = await redis_get_data(cache_key)
    if cached:
        return cached


    result = await db.execute(
        select(
            PropertyDetails.property_id,
            PropertyDetails.property_name,
            PropertyDetails.city,
            PropertyDetails.type,
            PropertyDetails.size,
            PropertyDetails.scale,
            PropertyDetails.active_sub
        ).where(PropertyDetails.user_id == user.user_id)
    )

    rows = result.all()
    properties = []

    for row in rows:
        image_exists = await check_object_exists(f"property/{row[0]}/legal_documents/property_photo.png")

        properties.append({
            "property_id": row[0],
            "name": row[1],
            "location": row[2],
            "type": row[3],
            "size": f"{int(row[4])} {str(row[5])}",
            "image_url": await get_image_cloudfront_signed_url(f"/property/{row[0]}/legal_documents/property_photo.png")
            ,"subscription":row[6]
            if image_exists else settings.DEFAULT_IMG_URL
        })

    await redis_set_data(cache_key, properties)
    return properties




@prop.get("/get-property-info/{property_id}")
async def get_property_info(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user(token, db)
        cache_key = f"property:{property_id}:info"
        cached = await redis_get_data(cache_key)
        # if cached:
        #     return cached
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # Convert SQLAlchemy row to dict
        full_data = {c.name: getattr(property_obj, c.name) for c in property_obj.__table__.columns}

        # ⭐ HARD-CODED JSON RESPONSE (BEST)
        data = {
            "property_id": property_id,
            "property_name": full_data["property_name"],
            "plot_number": full_data["plot_number"],
            "project_name_or_venture": full_data["project_name_or_venture"],
            "house_number": full_data["house_number"],
            "street": full_data["street"],
            "mandal": full_data["mandal"],
            "district": full_data["district"],
            "city": full_data["city"],

            # Convert Decimal → int
            "pin_code": int(full_data["pin_code"]) if full_data["pin_code"] else None,

            "type": full_data["type"],
            "sub_type": full_data["sub_type"],
            "facing": full_data["facing"],

            # Convert Decimal → float
            "size": f"{int(full_data['size'])} { full_data['scale']}" if full_data["size"] else None,
            "scale": full_data["scale"],
            "rental_income": float(full_data["rental_income"]) or 0.0,

            "state": full_data["state"],
            "is_verified": full_data["is_verified"],
            "alternate_name": full_data["alternate_name"],
            "alternate_contact": full_data["alternate_contact"],
            "gmap_url":full_data.get('gmap_url'),
           "subscription": full_data.get('active_sub')
        }
        print(f"{int(full_data['size'])} { full_data['scale']}")
        # Add property photo
        image_path = f"property/{property_id}/legal_documents/property_photo.png"
        exists = await check_object_exists(image_path)

        data["property_photo"] = (
            await get_image_cloudfront_signed_url(f"/{image_path}") if exists else settings.DEFAULT_IMG_URL
        )

        data["property_photos"] = (
            await get_reference_images(property_id=full_data['property_id'],token=token,db=db)
        )
        print(data)
        await redis_set_data(cache_key, data)
        return data

    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))


@prop.get("/get-reference-images/{property_id}")
async def get_reference_images(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    try:
        user=await get_current_user(token,db)
        cache_key = f"property:{property_id}:reference-images"
        cached = await redis_get_data(cache_key)

        # if cached:
        #     return cached

        s3_keys = await list_s3_objects(prefix=f"property/{property_id}/property_photos/")
        signed_urls = await asyncio.gather(
            *[generate_cloudfront_presigned_url(k) for k in s3_keys]
        )

        result = await db.execute(select(PropertyDocuments).where(PropertyDocuments.property_id == property_id))
        doc = result.scalar_one_or_none()
        print(doc.property_photos)

        response = {
            "is_verified": doc.property_photos if doc else False,
            "property_photos": signed_urls,
        }

        await redis_set_data(cache_key, response)
        return response
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))


@prop.get("/get-property-documents/{property_id}")
async def get_property_documents(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        user=await get_current_user(token,db)
        cache_key = f"property:{property_id}:documents"
        cached = await redis_get_data(cache_key)

        # if cached:
        #     return cached

        s3_keys = await list_s3_objects(prefix=f"property/{property_id}/legal_documents/")

        result = await db.execute(select(PropertyDocuments).where(PropertyDocuments.property_id == property_id))
        doc = result.scalar_one_or_none()

        response = {}
        for key in s3_keys:
            file_name = key.split("/")[-1].split(".")[0]
            response[file_name] = {
                "url": await generate_cloudfront_presigned_url(key),
                "is_verified": getattr(doc, file_name, False) if doc else False
            }

        await redis_set_data(cache_key, response)
        return response

    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))
    




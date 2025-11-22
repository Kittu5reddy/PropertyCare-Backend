from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from jose import JWTError
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

# Import utils & models
from app.core.controllers.auth.main import oauth2_scheme, get_db, get_current_user
from app.user.validators.propertydetails import PropertyDetailForm, UpdatePropertyNameRequest
from app.user.validators.changeproperty import PropertyDetailsUpdate as ChangePropertySchema
from app.user.models.users import User

from app.core.models.property_details import PropertyDetails
from app.core.models.property_documents import PropertyDocuments
from app.user.controllers.forms.utils import (
    property_upload_image_as_png,
    property_upload_documents,
    property_delete_document,
    property_delete_single_document,
    invalidate_files,
    list_s3_objects,
    generate_cloudfront_presigned_url,
    get_image,
    check_object_exists
)
from app.core.models import (
    get_redis,
    redis_get_data,
    redis_set_data,
    redis_delete_data,
    redis_delete_pattern
)

from config import settings
from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError
from app.core.controllers.auth.utils import generate_property_id

prop = APIRouter(prefix="/property", tags=["user property"])

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


@prop.post("/upload-document/{property_id}")
async def upload_property_documents(
    property_id: str,
    category: str = Form(...),
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_current_user(token, db)

        contents = await file.read()
        file_data = {"filename": file.filename, "bytes": contents, "content_type": file.content_type}

        result = await property_upload_documents(file_data, category, property_id)
        await redis_delete_data(f"property:{property_id}:documents")

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result

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
        await get_current_user(token, db)

        results = []
        for file in files:
            content = await file.read()
            file_data = {"filename": file.filename, "bytes": content, "content_type": file.content_type}
            results.append(await property_upload_image_as_png(file_data, category, property_id))

        await redis_delete_pattern(f"property:{property_id}:*")
        return {"status": "success", "files": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@prop.post("/add-property")
async def user_add_property(
    form: PropertyDetailForm,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user(token, db)

        result = await db.execute(select(func.max(PropertyDetails.id)))
        next_id = (result.scalar_one_or_none() or 0) + 1 + int(settings.PROPERTY_STARTING_NUMBER)
        property_id = generate_property_id(next_id)

        property = PropertyDetails(property_id=property_id, user_id=user.user_id, **form.dict())
        documents = PropertyDocuments(property_id=property_id)

        db.add(property)
        await db.commit()
        await db.refresh(property)

        db.add(documents)
        await db.commit()

        await redis_delete_pattern(f"user:{user.user_id}:*")

        return {"property_id": property_id, "message": "Property added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ======================================================
#                     P U T
# ======================================================

@prop.put("/update-property-name/{property_id}")
async def update_property_name(
    property_id: str,
    payload: UpdatePropertyNameRequest,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user(token, db)

        result = await db.execute(select(PropertyDetails).where(PropertyDetails.property_id == property_id))
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        property_obj.property_name = payload.property_name
        await db.commit()
        await db.refresh(property_obj)

        await redis_delete_data(f"property:{property_id}:info")

        return {"message": "Property name updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating property: {str(e)}")


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
        user = await get_current_user(token, db)

        result = await db.execute(select(PropertyDetails).where(PropertyDetails.property_id == property_id))
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # Apply updates dynamically
        for key, value in payload.dict(exclude_unset=True).items():
            setattr(property_obj, key, value)

        await db.commit()
        await db.refresh(property_obj)

        await redis_delete_data(f"property:{property_id}:info")

        return {"message": "Updated successfully", "property": property_obj}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating property details: {str(e)}")

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
        result = await property_delete_document(category, property_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        await redis_delete_data(f"property:{property_id}:documents")
        return {"message": "Document deleted"}

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
        file_url = payload["property_photos"]
        filename = file_url.split("/")[-1].split("?")[0]

        result = await property_delete_single_document("property_photos", property_id, filename)

        await redis_delete_data(f"property:{property_id}:reference-images")
        return {"message": "Reference image deleted", "deleted": filename}

    except Exception as e:
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
    cache_key = f"user:{user_id}:property-list"

    cached = await redis_get_data(cache_key)
    if cached:
        return cached

    user = await get_current_user(token, db)

    result = await db.execute(
        select(
            PropertyDetails.property_id,
            PropertyDetails.property_name,
            PropertyDetails.city,
            PropertyDetails.type,
            PropertyDetails.size
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
            "size": str(row[4]),
            "image_url": await get_image(f"/property/{row[0]}/legal_documents/property_photo.png")
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
        # cached = await redis_get_data(cache_key)
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
            "size": float(full_data["size"]) if full_data["size"] else None,
            "scale": full_data["scale"],
            "rental_income": float(full_data["rental_income"]) or 0.0,

            "state": full_data["state"],
            "is_verified": full_data["is_verified"],
            "alternate_name": full_data["alternate_name"],
            "alternate_contact": full_data["alternate_contact"],
        }

        # Add property photo
        image_path = f"property/{property_id}/legal_documents/property_photo.png"
        exists = await check_object_exists(image_path)

        data["property_photo"] = (
            await get_image(f"/{image_path}") if exists else settings.DEFAULT_IMG_URL
        )

        data["property_photos"] = (
            await get_reference_images(property_id=full_data['property_id'],token=token,db=db)
        )

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

        if cached:
            return cached

        s3_keys = await list_s3_objects(prefix=f"property/{property_id}/property_photos/")
        signed_urls = await asyncio.gather(
            *[generate_cloudfront_presigned_url(k) for k in s3_keys]
        )

        result = await db.execute(select(PropertyDocuments).where(PropertyDocuments.property_id == property_id))
        doc = result.scalar_one_or_none()

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

        if cached:
            return cached

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
    



# @prop.get("/get-property-reports/{property_id}")
# async def get_property_reports(
#     property_id: str,
#     token: str = Depends(oauth2_scheme),
#     db: AsyncSession = Depends(get_db),
# ):
#     try:
        
#         user=await get_current_user(token,db)
#         cache_key = f"property:{property_id}:reports"
#         cached = await redis_get_data(cache_key)

#         if cached:
#             return cached

#         s3_keys = await list_s3_objects(prefix=f"property/{property_id}/reports/")

#         result = await db.execute(select(PropertyDocuments).where(PropertyDocuments.property_id == property_id))
#         doc = result.scalar_one_or_none()

#         response = {}
#         urls=[]
#         for key in s3_keys:
#             file_name = key.split("/")[-1].split(".")[0]
#             url= await generate_cloudfront_presigned_url(key),
#             response[file_name] = urls.append(u)
            


#         await redis_set_data(cache_key, response)
#         return response

#     except HTTPException as e:
#         raise e 
#     except JWTError as e:
#         raise HTTPException(status_code=401,detail="Token Expired")
#     except Exception as e:
#         print(str(e))
#         raise HTTPException(status_code=500,detail=str(e))

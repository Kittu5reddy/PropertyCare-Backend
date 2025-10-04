from fastapi import APIRouter,Depends,HTTPException,Form, Body
from jose import JWTError
from app.core.controllers.auth.main import oauth2_scheme,AsyncSession,get_db,get_current_user
from app.user.controllers.surveillance.main import  get_current_month_photos
from app.user.validators.propertydetails import  PropertyDetailForm,UpdatePropertyNameRequest
from app.user.models.users import User
from app.core.models import get_redis,redis,redis_get_data,redis_set_data,redis_delete_data,redis_delete_data,redis_delete_pattern
import json
from app.core.models.property_documents import PropertyDocuments
from .utils import generate_property_id
from sqlalchemy import select,func,and_
from app.core.models.property_details import PropertyDetails
from app.user.controllers.forms.utils import property_upload_image_as_png,property_upload_documents,property_delete_document,invalidate_files,property_delete_single_document
from fastapi import APIRouter, Depends, UploadFile, File
from app.user.controllers.forms.utils import list_s3_objects,get_image,check_object_exists
from config import settings
from datetime import datetime,date
from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError
prop=APIRouter(prefix='/property',tags=['user property'])


# ======================
#     P O S T
# ======================

@prop.post("/is-property-exists")
async def is_property_exist(
    form: PropertyDetailForm,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        
        user: User = await get_current_user(token, db)

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


        property_obj = result.first()
        return {"is_property_exist": property_obj is not None}

    except HTTPException as http_exc:
        raise http_exc
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Failed to check property existence: {str(e)}")





@prop.post('/upload-document/{property_id}')
async def upload_property_documents(
    property_id: str,
    category: str = Form(...),  
    file: UploadFile = File(...),            
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)
        cache_key="property:{property_id}:documents"
        # Convert UploadFile → dict
        contents = await file.read()
        file_data = {
            "filename": file.filename,
            "bytes": contents,
            "content_type": file.content_type,
        }

        # Call existing helper
        result = await property_upload_documents(file_data, category, property_id)
        await redis_delete_data(cache_key)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except HTTPException as http_exc:
        raise http_exc
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Failed to check property existence: {str(e)}")
        




@prop.post("/add-reference-image/{property_id}")
async def add_reference_photo(
    property_id: str,
    category: str = Form(...),  # required
    files: list[UploadFile] = File(...),  # multiple files
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user(token, db)
        cache_key = f"property:{property_id}:reference-images"
        results = []
        for file in files:
            contents = await file.read()
            file_data = {
                "filename": file.filename,
                "bytes": contents,
                "content_type": file.content_type,
            }
            result = await property_upload_image_as_png(file_data, category, property_id)
            results.append(result)
        await redis_delete_pattern(f"property:{property_id}:*")
        return {"status": "success", "files": results}

    except HTTPException as e:
        raise e
    except JWTError as e:
        raise HTTPException(status_code=401,detail=f"Token Expired")
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload reference photo: {str(e)}")


@prop.post("/add-property")
async def user_add_property(
    form: PropertyDetailForm,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Authenticate
        user: User = await get_current_user(token, db)

        # Generate property_id
        result = await db.execute(select(func.max(PropertyDetails.id)))
        last_id = result.scalar_one_or_none() or 0
        next_id = last_id + 1
        property_id = generate_property_id(next_id)

        # Create records
        property = PropertyDetails(
            property_id=property_id,
            property_name=form.name,
            survey_number=form.survey_number,
            plot_number=form.plot_number,
            user_id=user.user_id,
            house_number=form.house_number,
            project_name_or_venture=form.project_name,
            street=form.street,
            city=form.city,
            state=form.state,
            district=form.district,
            mandal=form.mandal,
            country="India",
            pin_code=int(form.pin_code) if form.pin_code else None,
            size=int(form.size) if form.size else None,
            phone_number=form.owner_contact,
            land_mark=form.nearby_landmark,
            latitude=str(form.latitude) if form.latitude else None,
            longitude=str(form.longitude) if form.longitude else None,
            facing=form.facing,
            type=form.type_of_property.strip() if form.type_of_property else None,
            sub_type=form.sub_type_property.strip() if form.sub_type_property else None,
            description=form.additional_notes,
        )
        
        await redis_delete_pattern(f"user:{user.user_id}:*")
        documents = PropertyDocuments(property_id=property_id)
        db.add(property)
        await db.commit()
        await db.refresh(property)
        # db.add_all([property, documents]) 
        db.add(documents)

        # Save
        await db.commit()
        await db.refresh(documents)

        return {"property_id": property_id, "message": "Property added successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add property: {str(e)}")

@prop.post("/add-documents/{property_id}")
async def property_documents(
    property_id: str,
    files: list[UploadFile] = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        # Validate ownership
        property_obj = await db.execute(
            select(PropertyDetails).where(
                PropertyDetails.user_id == user.user_id,
                PropertyDetails.property_id == property_id
            )
        )
        property_obj = property_obj.scalar_one_or_none()
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found or unauthorized")

        # Validate document container
        authorized = await db.execute(
            select(PropertyDocuments).where(PropertyDocuments.property_id == property_id).limit(1)
        )
        authorized = authorized.scalar_one_or_none()
        if not authorized:
            raise HTTPException(status_code=400, detail="No document container found for this property")
        
        uploaded = []
        for file in files:
            content = await file.read()
            if "__" in file.filename:
                doc_type, original_name = file.filename.split("__", 1)
            else:
                doc_type, original_name = "unknown", file.filename

            # Prevent overwriting verified docs
            if getattr(authorized, doc_type, False):
                raise HTTPException(
                    status_code=400,
                    detail=f"Document '{doc_type}' is already verified, contact admin to update"
                )

            # Prepare dict
            file_dict = {
                "doc_type": doc_type,
                "filename": original_name,
                "size": len(content),
                "bytes": content,
            }

            # Upload
            if doc_type in ["property_photos", "property_photo"]:
                result = await property_upload_image_as_png(file_dict, doc_type, property_id)
            else:
                result = await property_upload_documents(file_dict, doc_type, property_id)

            uploaded.append({
                "doc_type": doc_type,
                "filename": original_name,
                "size": len(content),
                "s3_path": result.get("file_path") if result else None
            })

        # Invalidate cache
        cache_key = f"property:{property_id}:documents"
        await redis_delete_data(cache_key)

        return {"property_id": property_id, "uploaded": uploaded}

    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload documents: {str(e)}")





@prop.put("/update-property-name/{property_id}")
async def update_property_name(
    property_id: str,
    payload: UpdatePropertyNameRequest,   
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # Update name
        property_obj.property_name = payload.property_name
        await db.commit()
        await db.refresh(property_obj)
        cache_key = f"property:{property_id}:info"
        await redis_delete_data(cache_key)
        return {"message": "Property name updated successfully", "property": property_obj.property_name}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating property: {str(e)}")


@prop.put("/change-property-photo/{property_id}")
async def change_property_photo(
    property_id: str,
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        # Check if property exists
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # Upload to S3 (pass as dict to function)
        file_content = await file.read()
        result = await property_upload_image_as_png(
            {"bytes": file_content},  # dict wrapper
            "property_photo",         # category
            property_id               # property_id
        )
        await invalidate_files(f'/property/{property_id}/legal_documents/property_photo.png')
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        cache_key = f"property:{property_id}:info"
        await redis_delete_data(cache_key)
        return result

    except HTTPException as e:
        raise e   # re-raise FastAPI HTTP errors

    except Exception as e:
        # Log it if needed
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error{str(e)}")



from pydantic import BaseModel
from typing import Dict, Any

class UpdatePropertyDetailsRequest(BaseModel):
    details: Dict[str, Any]
from typing import Dict, Any
from fastapi import Body

@prop.put("/update-property-details/{property_id}")
async def update_property_details(
    property_id: str,
    payload: Dict[str, Any] = Body(...),   # accepts raw JSON as dict
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        # Check if property exists
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.property_id == property_id)
        )
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        if property_obj.is_verified:
            raise HTTPException(status_code=400, detail="Property is verfied contact to admin team")
        # Dynamically update fields from JSON
        for key, value in payload.items():
            if hasattr(property_obj, key):
                setattr(property_obj, key, value)

        await db.commit()
        await db.refresh(property_obj)
        cache_key = f"property:{property_id}:info"
        await redis_delete_data(cache_key)
        return {
            "message": "Property details updated successfully",
            "property": property_obj
        }
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token as Expired")
    except Exception as e:
        await db.rollback()
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Error updating property: {str(e)}")





# ==================================
#     D   E   L    E    T    E
# ==================================



@prop.delete("/delete-document/{property_id}")
async def delete_document(
    property_id: str,
    category: str,   # pass category name
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    
    user = await get_current_user(token, db)
    cache_key="property:{property_id}:documents"
    data=await db.execute(select(PropertyDocuments).where(PropertyDocuments.property_id==property_id).limit(1))
    data=data.scalar_one_or_none()
    is_verified=getattr(data,category,None)
    if is_verified:
        raise HTTPException(status_code=400,detail="Document is verifed contact admin team")
    result = await property_delete_document(category, property_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    await redis_delete_data(cache_key)
    return result


@prop.delete("/delete-reference-image/{property_id}")
async def delete_reference_photo(
    property_id: str,
    property_photos: str = Body(..., embed=True),  # now expects { "property_photos": "..." }
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):

    try:    
        user = await get_current_user(token, db)
        filename = property_photos.split("/")[-1]
        if "?v" in filename:
            filename=filename.split('?')[0]
        print(filename)
        print(filename,property_id)
        result = await property_delete_single_document(
            category="property_photos",
            property_id=property_id,
            filename=filename
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        cache_key = f"property:{property_id}:reference-images"
        await redis_delete_data(cache_key)
        return {"status": "success", "deleted_file": result["deleted_file"]}

    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete reference photo: {str(e)}")



























































































# ============================
#     G   E   T
# ============================




@prop.get("/properties-list/{user_id}")
async def get_property_list(
    user_id:str,
    token:str=Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db),
    redis_client:redis.Redis=Depends(get_redis)
):
    cache_key = f"user:{user_id}:property-list"

    cached_data = await redis_get_data(cache_key)
    if cached_data:
        return cached_data
    user=await get_current_user(token,db)
    result = await db.execute(
        select(
            PropertyDetails.property_id,
            PropertyDetails.property_name,
            PropertyDetails.city,
            PropertyDetails.type,
            PropertyDetails.size
        ).where(PropertyDetails.user_id == user_id)
    )
    rows = result.all()  # list of tuples
    properties = []
    for row in rows:
        photos = await check_object_exists(f"property/{row[0]}/legal_documents/property_photo.png")
        properties.append({
            "property_id": row[0],
            "name": row[1],
            "location": row[2],
            "type": row[3],
            "size": str(row[4]),
            'status':"active",
            'subscription':str(date.today()),
            "image_url":  get_image(f"/property/{row[0]}/legal_documents/property_photo.png") if photos else settings.DEFAULT_IMG_URL
        })

    await   redis_set_data(cache_key,properties)
        # print("miss")
    return properties



@prop.get("/get-property-info/{property_id}")
async def get_property_info(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client:redis.Redis=Depends(get_redis)
):
    try:
        # ✅ Cache key
        cache_key = f"property:{property_id}:info"


        cached_data = await redis_get_data(cache_key)
        if cached_data:
            print(("hit"))
            return cached_data

        # 🔹 Step 2: Validate token
        user = await get_current_user(token, db)

        # 🔹 Step 3: Query DB
        result = await db.execute(
            select(
                PropertyDetails.property_id,
                PropertyDetails.property_name,
                PropertyDetails.survey_number,
                PropertyDetails.plot_number,
                PropertyDetails.project_name_or_venture,
                PropertyDetails.house_number,
                PropertyDetails.street,
                PropertyDetails.mandal,
                PropertyDetails.district,
                PropertyDetails.city,
                PropertyDetails.pin_code,
                PropertyDetails.state,
                PropertyDetails.size,
                PropertyDetails.facing,
                PropertyDetails.type,
                PropertyDetails.sub_type,
                PropertyDetails.latitude,
                PropertyDetails.longitude,
                PropertyDetails.gmap_url,
                PropertyDetails.land_mark,
                PropertyDetails.description,
                PropertyDetails.reference_images
            ).where(PropertyDetails.property_id == property_id).limit(1)
        )

        row = result.mappings().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Property not found")

        data = dict(row)

        # 🔹 S3 photos
        objects = await list_s3_objects(prefix=f"property/{property_id}/property_photos/")
        data['property_photos'] = [get_image("/" + images) for images in objects]
        # print(data['property_photos'])
        # 🔹 Legal photo
        object_key = f'property/{property_id}/legal_documents/property_photo.png'
        is_exists = await check_object_exists(object_key)
        if is_exists:
            data['property_photo'] = get_image("/" + object_key)
        else:
            data['property_photo'] = settings.DEFAULT_IMG_URL

        # 🔹 Monthly photos
        monthly_photos = await get_current_month_photos(property_id, token, db)
        data['monthly-photos'] = monthly_photos.get('photos')

        # 🔹 Step 4: Save to Redis with TTL (5 min)
        await redis_set_data(cache_key,data)
        return data

    except HTTPException as http_exc:
        raise http_exc
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch property info: {str(e)}")

@prop.get("/get-reference-images/{property_id}")
async def get_reference_images(
    property_id: str,
    token:str=Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis_client:redis.Redis=Depends(get_redis)
):
    try:
                # ✅ Cache key
        cache_key = f"property:{property_id}:reference-images"
        # 🔹 Step 1: Try to fetch from Redis
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            print(("hit"))
            return json.loads(cached_data)

        objects = await list_s3_objects(prefix=f"property/{property_id}/property_photos/")
        # print(objects)
        # Convert S3 keys to signed/public URLs if needed
        image_urls = list(map(get_image,list("/"+images for images in objects)))
        data={
            "property_photos": image_urls
        }
        await redis_set_data(cache_key=cache_key,data=data)
        print("miss")
        return data
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch reference images: {str(e)}")
    


@prop.get("/get-property-documents/{property_id}")
async def get_reference_documents(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        cache_key="property:{property_id}:documents"
        cached_data = await redis_get_data(cache_key)
        if cached_data:
            # print(("hit"))
            return cached_data       
        # Authenticate user
        user = await get_current_user(token, db)

        # List objects from S3
        objects = await list_s3_objects(prefix=f"property/{property_id}/legal_documents/")
        image_urls = list(map(get_image, map(lambda x:"/"+x,objects)))

        # Fetch DB record
        result = await db.execute(
            select(PropertyDocuments).where(PropertyDocuments.property_id == property_id)
        )
        data = result.scalar_one_or_none()

        # Construct response
        response = {}
        for image in image_urls:
            print((image))
            key = image.split("/")[-1].split('.')[0]
            response[key] = {
                "url": image,
                "isverified": getattr(data, key, False) if data else False
            }
        await redis_set_data(cache_key=cache_key,data=response)
        return response
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Invalid Token")
    except ClientError as e:
        raise HTTPException(status_code=502, detail=f"S3 Error: {str(e)}")
    except SQLAlchemyError as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")


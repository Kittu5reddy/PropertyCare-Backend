from fastapi import APIRouter,Depends,HTTPException
from jose import JWTError
from app.user.controllers.auth.main import oauth2_scheme,AsyncSession,get_db,get_current_user
from app.user.validators.propertydetails import  PropertyDetailForm
from app.user.models.users import User
from .utils import generate_property_id
from sqlalchemy import select,func,and_
from app.user.models.property_details import PropertyDetails
prop=APIRouter(prefix='/property',tags=['user property'])
from app.user.controllers.forms.utils import property_upload_image_as_png,property_upload_documents,create_property_directory
from fastapi import APIRouter, Depends, UploadFile, File
from app.user.controllers.forms.utils import list_s3_objects,get_image,check_object_exists
from config import settings
from datetime import datetime,date
from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError
from PIL import UnidentifiedImageError
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

@prop.post("/add-property")
async def user_add_property(
    form: PropertyDetailForm,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        
        user:User=await get_current_user(token,db)
        result = await db.execute(select(func.max(PropertyDetails.id)))
        last_id = result.scalar_one_or_none() or 0 # None if no rows
        next_id = last_id + 1  # safe increment
        property_id = generate_property_id(next_id)
        property = PropertyDetails(
        property_id=property_id,  # unique ID
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
        country="India",  # default
        pin_code=int(form.pin_code),
        size=int(form.size),
        phone_number=form.owner_contact,
        land_mark=form.nearby_landmark,
        latitude=form.latitude  ,
        longitude=form.longitude ,
        facing=form.facing,
        type=f"{form.type_of_property} ",
        sub_type=f" {form.sub_type_property}",
        description=form.additional_notes,
    )
        await create_property_directory(property_id)
        db.add(property)
        await db.commit()
        await db.refresh(property)
        return {"property_id":property_id}
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update first name: {str(e)}")
    

@prop.post("/add-documents/{property_id}")
async def property_documents(
    property_id: str,
    files: list[UploadFile] = File(...)
):
    uploaded = []

    for file in files:
        content = await file.read()
        if "__" in file.filename:
            doc_type, original_name = file.filename.split("__", 1)
        else:
            doc_type, original_name = "unknown", file.filename

        # Internal dict (with bytes for upload)
        file_dict = {
            "doc_type": doc_type,
            "filename": original_name,
            "size": len(content),
            "bytes": content,
        }

        # Upload to S3
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


    return {"property_id": property_id, "uploaded": uploaded}


@prop.get("/properties-list/{user_id}")
async def get_property_list(
    user_id:str, 
    db: AsyncSession = Depends(get_db)
):
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


    return properties


@prop.get("/get-property-info/{property_id}")
async def get_property_info(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Validate token
        user = await get_current_user(token, db)

        # Execute query
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
            ).where(PropertyDetails.property_id == property_id).limit(1)
        )

        # Get one row as mapping (dict-like)
        row = result.mappings().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Property not found")

        data = dict(row)  # Convert RowMapping → dict
        # print(data)
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
    db: AsyncSession = Depends(get_db)
):
    try:
        objects = await list_s3_objects(prefix=f"property/{property_id}/property_photos/")
        # print(objects)
        # Convert S3 keys to signed/public URLs if needed
        image_urls = list(map(get_image,list("/"+images for images in objects)))

        return {
            "property_photos": image_urls
        }
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch reference images: {str(e)}")
    




@prop.get("/get-property-documents/{property_id}")
async def get_reference_images(
    property_id: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Authenticate user
        user = await get_current_user(token, db)

        # List objects from S3
        objects = await list_s3_objects(prefix=f"property/{property_id}/legal_documents/")
        image_urls = list(map(get_image, objects))

        # Map file names to URLs
        image_urls = {image.split("/")[-1].split('.')[0]: image for image in image_urls}
        print(image_urls)
        return image_urls

    except ClientError as e:
        # AWS S3 errors
        print(f"S3 Error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"S3 Error: {str(e)}")

    except SQLAlchemyError as e:
        # Database-related errors
        print(f"Database Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

    except UnidentifiedImageError:
        # If something goes wrong with image processing
        print("Invalid image format found in S3")
        raise HTTPException(status_code=400, detail="Invalid image format found in S3")

    except HTTPException as e:
        # Pass through already raised HTTP exceptions
        raise e

    except Exception as e:
        # Fallback for unexpected errors
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")




@prop.get('/get-property-image/{property_id}')
async def get_reference_images(property_id: str):
    try:
        object_key = f'property/{property_id}/legal_documents/property_photo.png'

        # Check if object exists in S3
        is_exists = await check_object_exists(object_key)

        if is_exists:
            return {"property_photo":get_image("/"+object_key)}
        else:
            return settings.DEFAULT_IMG_URL

    except ClientError as e:
        # AWS S3 related error
        print(f"S3 Error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"S3 Error: {str(e)}")

    except HTTPException as e:
        # Re-raise if already an HTTPException
        raise e

    except Exception as e:
        # Unexpected error
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
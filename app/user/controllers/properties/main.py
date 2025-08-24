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
from app.user.models.documents import PropertyDocuments

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
        if doc_type == "plot_photos":
            result=await property_upload_image_as_png(file_dict, "original_photos", property_id)
            
        else:
            await property_upload_documents(file_dict, doc_type, property_id)
            # obj:PropertyDocuments=PropertyDocuments(document_id=)
        # Public response metadata (no raw bytes)
        uploaded.append({
            "doc_type": doc_type,
            "filename": original_name,
            "size": len(content),
        })

    return {"property_id": property_id, "uploaded": uploaded}

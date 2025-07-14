

from app.controllers.forms.utils import upload_documents
from typing import Annotated, Optional
from fastapi import Form, File, UploadFile
from enum import Enum

class Gender(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"
async def get_personal_details(
    first_name: Annotated[str, Form(...)],
    last_name: Annotated[str, Form(...)],
    user_name: Annotated[str, Form(...)],
    dob: Annotated[str, Form(...)],
    gender: Annotated[Gender, Form(...)],
    contact_number: Annotated[str, Form(...)],
    house_number: Annotated[str, Form(...)],
    street: Annotated[str, Form(...)],
    city: Annotated[str, Form(...)],
    state: Annotated[str, Form(...)],
    country: Annotated[str, Form(...)],
    pin_code: Annotated[str, Form(...)],
    pan_number: Annotated[str, Form(...)],
    aadhaar_number: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    profile_photo: Annotated[Optional[UploadFile], File()] = None,
    pan_document: Annotated[Optional[UploadFile], File()] = None,
    aadhaar_document: Annotated[Optional[UploadFile], File()] = None,
):
    documents = {}

    async def upload_and_store(file: UploadFile, category: str):
        content = await file.read()
        file_dict = {
            "filename": file.filename,
            "bytes": content
        }

        return await upload_documents(file_dict, category=category, user_id=user_name)

    if profile_photo:
        documents["profile_photo"] = await upload_and_store(profile_photo, category="profile_photo")

    if pan_document:
        documents["pan_document"] = await upload_and_store(pan_document, category="pan")

    if aadhaar_document:
        documents["aadhaar_document"] = await upload_and_store(aadhaar_document, category="aadhaar")

    return {
        "first_name": first_name,
        "last_name": last_name,
        "user_name": user_name,
        "date_of_birth": dob,
        "gender": gender,
        "contact_number": contact_number,
        "description": description,
        "address": {
            "house_number": house_number,
            "street": street,
            "city": city,
            "state": state,
            "country": country,
            "pincode": pin_code,
        },
        "govt_ids": {
            "pan_number": pan_number,
            "aadhaar_number": aadhaar_number,
        },
        "documents": documents
    }

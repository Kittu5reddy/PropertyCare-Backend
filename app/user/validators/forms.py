

from app.user.controllers.forms.utils import upload_documents,upload_image_as_png
from app.core.controllers.auth.utils import get_current_user
from typing import Annotated, Optional
from app.core.controllers.auth.main import oauth2_scheme
from app.core.models import get_db
from fastapi import Form, File, UploadFile,Depends,HTTPException,status
from app.user.models.required_actions import RequiredAction
from enum import Enum

class Gender(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"
from datetime import date

# async def get_personal_details(
#     first_name: Annotated[str, Form(...)],
#     last_name: Annotated[str, Form(...)],
#     user_name: Annotated[str, Form(...)],
#     dob: Annotated[date, Form(...)],  
#     gender: Annotated[Gender, Form(...)],
#     contact_number: Annotated[int, Form(...)],
#     house_number: Annotated[str, Form(...)],
#     street: Annotated[str, Form(...)],
#     city: Annotated[str, Form(...)],
#     state: Annotated[str, Form(...)],
#     country: Annotated[str, Form(...)],
#     pin_code: Annotated[str, Form(...)],
#     nri:Annotated[bool,Form(...)],
#     pan_number: Annotated[str, Form(...)],
#     aadhaar_number: Annotated[str, Form(...)],
#     description: Annotated[str, Form(...)],
#     profile_photo: Annotated[Optional[UploadFile], File()] = None,
#     pan_document: Annotated[Optional[UploadFile], File()] = None,
#     aadhaar_document: Annotated[Optional[UploadFile], File()] = None,
#     token=Depends(oauth2_scheme),
#     db=Depends(get_db)
# ):
#     documents = {}
#     user = await get_current_user(token, db)

#     async def upload_and_store(file: UploadFile, category: str):
#         content = await file.read()
#         file_dict = {"filename": file.filename, "bytes": content}
#         if category == "profile_photo":
#             return await upload_image_as_png(file_dict, category=category, user_id=user.user_id)
#         return await upload_documents(file_dict, category=category, user_id=user.user_id)

#     if profile_photo:
#         documents["profile_photo"] = await upload_and_store(profile_photo, category="profile_photo")
#     if pan_document:
#         documents["pan_document"] = await upload_and_store(pan_document, category="pan")
#     if aadhaar_document:
#         documents["aadhaar_document"] = await upload_and_store(aadhaar_document, category="aadhaar")
#     return {
#         "first_name": first_name,
#         "last_name": last_name,
#         "user_name": user_name,
#         "date_of_birth": dob,   # 👈 already a date object now
#         "gender": gender,
#         "contact_number": contact_number,
#         "description": description,
#         "address": {
#             "house_number": house_number,
#             "street": street,
#             "city": city,
#             "state": state,
#             "country": country,
#             "pincode": pin_code,
#         "nri":nri,
#         },
#         "govt_ids": {
#             "pan_number": pan_number,
#             "aadhaar_number": aadhaar_number,
#         },
#         "documents": documents
#     }

# from typing import Optional, Annotated
# from datetime import date
# from fastapi import Form, File, UploadFile, Depends, HTTPException, status

# @app.post("/personal-details")
async def get_personal_details(
    first_name: Annotated[str, Form(...)],
    last_name: Annotated[str, Form(...)],
    user_name: Annotated[str, Form(...)],
    dob: Annotated[date, Form(...)],
    gender: Annotated[str, Form(...)],
    contact_number: Annotated[int, Form(...)],
    house_number: Annotated[str, Form(...)],
    street: Annotated[str, Form(...)],
    city: Annotated[str, Form(...)],
    state: Annotated[str, Form(...)],
    country: Annotated[str, Form(...)],
    pin_code: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    nri: Annotated[Optional[str], Form()] = None,   # ✅ fix here
    pan_number: Annotated[Optional[str], Form()] = None,
    aadhaar_number: Annotated[Optional[str], Form()] = None,
    profile_photo: Annotated[Optional[UploadFile], File()] = None,
    pan_document: Annotated[Optional[UploadFile], File()] = None,
    aadhaar_document: Annotated[Optional[UploadFile], File()] = None,
    token=Depends(oauth2_scheme),
    db=Depends(get_db)
):
    user = await get_current_user(token, db)

    # ✅ Convert NRI checkbox string to boolean safely
    nri = str(nri).lower() in ("true", "1", "on", "yes")

    # ✅ Validation Logic
    if not nri:
        if not pan_number or not aadhaar_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PAN and Aadhaar details are required for non-NRI users."
            )
    else:
        # Clear unnecessary fields for NRI users
        pan_number = None
        aadhaar_number = None
        pan_document = None
        aadhaar_document = None

    async def upload_and_store(file: UploadFile, category: str):
        content = await file.read()
        file_dict = {"filename": file.filename, "bytes": content}
        if category == "profile_photo":
            return await upload_image_as_png(file_dict, category=category, user_id=user.user_id)
        return await upload_documents(file_dict, category=category, user_id=user.user_id)

    documents = {}

    if profile_photo:
        documents["profile_photo"] = await upload_and_store(profile_photo, category="profile_photo")

    if not nri:
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
            "nri": nri,
        },
        "govt_ids": {
            "pan_number": pan_number,
            "aadhaar_number": aadhaar_number,
        },
        "documents": documents
    }

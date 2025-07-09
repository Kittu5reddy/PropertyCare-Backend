from fastapi import FastAPI, Form, File, UploadFile, Depends
from enum import Enum
from pydantic import BaseModel

app = FastAPI()

# Gender enum
class Gender(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"


# Dependency function to extract all form data + files
def get_personal_details(
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: str = Form(...),
    gender: Gender = Form(...),
    contact_number: int = Form(...),
    house_number: str = Form(...),
    street: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    country: str = Form(...),
    pincode: str = Form(...),
    pan_number: int = Form(...),
    aadhaar_number: int = Form(...),
    pan_document: UploadFile = File(...),
    aadhaar_document: UploadFile = File(...)
):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "gender": gender,
        "contact_number": contact_number,
        "address": {
            "house_number": house_number,
            "street": street,
            "city": city,
            "state": state,
            "country": country,
            "pincode": pincode
        },
        "govt_ids": {
            "pan_number": pan_number,
            "aadhaar_number": aadhaar_number
        },
        "documents": {
            "pan_doc_filename": pan_document.filename,
            "aadhaar_doc_filename": aadhaar_document.filename
        }
    }


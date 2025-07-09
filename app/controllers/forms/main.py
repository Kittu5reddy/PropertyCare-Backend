from fastapi import APIRouter,Depends
from app.validators.forms import get_personal_details


form=APIRouter(prefix="/form",tags=['form'])


@form.post("/submit-details")
async def submit(data: dict = Depends(get_personal_details)):
    return {"message": "Form submitted successfully", "data": data}

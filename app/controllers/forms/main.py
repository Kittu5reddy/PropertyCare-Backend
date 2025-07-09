from fastapi import APIRouter,Depends,HTTPException
from app.validators.forms import get_personal_details
from app.controllers.auth.main import oauth2_scheme
from app.models.personal_details import PersonalDetails
from app.models import get_db
form=APIRouter(prefix="/form",tags=['form'])
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
@form.post("/submit-details")
async def submit(data: dict = Depends(get_personal_details)):
    return {"message": "Form submitted successfully", "data": data}




async def check_username(username:str,db: AsyncSession,token=Depends(oauth2_scheme)):
    if token:
        result = await db.execute(select(PersonalDetails).where(PersonalDetails.username == username))
        if not  result:
            return True
        else:
            raise HTTPException(status_code=401,detail="user exits")
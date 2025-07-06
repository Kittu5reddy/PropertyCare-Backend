from fastapi import APIRouter,Depends,UploadFile, File, Depends
from app.models import get_db,AsyncSession
from app.controllers.auth.main import oauth2_scheme
from app.models.personal_details import PCUser
from sqlalchemy import select
from app.controllers.auth.utils import get_current_user
from fastapi import UploadFile, File, HTTPException, status, BackgroundTasks
from pathlib import Path
import os
import shutil
from app.controllers.forms.utils import create_user_directory, get_file_name,save_file,log_upload  # adjust import as needed
from config import settings
from app.validators.forms import PCFORM
form=APIRouter(prefix='/form',tags=['form'])


# adjust based on your model path




@form.post('/pc-user-details')
async def pc_user_details(
    form: PCFORM,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user(token, db)
    # Convert PCFORM (Pydantic) to PCUser (ORM)
    new_user = PCUser(**form.dict())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"message": "Form received successfully", "user_id": new_user.id}

@form.get("/pc-username-check/{username}")
async def check_username(
    username: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    current_user = await get_current_user(token, db)
    result = await db.execute(select(PCUser).where(PCUser.user_name == username))
    user = result.scalar_one_or_none()
    return {"username": username, "available": user is None}



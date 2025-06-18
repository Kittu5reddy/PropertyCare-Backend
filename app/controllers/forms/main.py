from fastapi import APIRouter,Depends
from app.models import get_db,AsyncSession
from app.controllers.auth.main import oauth2_scheme
from app.models.personal_details import PCUser
from sqlalchemy import select
from app.controllers.auth.utils import get_current_user
from fastapi import UploadFile, File, HTTPException, status, BackgroundTasks
from pathlib import Path
import os
import shutil
from app.controllers.forms.utils import create_user_directory, get_file_name  # adjust import as needed
from config import Config
form=APIRouter(prefix='/form')


# adjust based on your model path

@form.get("/check-username/{username}")
async def check_username(
    username: str,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    # Optional: verify token
    current_user = await get_current_user(token, db)

    result = await db.execute(select(PCUser).where(PCUser.user_name == username))
    user = result.scalar_one_or_none()  # Returns None if not found

    return {"available": user is None}





# Upload Aadhaar / PAN / Legal files etc.
@form.post("/upload/{doc_type}")
async def upload_file(
    doc_type: str,
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    # Validate doc_type
    if doc_type not in Config.SUBFOLDERS:
        raise HTTPException(status_code=400, detail="Invalid document type.")

    # Get current user
    current_user = await get_current_user(token, db)
    user_id = current_user.user_id  

    # Create user directory (if not already created)
    user_folder = await create_user_directory(user_id)

    # Destination folder
    dest_folder = os.path.join(user_folder, Config.SUBFOLDERS[doc_type])
    Path(dest_folder).mkdir(parents=True, exist_ok=True)

    # Generate filename
    filename = get_file_name(doc_type, file.filename)
    file_path = os.path.join(dest_folder, filename)

    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    return {"message": "File uploaded successfully", "filename": filename}

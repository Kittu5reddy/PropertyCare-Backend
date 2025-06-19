from datetime import datetime
import os
import asyncio
from pathlib import Path
import aiofiles
from app.models.uploadlogs import  UploadLog
from app.models import AsyncSession
import shutil
from config import Config
from fastapi import HTTPException,UploadFile
BASE_DOCUMENT_PATH = Config.BASE_DOCUMENT_PATH
SUBFOLDERS = Config.SUBFOLDERS

# =======================================
#       File Utilities
# =======================================

def get_file_name(prefix: str, original_filename: str) -> str:
    """
    Generate a timestamped filename with a prefix.
    """
    base, ext = os.path.splitext(original_filename)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    return f"{prefix}_{date_str}{ext}"

async def create_user_directory(user_id: str) -> str:
    """
    Asynchronously create the main user directory and necessary subfolders.
    """
    user_folder = os.path.join(BASE_DOCUMENT_PATH, user_id)
    await asyncio.to_thread(Path(user_folder).mkdir, parents=True, exist_ok=True)

    for folder in SUBFOLDERS.values():
        folder_path = os.path.join(user_folder, folder)
        await asyncio.to_thread(Path(folder_path).mkdir, parents=True, exist_ok=True)

    return user_folder


async def save_file(file: UploadFile, folder_name: str, save_base: str, uploaded_files: dict):
    if not file:
        return  # Skip if no file provided

    # Check for allowed extensions
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in Config.SUBFOLDERS.get(folder_name, []):
        raise HTTPException(status_code=400, detail=f"Invalid file extension for {folder_name}: {ext}")

    try:
        dest_folder = os.path.join(save_base, Config.SUBFOLDERS[folder_name])
        await asyncio.to_thread(os.makedirs, dest_folder, exist_ok=True)

        file_name = get_file_name(folder_name, file.filename)
        file_path = os.path.join(dest_folder, file_name)

        # Save file
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)

        # Store using meaningful key for downstream logging
        key_map = {
    "profile_pics": "profile_photo",
    "pan": "pan_document",
    "aadhar": "aadhaar_document"
}
        key_name = key_map.get(folder_name, folder_name)
        uploaded_files[key_name] = file_name

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file for {folder_name}: {str(e)}")


async def log_upload(db: AsyncSession, user_id: int, file_type: str, file_path: str):
    log_entry = UploadLog(user_id=user_id, file_type=file_type, file_path=file_path)
    db.add(log_entry)
    await db.commit()
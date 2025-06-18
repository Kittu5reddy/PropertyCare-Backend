from datetime import datetime
import os
import asyncio
from pathlib import Path

from config import Config

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

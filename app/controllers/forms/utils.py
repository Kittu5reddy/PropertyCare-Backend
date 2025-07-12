from imagekitio import ImageKit
from config import settings
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions


imagekit=ImageKit(public_key=settings.IMAGE_KIT_PUBLIC_KEY,
                  private_key=settings.IMAGE_KIT_PRIVATE_KEY,
                  url_endpoint=settings.IMAGE_URL_END_POINT)



async def create_user_directory(user_id: str):
    base_folder = f"user/{user_id}/"
    
    SUBFOLDERS: dict[str, str] = {
        "aadhar": "aadhar",
        "pan": "pan",
        "agreements": "agreements",
        "profile_pictures": "profile_pictures",
        "legal_documents": "legal_documents",
        
    }

    results = {}

    for key, subfolder in SUBFOLDERS.items():
        folder_path = f"{base_folder}{subfolder}/"
        
        options = UploadFileRequestOptions(
            folder=folder_path,
            use_unique_file_name=False,
            is_private_file=True
        )

        response = imagekit.upload_file(
            file=b"init",  
            file_name="init.txt",
            options=options
        )

        results[subfolder] = (
            response.response_metadata if response.response_metadata else response.error
        )

    return results

from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from config import settings
from fastapi import UploadFile
from typing import Optional

imagekit = ImageKit(
    public_key=settings.IMAGE_KIT_PUBLIC_KEY,
    private_key=settings.IMAGE_KIT_PRIVATE_KEY,
    url_endpoint=settings.IMAGE_URL_END_POINT
)

# Mapping for folder categories
CATEGORY_FOLDER_MAP = {
    "aadhaar": "aadhar",
    "pan": "pan",
    "agreements": "agreements",
    "profile": "profile_pictures",
    "legal": "legal_documents"
}


async def upload_documents(file: dict, category: str, user_id: str) -> dict:
    folder_name = CATEGORY_FOLDER_MAP.get(category.lower())
    if not folder_name:
        return {"error": f"Invalid category '{category}'"}

    folder_path = f"user/{user_id}/{folder_name}/"

    options = UploadFileRequestOptions(
        folder=folder_path,
        use_unique_file_name=True,
        is_private_file=True
    )

    response = imagekit.upload_file(
        file=file["bytes"],
        file_name=file["filename"],
        options=options
    )

    if response.error:
        return {"error": str(response.error)}

    return {
        "success": True,
        "file_id": response.file_id,
        "url": response.url,
        "thumbnail_url": response.thumbnail_url,
        "file_path": response.file_path,
    }





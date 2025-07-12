from datetime import datetime
def generate_user_id(id):
    return f'PC{datetime.utcnow().year}U{str(id).zfill(3)}'
def generate_employee_id(id):
    return f'PC{datetime.utcnow().year}E{str(id).zfill(3)}'
def generate_employee_superviser_id(id):
    return f'PC{datetime.utcnow().year}S{str(id).zfill(3)}'
def generate_employee_admin_id(id):
    return f'PC{datetime.utcnow().year}A{str(id).zfill(3)}'

print(generate_employee_admin_id(1))
print(generate_employee_id(2))
print(generate_employee_superviser_id(3))
print(generate_user_id(4))
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

from config import settings



imagekit=ImageKit(public_key=settings.IMAGE_KIT_PUBLIC_KEY,private_key=settings.IMAGE_KIT_PRIVATE_KEY,url_endpoint=settings.IMAGE_URL_END_POINT)


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
            file=b"init",  # dummy content
            file_name="init.txt",
            options=options
        )

        results[subfolder] = (
            response.response_metadata if response.response_metadata else response.error
        )

    return results


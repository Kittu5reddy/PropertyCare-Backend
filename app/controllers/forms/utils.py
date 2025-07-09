from imagekitio import ImageKit
from config import settings



imagekit=ImageKit(public_key=settings.IMAGE_KIT_PUBLIC_KEY,private_key=settings.IMAGE_KIT_PRIVATE_KEY,url_endpoint=settings.IMAGE_URL_END_POINT)


def create_user_directory(user_id: str):
    base_folder = f"user/{user_id}/personal/"
    
    SUBFOLDERS: dict[str, str] = {
        "aadhar": "aadhar",
        "pan": "pan",
        "agreements": "agreements",
        "profile_pictures": "profile_pictures",
        "legal_documents": "legal_documents"
    }
    results = {}
    for key, subfolder in SUBFOLDERS.items():
        folder_path = f"{base_folder}{subfolder}/"
        response = imagekit.upload_file(
            file=b"init",  # Small dummy content
            file_name="init.txt",
            options={
                "folder": folder_path,
                "use_unique_file_name": False,
                "is_private_file": True
            }
        )
        results[subfolder] = response.response_metadata if response.response_metadata else response.error

    return results
create_user_directory((2002))
from imagekitio import ImageKit
from config import settings



imagekit=ImageKit(public_key=settings.IMAGE_KIT_PUBLIC_KEY,private_key=settings.IMAGE_KIT_PRIVATE_KEY,url_endpoint=settings.IMAGE_URL_END_POINT)


def create_user_directory(user_id: str):
    folder_path = f"user/{user_id}/personal/"
    
    # Upload a dummy file to create the folder
    response = imagekit.upload_file(
        file=b"dummy",  # Some dummy content
        file_name="init.txt",
        options={
            "folder": folder_path,
            "use_unique_file_name": False,
            "is_private_file": True
        }
    )

    return response.response_metadata if response.response_metadata else response.error

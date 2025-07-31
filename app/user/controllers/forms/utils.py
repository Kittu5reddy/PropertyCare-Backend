import os
import aioboto3
from config import settings
from typing import Dict, Union
from botocore.exceptions import ClientError
from io import BytesIO
from PIL import Image, UnidentifiedImageError

# Config values
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_REGION = settings.AWS_REGION
S3_BUCKET = settings.S3_BUCKET_NAME

CATEGORY_FOLDER_MAP = {
    "aadhaar": "aadhar",
    "pan": "pan",
    "agreements": "agreements",
    "profile_photo": "profile_photo",
    "legal": "legal_documents"
}

# Reusable S3 session
session = aioboto3.Session()


async def create_user_directory(user_id: str) -> Dict[str, Dict[str, str]]:
    base_folder = f"user/{user_id}/"
    results = {}

    async with session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        for key, subfolder in CATEGORY_FOLDER_MAP.items():
            folder_path = f"{base_folder}{subfolder}/.keep"
            try:
                await s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=folder_path,
                    Body=b"init",
                    ACL="private"
                )
                results[subfolder] = {"status": "created", "path": folder_path}
            except ClientError as e:
                results[subfolder] = {"status": "error", "error": str(e)}

    return results


async def upload_documents(file: dict, category: str, user_id: Union[str, int]) -> dict:
    folder_name = CATEGORY_FOLDER_MAP.get(category.lower())
    if not folder_name:
        return {"error": f"Invalid category '{category}'"}

    file_name = file.get("filename", "uploaded_file")
    name, ext = os.path.splitext(file_name)
    object_key = f"user/{user_id}/{folder_name}/{category}{ext}"

    async with session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        try:
            await s3.put_object(
                Bucket=S3_BUCKET,
                Key=object_key,
                Body=file["bytes"],
                ACL="private",
                ContentType=file.get("content_type", "application/octet-stream")
            )
            return {
                "success": True,
                "file_path": object_key,
            }
        except ClientError as e:
            return {"error": str(e)}


async def upload_image_as_png(file: dict, category: str, user_id: Union[str, int]) -> dict:
    folder_name = CATEGORY_FOLDER_MAP.get(category.lower())
    if not folder_name:
        return {"error": f"Invalid category '{category}'"}

    object_key = f"user/{user_id}/{folder_name}/{category}.png"

    # Convert to PNG
    try:
        image = Image.open(BytesIO(file["bytes"])).convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
    except UnidentifiedImageError:
        return {"error": "Uploaded file is not a valid image."}
    except Exception as e:
        return {"error": f"Image conversion error: {str(e)}"}

    async with session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        try:
            await s3.put_object(
                Bucket=S3_BUCKET,
                Key=object_key,
                Body=buffer.read(),
                ACL="private",
                ContentType="image/png"
            )
            return {
                "success": True,
                "file_path": object_key,
                "content_type": "image/png"
            }
        except ClientError as e:
            return {"error": str(e)}


def get_image(filename: str) -> str:
    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com{filename}"

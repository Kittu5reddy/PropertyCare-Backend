import boto3
import os
from botocore.exceptions import ClientError
from config import settings


# Initialize S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

S3_BUCKET = settings.S3_BUCKET_NAME

# Folder category mapping
CATEGORY_FOLDER_MAP = {
    "aadhaar": "aadhar",
    "pan": "pan",
    "agreements": "agreements",
    "profile": "profile_pictures",
    "legal": "legal_documents"
}



async def create_user_directory(user_id: str):
    base_folder = f"user/{user_id}/"
    
    SUBFOLDERS = {
        "aadhar": "aadhar",
        "pan": "pan",
        "agreements": "agreements",
        "profile_pictures": "profile_pictures",
        "legal_documents": "legal_documents"
    }

    results = {}

    for key, subfolder in SUBFOLDERS.items():
        folder_path = f"{base_folder}{subfolder}/.keep"
        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=folder_path,
                Body=b"init",
                ACL="private"
            )
            results[subfolder] = {"status": "created", "path": folder_path}
        except ClientError as e:
            results[subfolder] = {"status": "error", "error": str(e)}

    return results
from fastapi import UploadFile
import boto3
from botocore.exceptions import ClientError
from config import settings

CATEGORY_FOLDER_MAP = {
    "aadhaar": "aadhar",
    "pan": "pan",
    "agreements": "agreements",
    "profile_photo": "profile_pictures",
    "legal": "legal_documents"
}

s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

S3_BUCKET = settings.S3_BUCKET_NAME
async def upload_documents(file: dict, category: str,user_id) -> dict:
   
    folder_name = CATEGORY_FOLDER_MAP.get(category.lower())
    if not folder_name:
        return {"error": f"Invalid category '{category}'"}

    folder_path = f"user/{user_id}/{folder_name}/"
    object_key = folder_path + folder_name  # ✅ Corrected here

    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=object_key,
            Body=file["bytes"],  # ✅ use the content
            ACL="private",
            ContentType="application/octet-stream"  # or pass dynamic content type
        )

 
        return {
            "success": True,
            "file_path": object_key,
   
        }

    except ClientError as e:
        return {"error": str(e)}

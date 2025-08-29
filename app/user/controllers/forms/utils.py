import os
import aioboto3
from config import settings
from typing import Dict, Union
from botocore.exceptions import ClientError
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from datetime import datetime
import uuid
from fastapi import HTTPException
import time
# Config values
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_REGION = settings.AWS_REGION
S3_BUCKET = settings.S3_BUCKET_NAME
DISTRIBUTION_ID = settings.DISTRIBUTION_ID
CLOUDFRONT_URL=settings.CLOUDFRONT_URL


CATEGORY_FOLDER_MAP = {
    "aadhaar": "aadhar",
    "pan": "pan",
    "agreements": "agreements",
    "profile_photo": "profile_photo",
    "legal": "legal_documents",

}


# Reusable S3 session
session = aioboto3.Session()


async def invalidate_files(paths: list[str]):
    try:
        # Ensure all paths start with a leading '/'
        paths = [p if p.startswith('/') else f'/{p}' for p in paths]

        async with session.client("cloudfront") as client:
            response = await client.create_invalidation(
                DistributionId=DISTRIBUTION_ID,
                InvalidationBatch={
                    "Paths": {"Quantity": len(paths), "Items": paths},
                    "CallerReference": str(datetime.now().timestamp()),
                },
            )
            return response["Invalidation"]
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))

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

async def create_property_directory(property_id: str) -> Dict[str, Dict[str, str]]:
    base_folder = f"property/{property_id}/"
    results = {}
    async with session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        for key, subfolder in PROPERTY_FOLDER_MAP.items():
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
    print(object_key)
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
            await invalidate_files([object_key])

            return {
                "success": True,
                "file_path": object_key,
                "content_type": "image/png"
            }
        except ClientError as e:
            return {"error": str(e)}

PROPERTY_FOLDER_MAP = {
    "property_photos":"property_photos",
    "monthly_photos":"monthly_photos",
    "legal_documents":"legal_documents",
    "property_photo":"property_photo"
}


async def property_upload_image_as_png(file: dict, category: str, property_id: Union[str, int]) -> dict:
    folder_name = PROPERTY_FOLDER_MAP.get(category.lower())
    if not folder_name:
        return {"error": f"Invalid category '{category}'"}
    if category=="property_photo":
        object_key = f"property/{property_id}/legal_documents/{category}.png"
    else:
        object_key = f"property/{property_id}/{folder_name}/{uuid.uuid4()}.png"
    print(object_key)
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
            await invalidate_files([object_key])

            return {
                "success": True,
                "file_path": object_key,
                "content_type": "image/png"
            }
        except ClientError as e:
            return {"error": str(e)}


async def property_upload_documents(file: dict, category: str, property_id: Union[str, int]) -> dict:
    folder_name = category.lower()
    if not folder_name:
        return {"error": f"Invalid category '{category}'"}

    file_name = file.get("filename", "uploaded_file")
    name, ext = os.path.splitext(file_name)
    
    object_key = f"property/{property_id}/legal_documents/{category}{ext}"

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

def get_image(filename: str) -> str:
    return f"{CLOUDFRONT_URL}{filename}?v={int(time.time())}"


async def list_s3_objects(bucket_name=S3_BUCKET, prefix=None):
    async with session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        paginator = s3.get_paginator("list_objects_v2")
        page_iterator = (
            paginator.paginate(Bucket=bucket_name, Prefix=prefix)
            if prefix else paginator.paginate(Bucket=bucket_name)
        )
        
        keys = []
        async for page in page_iterator:
            # print(page)
            if "Contents" in page:
                for obj in page["Contents"]:
                    key = obj["Key"]
                    # skip unwanted files
                    if key.endswith(".keep"):
                        continue
                    keys.append(key)
        return keys  # apply limit after filtering

async def check_object_exists( object_key: str,bucket_name: str=S3_BUCKET) -> bool:
    async with session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        try:
            await s3.head_object(Bucket=bucket_name, Key=object_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise
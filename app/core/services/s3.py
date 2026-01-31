# app/core/aws_service.py
"""
Consolidated AWS helpers (S3 + CloudFront) for uploads, downloads, deletes and signing.

- Single aioboto3 Session
- Reusable upload/delete/list helpers
- Image conversion utility (PIL)
- PDF validation (PyMuPDF)
- CloudFront signed URL generation with cache-busting included BEFORE signing
- invalidate_files() kept but NOT called automatically by upload functions (cheaper)

Note: keep PRIVATE_KEY_PATH, CLOUDFRONT_KEY_PAIR_ID, CLOUDFRONT_DOMAIN in your config.
"""

import os
import time
import uuid
import base64
import json
from typing import Any, Dict, List, Optional, Union

import aioboto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from datetime import datetime

# crypto for CloudFront signing
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# pdf validation
import fitz  # PyMuPDF

from config import settings
from app.core.services.redis import REDIS_EXPIRE_TIME  # keep your constant import

# -----------------------
# Configuration (from settings)
# -----------------------
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_REGION = settings.AWS_REGION
S3_BUCKET = settings.S3_BUCKET_NAME
DISTRIBUTION_ID = settings.DISTRIBUTION_ID
CLOUDFRONT_DOMAIN = settings.CLOUDFRONT_URL  # e.g. https://d123.cloudfront.net
CLOUDFRONT_KEY_PAIR_ID = settings.CLOUDFRONT_KEY_PAIR_ID
PRIVATE_KEY_PATH = settings.PRIVATE_KEY_PATH

# Allowed file constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}

# Folder maps
CATEGORY_FOLDER_MAP = {
    "aadhaar": "aadhaar",
    "pan": "pan",
    "agreements": "agreements",
    "profile_photo": "profile_photo",
    "legal": "legal_documents",
}

PROPERTY_FOLDER_MAP = {
    "property_photos": "property_photos",
    "monthly_photos": "monthly_photos",
    "legal_documents": "legal_documents",
    "property_photo": "property_photo",
}


legal_documents={
    "link_documents":"link_documents",
    "encumbrance_certificate":"encumbrance_certificate",
    "patta_title_deed":"patta_title_deed",
    "mutation_order":"mutation_order",
    "layout_approval":"layout_approval",
    "tax_receipt":"tax_receipt",
    "agreement_of_sale":"agreement_of_sale",
    "bank_noc":"bank_noc",
    "property_photo": "property_photo"

}

# Single aioboto3 session
_session = aioboto3.Session()


# -----------------------
# Utilities
# -----------------------
def _read_private_key() -> bytes:
    """Read private key bytes once; raise clear error if missing."""
    if not PRIVATE_KEY_PATH or not os.path.exists(PRIVATE_KEY_PATH):
        raise RuntimeError("CloudFront PRIVATE_KEY_PATH is missing or file not found.")
    with open(PRIVATE_KEY_PATH, "rb") as f:
        return f.read()


# load private key (RSA)
_private_key = serialization.load_pem_private_key(_read_private_key(), password=None)


def _url_safe_b64(s: bytes) -> str:
    """CloudFront expects URL-safe base64 with custom replacements."""
    return base64.b64encode(s).decode("utf-8").replace("+", "-").replace("=", "_").replace("/", "~")


# -----------------------
# CloudFront: policy signing & URL generation
# -----------------------
def _sign_policy(policy_bytes: bytes) -> str:
    """
    Sign the policy using RSA-SHA1 (CloudFront legacy required format).
    Note: CloudFront supports the SHA1 signature format for key-pair signed URLs.
    """
    signature = _private_key.sign(policy_bytes, padding.PKCS1v15(), hashes.SHA1())
    return _url_safe_b64(signature)


async def generate_cloudfront_presigned_url(resource_key: str, expires_in: int = 300, include_cache_buster: bool = True) -> str:
    """
    Generate a CloudFront signed URL for the given resource_key (path inside distribution).
    IMPORTANT: if include_cache_buster=True, the cache buster (?v=...) is INCLUDED in the signed resource URL,
    so the signature is valid for that exact cache-busted URL.
    """
    # Normalize key
    resource_key = resource_key.lstrip("/")

    ts_now = int(time.time())
    expires = ts_now + int(expires_in)

    # include cache buster directly into resource url path BEFORE signing — correct approach
    resource_url = f"{CLOUDFRONT_DOMAIN}/{resource_key}"
    if include_cache_buster:
        resource_url = f"{resource_url}?v={ts_now}"

    # Build policy JSON (simple expires-only policy)
    policy = json.dumps({
        "Statement": [
            {
                "Resource": resource_url,
                "Condition": {"DateLessThan": {"AWS:EpochTime": expires}}
            }
        ]
    }, separators=(",", ":"))  # compact

    signature = _sign_policy(policy.encode("utf-8"))

    # Append query params. Note: we already added ?v=... if include_cache_buster True -> need to append & for next params
    connector = "&" if "?" in resource_url else "?"
    signed_url = f"{resource_url}{connector}Expires={expires}&Signature={signature}&Key-Pair-Id={CLOUDFRONT_KEY_PAIR_ID}"
    return signed_url

import aiohttp

async def url_is_200(url: str, timeout: int = 3) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=timeout, allow_redirects=True) as resp:
                return resp.status == 200
    except Exception:
        return False

DEFAULT_IMG_URL = "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1075&q=80"



async def get_image_cloudfront_signed_url(
    filename: str | None,
    expires_in: int = 300,
    include_cache_buster: bool = True
) -> str:
    if not filename:
        return DEFAULT_IMG_URL

    key = filename.lstrip("/")

    signed_url = await generate_cloudfront_presigned_url(
        key,
        expires_in=expires_in,
        include_cache_buster=include_cache_buster
    )

    # 🔍 TEST IT
    if await _s3_head_object(signed_url):
        return signed_url

    return DEFAULT_IMG_URL



# -----------------------
# Optional CloudFront invalidation helper (kept but not auto-used)
# -----------------------
async def invalidate_files(paths: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Create CloudFront invalidation for given path(s).
    paths may be single string or list of strings. Paths should be like '/property/123/..png'.
    Note: invalidations can be slow and cost if you exceed free tier — prefer cache-busting.
    """
    try:
        if isinstance(paths, str):
            paths = [paths]
        # ensure list of strings and start with '/'
        paths = [p if p.startswith("/") else f"/{p}" for p in map(str, paths)]

        async with _session.client("cloudfront",
                                   aws_access_key_id=AWS_ACCESS_KEY_ID,
                                   aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                   region_name=AWS_REGION) as client:
            response = await client.create_invalidation(
                DistributionId=DISTRIBUTION_ID,
                InvalidationBatch={
                    "Paths": {"Quantity": len(paths), "Items": paths},
                    "CallerReference": str(datetime.now().timestamp())
                }
            )
            return response.get("Invalidation", {})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"CloudFront invalidation failed: {exc}")


# -----------------------
# S3 low-level helpers
# -----------------------
async def _s3_put_object(key: str, body: bytes, content_type: str = "application/octet-stream") -> None:
    async with _session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        try:
            await s3.put_object(Bucket=S3_BUCKET, Key=key, Body=body, ACL="private", ContentType=content_type)
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"S3 put_object failed: {e}")


async def _s3_delete_object(key: str) -> None:
    async with _session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        try:
            await s3.delete_object(Bucket=S3_BUCKET, Key=key)
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"S3 delete_object failed: {e}")


async def _s3_head_object(key: str) -> bool:
    async with _session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        try:
            await s3.head_object(Bucket=S3_BUCKET, Key=key)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NotFound"):
                return False
            raise


async def generate_s3_presigned_url(key: str, expires_in: int = REDIS_EXPIRE_TIME) -> str:
    """
    Generate a pre-signed S3 URL (not CloudFront). Useful when you want direct S3 access.
    """
    async with _session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        try:
            # botocore's generate_presigned_url is usually synchronous; aioboto3 proxies allow this usage
            url = await s3.generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=expires_in)
            return url
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate S3 presigned URL: {e}")


# -----------------------
# Image helpers
# -----------------------
def _convert_bytes_to_png_buffer(file_bytes: bytes) -> BytesIO:
    """
    Convert given bytes (jpg/png/whatever PIL supports) into PNG bytes buffer.
    Raises HTTPException on invalid image.
    """
    try:
        img = Image.open(BytesIO(file_bytes)).convert("RGB")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image conversion error: {e}")


# -----------------------
# File validators
# -----------------------
def _validate_extension_and_size(filename: str, file_bytes: bytes) -> str:
    _, ext = os.path.splitext(filename or "")
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max {MAX_FILE_SIZE} bytes allowed.")
    return ext


def _detect_mime_type(filename: str, provided_mime: Optional[str]) -> str:
    _, ext = os.path.splitext(filename or "")
    ext = ext.lower()
    if provided_mime and provided_mime.lower() in ALLOWED_MIME_TYPES:
        return provided_mime.lower()
    # fallback by extension
    if ext == ".pdf":
        return "application/pdf"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    return "application/octet-stream"


def _validate_pdf_bytes(file_bytes: bytes) -> None:
    try:
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        if pdf.page_count == 0:
            raise HTTPException(status_code=400, detail="Invalid or empty PDF.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Corrupted or unsafe PDF file.")


# -----------------------
# High-level upload / document functions (clean & de-duplicated)
# -----------------------
async def create_user_directory(user_id: Union[str, int]) -> Dict[str, Dict[str, str]]:
    """Create minimal .keep objects for user folders."""
    base = f"user/{user_id}/"
    results: Dict[str, Dict[str, str]] = {}
    async with _session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        for alias, folder in CATEGORY_FOLDER_MAP.items():
            key = f"{base}{folder}/.keep"
            try:
                await s3.put_object(Bucket=S3_BUCKET, Key=key, Body=b"init", ACL="private")
                results[folder] = {"status": "created", "path": key}
            except ClientError as e:
                results[folder] = {"status": "error", "error": str(e)}
    return results


async def create_property_directory(property_id: Union[str, int]) -> Dict[str, Dict[str, str]]:
    """Create minimal .keep objects for property folders."""
    base = f"property/{property_id}/"
    results: Dict[str, Dict[str, str]] = {}
    async with _session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        for folder in PROPERTY_FOLDER_MAP.values():
            key = f"{base}{folder}/.keep"
            try:
                await s3.put_object(Bucket=S3_BUCKET, Key=key, Body=b"init", ACL="private")
                results[folder] = {"status": "created", "path": key}
            except ClientError as e:
                results[folder] = {"status": "error", "error": str(e)}
    return results


async def upload_documents(file: dict, category: str, user_id: Union[str, int]) -> dict:
    """
    Upload arbitrary document (pdf/images) for user categories.
    file: {"filename": str, "bytes": b"...", "content_type": "..." }
    """
    folder = CATEGORY_FOLDER_MAP.get(category.lower())
    if not folder:
        raise HTTPException(status_code=400, detail=f"Invalid category '{category}'")

    filename = file.get("filename", "uploaded_file")
    ext = os.path.splitext(filename)[1].lower()
    # basic validation
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
    if len(file["bytes"]) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    key = f"user/{user_id}/{folder}/{category}{ext}"
    content_type = file.get("content_type") or _detect_mime_type(filename, None)

    await _s3_put_object(key=key, body=file["bytes"], content_type=content_type)
    # NOTE: Do not invalidate CloudFront here. Prefer cache-busting at URL generation.
    return {"success": True, "file_path": key}


async def upload_image_as_png(file: dict, category: str, user_id: Union[str, int]) -> dict:
    """
    Convert image to PNG and upload for given user/category.
    Returns the S3 key (not signed URL).
    """
    folder = CATEGORY_FOLDER_MAP.get(category.lower())
    if not folder:
        raise HTTPException(status_code=400, detail=f"Invalid category '{category}'")
    filename = file.get("filename", f"{category}.png")
    # convert and validate
    buf = _convert_bytes_to_png_buffer(file["bytes"])
    key = f"user/{user_id}/{folder}/{category}.png"
    await _s3_put_object(key=key, body=buf.read(), content_type="image/png")
    return {"success": True, "file_path": key, "content_type": "image/png"}


async def upload_feedback_image_as_png(file: dict, feedback_id: Union[int, str]) -> dict:
    """Upload feedback image as png; unique filename is feedbacks/<id>.png"""
    buf = _convert_bytes_to_png_buffer(file["bytes"])
    key = f"feedbacks/{feedback_id}.png"
    await _s3_put_object(key=key, body=buf.read(), content_type="image/png")
    return {"success": True, "file_path": key, "content_type": "image/png"}


async def property_upload_image_as_png(file: dict, category: str, property_id: Union[int, str]) -> dict:
    """
    Upload property image as PNG. If category == 'property_photo' we keep a fixed name under legal_documents,
    otherwise we use a uuid filename in the folder.
    """
    folder = PROPERTY_FOLDER_MAP.get(category.lower())
    if not folder:
        raise HTTPException(status_code=400, detail=f"Invalid category '{category}'")

    buf = _convert_bytes_to_png_buffer(file["bytes"])
    if category == "property_photo":
        key = f"property/{property_id}/legal_documents/{category}.png"
    else:
        key = f"property/{property_id}/{folder}/{uuid.uuid4()}.png"

    await _s3_put_object(key=key, body=buf.read(), content_type="image/png")
    return {"success": True, "file_path": key, "content_type": "image/png"}


async def property_upload_documents(file: dict, category: str, property_id: Union[str, int]) -> dict:
    """
    Validates and uploads property documents (pdf, images). Returns the S3 key.
    """
    filename = file.get("filename", "uploaded_file")
    ext = _validate_extension_and_size(filename, file["bytes"])
    mime = _detect_mime_type(filename, file.get("content_type"))

    if mime == "application/pdf":
        _validate_pdf_bytes(file["bytes"])

    key = f"property/{property_id}/legal_documents/{category}{ext}"
    await _s3_put_object(key=key, body=file["bytes"], content_type=mime)
    return {"success": True, "file_path": key, "mime_type": mime}


# -----------------------
# Listing / existence / delete helpers
# -----------------------
async def list_s3_objects(bucket_name: str = S3_BUCKET, prefix: Optional[str] = None) -> List[str]:
    keys: List[str] = []
    async with _session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        paginator = s3.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix) if prefix else paginator.paginate(Bucket=bucket_name)
        async for page in page_iterator:
            for obj in page.get("Contents", []):
                k = obj.get("Key")
                if k and not k.endswith(".keep"):
                    keys.append(k)
    return keys


async def check_object_exists(object_key: str, bucket_name: str = S3_BUCKET) -> bool:
    return await _s3_head_object(object_key)


async def property_delete_document(category: str, property_id: Union[str, int]) -> dict:
    prefix = f"property/{property_id}/legal_documents/{category}"
    async with _session.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ) as s3:
        try:
            response = await s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
            if "Contents" not in response:
                return {"error": f"No document found for category '{category}'"}
            deleted = []
            for obj in response["Contents"]:
                key = obj["Key"]
                await s3.delete_object(Bucket=S3_BUCKET, Key=key)
                # optionally invalidate: await invalidate_files([f"/{key}"])
                deleted.append(key)
            return {"success": True, "deleted_files": deleted}
        except ClientError as e:
            raise HTTPException(status_code=500, detail=str(e))


async def property_delete_single_document(category: str, property_id: Union[str, int], filename: str) -> dict:
    if category == "property_photos":
        key = f"property/{property_id}/{category}/{filename}"
    else:
        key = f"property/{property_id}/legal_documents/{category}/{filename}"
    # check & delete
    exists = await _s3_head_object(key)
    if not exists:
        return {"error": f"File '{filename}' not found in category '{category}'"}
    await _s3_delete_object(key)
    # optionally invalidate: await invalidate_files([f"/{key}"])
    return {"success": True, "deleted_file": key}


# -----------------------
# Final convenience: get signed URL for object
# -----------------------
async def get_signed_image_url(key: str, use_cloudfront: bool = True, expires_in: int = 300) -> str:
    """
    Returns a URL to access the given object:
    - If use_cloudfront=True -> CloudFront signed URL (with cache-buster included)
    - Else -> S3 presigned URL
    """
    if use_cloudfront:
        return await get_image_cloudfront_signed_url(key, expires_in=expires_in, include_cache_buster=True)
    return await generate_s3_presigned_url(key, expires_in=expires_in)

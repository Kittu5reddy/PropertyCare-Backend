import boto3
import os

# Set up S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

S3_BUCKET = os.getenv("S3_BUCKET_NAME")

async def create_user_directory(user_id: str):
    base_folder = f"user/{user_id}/"

    SUBFOLDERS = {
        "aadhar": "aadhar",
        "pan": "pan",
        "agreements": "agreements",
        "profile_pictures": "profile_pictures",
        "legal_documents": "legal_documents",
    }

    results = {}

    for key, subfolder in SUBFOLDERS.items():
        folder_path = f"{base_folder}{subfolder}/.keep"

        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=folder_path,
                Body=b"",  # empty file
                ACL="private"
            )
            results[subfolder] = {"status": "created", "path": folder_path}
        except Exception as e:
            results[subfolder] = {"status": "error", "error": str(e)}

    return results
import asyncio

async def main():
    c = await create_user_directory(2222)
    print(c)

if __name__ == "__main__":
    asyncio.run(main())
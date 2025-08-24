import boto3
import os
import dotenv
dotenv.load_dotenv()

def list_s3_objects(bucket_name, prefix=None):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix) if prefix else paginator.paginate(Bucket=bucket_name)
    
    keys = []
    for page in page_iterator:
        if "Contents" in page:
            for obj in page["Contents"]:
                keys.append(obj["Key"])
    
    return keys

bucket_name = "propcare-demos"
folder_prefix = "user/PC2025U001/profile_photo/"
total = list_s3_objects(bucket_name, folder_prefix)
print(f"Total objects in '{folder_prefix}' = {total}")

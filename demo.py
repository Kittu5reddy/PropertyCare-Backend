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
import boto3
from botocore.client import Config

s3 = boto3.client("s3", region_name="ap-south-1")

url = s3.generate_presigned_url(
    ClientMethod="get_object",
    Params={"Bucket": "propcare", "Key": "yourfile.jpg"},
    ExpiresIn=3600,
)
print(url)


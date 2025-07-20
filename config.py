import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# load_dotenv('.env.dev')

class Settings(BaseSettings):
    # JWT
    REFRESH_TOKEN_SECRET_KEY: str
    ACCESS_TOKEN_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # File Config
    BASE_DOCUMENT_PATH: str
    MAX_SIZE_PDF: int
    MAX_SIZE_IMAGE: int
    MAX_SIZE_VIDEO: int


    SUBFOLDERS: dict[str, str] = {
    "aadhaar": "aadhar",
    "pan": "pan",
    "agreements": "agreements",
    "profile_photo": "profile_photo",
    "legal": "legal_documents"
    }

    # Database
    HOST_NAME: str
    DATABASE_NAME: str
    USERNAME: str
    PASSWORD: str
    PORT_ID: int
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_TIME_OUT: int = 30
    DATABASE_URL: str  # ✅ Add this line
    # Email
    SMTP_SERVER: str
    SMTP_PORT: int
    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str
    EMAIL_URL: str
    EMAIL_TOKEN_VERIFICATION:str

    AWS_ACCESS_KEY_ID:str
    AWS_SECRET_ACCESS_KEY:str
    AWS_REGION:str
    S3_BUCKET_NAME:str
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

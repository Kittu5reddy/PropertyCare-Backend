import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    ALLOWED_PDF_EXTENSIONS: List[str]
    ALLOWED_IMAGE_EXTENSIONS: List[str]
    ALLOWED_VIDEO_EXTENSIONS: List[str]
    SUBFOLDERS: dict[str, str] = {
        "aadhar": "aadhar",
        "pan": "pan",
        "agreements": "agreements",
        "profile_pics": "profile_pictures",
        "legal_documents": "legal_documents"
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


    
    IMAGE_KIT_PRIVATE_KEY:str
    IMAGE_KIT_PUBLIC_KEY:str
    IMAGE_URL_END_POINT:str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

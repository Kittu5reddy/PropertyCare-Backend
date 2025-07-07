import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pydantic import  Field

# Load the correct .env file
env = os.getenv("ENV", "dev")
load_dotenv(f".env.{env}")
load_dotenv()

class Settings(BaseSettings):
    # JWT
    REFRESH_TOKEN_SECRET_KEY: str
    ACCESS_TOKEN_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ALLOWED_PDF_EXTENSIONS: List[str] = Field(default_factory=list)
    ALLOWED_IMAGE_EXTENSIONS: List[str] = Field(default_factory=list)
    ALLOWED_VIDEO_EXTENSIONS: List[str] = Field(default_factory=list)
    # File Config
    BASE_DOCUMENT_PATH: str
    MAX_SIZE_PDF: int
    MAX_SIZE_IMAGE: int
    MAX_SIZE_VIDEO: int

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


    class Config:
        env_file = f".env.{env}"
        case_sensitive = True

settings = Settings()

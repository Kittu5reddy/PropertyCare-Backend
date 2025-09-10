import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
#make it uncomment in production and comment in developement
# load_dotenv('.env.prod')
load_dotenv('.env')

class Settings(BaseSettings):





    # ==================================
    #  J W T AUTH KEYS
    # ==================================   
    REFRESH_TOKEN_SECRET_KEY: str
    ACCESS_TOKEN_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN: int
    REFRESH_TOKEN_EXPIRE_DAYS_ADMIN: int
    REFRESH_TOKEN_EXPIRE_DAYS: int



    
    # ==================================
    #  F I L E  S I Z E 
    # ==================================   
    BASE_DOCUMENT_PATH: str
    MAX_SIZE_PDF: int
    MAX_SIZE_IMAGE: int
    MAX_SIZE_VIDEO: int


    # ==================================
    #  S U B F O L D E R S
    # ==================================   
    SUBFOLDERS: dict[str, str] = {
    "aadhaar": "aadhar",
    "pan": "pan",
    "agreements": "agreements",
    "profile_photo": "profile_photo",
    "legal": "legal_documents",
    "properties":"properties",
    }





    # ==================================
    #  P O S T G R E S  D A T A B A S E
    # ==================================   
    HOST_NAME: str
    SCHEMA:str
    DATABASE_NAME: str
    USERNAME: str
    PASSWORD: str
    PORT_ID: int
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_TIME_OUT: int = 30
    DATABASE_URL: str  


    # ================================
    #        R E D I S
    # ================================
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_POOL_SIZE: int = 50          
    REDIS_POOL_TIMEOUT: int = 10       
    REDIS_EXPIRE_TIME: int = 300       
    REDIS_URL: str






    # ==================================
    #          E M A I L
    # ==================================   
    SMTP_SERVER: str
    SMTP_PORT: int
    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str
    EMAIL_URL: str
    EMAIL_TOKEN_VERIFICATION:str







    # ==================================
    #          A W S
    # ==================================
    AWS_ACCESS_KEY_ID:str
    AWS_SECRET_ACCESS_KEY:str
    AWS_REGION:str
    S3_BUCKET_NAME:str
    DISTRIBUTION_ID:str
    CLOUDFRONT_URL:str



    # ==================================
    #         I M A G E S 
    # ==================================
    DEFAULT_IMG_URL:str




    # MONTH={}

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

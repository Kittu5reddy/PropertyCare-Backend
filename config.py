from datetime import datetime
class JWT:
    REFRESH_TOKEN_SECRET_KEY = "your-secret-key-change-this-in-production"
    ACCES_TOKEN_SECRET_KEY = "your-secret-key-change-this-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1
    REFRESH_TOKEN_EXPIRE_DAYS = 7

class File(JWT):
    # Base path where all user folders will be created
    BASE_DOCUMENT_PATH = "user_documents"  # You can also use absolute path like "/var/data/user_documents"

    # Maximum allowed sizes
    MAX_SIZE_PDF = 5 * 1024 * 1024        # 5 MB
    MAX_SIZE_IMAGE = 2 * 1024 * 1024      # 2 MB
    MAX_SIZE_VIDEO = 50 * 1024 * 1024     # 50 MB

    # Allowed file extensions
    ALLOWED_PDF_EXTENSIONS = [".pdf"]
    ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif"]
    ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv"]

    # Subfolders inside each user directory
    SUBFOLDERS = {
        "aadhar": "aadhar",
        "pan": "pan",
        "agreements": "agreements",
        "profile_pics": "profile_pictures",
        "legal_documents":"legal_documents"
    }



class Database(File):
    HOST_NAME = "localhost"
    DATABASE_NAME = "PropCare"
    USERNAME = "postgres"
    PASSWORD = "Palvai2004@"
    PORT_ID = 5432
    # Encode special characters in pasword if necessary
    ENCODED_PASSWORD = PASSWORD.replace("@", "%40")  # If '@' is present
    DATABASE_URL = (
        f"postgresql+asyncpg://{USERNAME}:{ENCODED_PASSWORD}"
        f"@{HOST_NAME}:{PORT_ID}/{DATABASE_NAME}"
    )
    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_TIME_OUT = 30

class Email(Database):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = "kaushikpalvai2004@gmail.com"
    EMAIL_PASSWORD = "qtca zitr naez ilip"




class Config(Email):
    pass
class JWT:
    REFRESH_TOKEN_SECRET_KEY= "your-secret-key-change-this-in-production"
    ACCES_TOKEN_SECRET_KEY = "your-secret-key-change-this-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_MINUTES = 7

class Config(JWT):
    pass

print(Config.ALGORITHM)
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from redis.exceptions import RedisError
from jose import JWTError, ExpiredSignatureError
from typing import Optional, Any, Dict, Union
from botocore.exceptions import (
    ClientError, BotoCoreError, ConnectionError as BotoConnectionError,
    HTTPClientError, ParamValidationError, WaiterError
)

class AppException(HTTPException):
    """Base exception class for application-specific exceptions"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)

class ValidationError(AppException):
    """Raised when input validation fails"""
    def __init__(self, message: str):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)

class AuthenticationError(AppException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)

class AuthorizationError(AppException):
    """Raised when authorization fails"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)

class ResourceNotFoundError(AppException):
    """Raised when a requested resource is not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)

class DatabaseError(AppException):
    """Raised when database operations fail"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CacheError(AppException):
    """Raised when cache operations fail"""
    def __init__(self, message: str = "Cache operation failed"):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FileOperationError(AppException):
    """Raised when file operations fail"""
    def __init__(self, message: str = "File operation failed"):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class S3OperationError(AppException):
    """Raised when S3 operations fail"""
    def __init__(self, message: str = "S3 operation failed"):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY)

class S3ConnectionError(AppException):
    """Raised when there are connection issues with S3"""
    def __init__(self, message: str = "Could not connect to S3"):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

class S3ValidationError(AppException):
    """Raised when S3 input validation fails"""
    def __init__(self, message: str = "Invalid S3 parameters"):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)

class S3ClientError(AppException):
    """Raised when there's a client-side error with S3 operations"""
    def __init__(self, message: str = "S3 client error"):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)
async def handle_exception(error: Exception, db=None):
    """
    Centralized exception handler that raises appropriate HTTPExceptions
    """

    if isinstance(error, AppException):
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
            headers=error.headers
        )

    # SQLAlchemy errors
    if isinstance(error, IntegrityError):
        if db:
            await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error. Please check your input."
        )

    if isinstance(error, SQLAlchemyError):
        if db:
            await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )

    # Redis errors
    if isinstance(error, RedisError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache operation failed. Please try again later."
        )

    # JWT errors
    if isinstance(error, ExpiredSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )

    if isinstance(error, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # AWS S3 errors
    if isinstance(error, ParamValidationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid S3 parameters. Please check your input."
        )

    if isinstance(error, BotoConnectionError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to S3. Please try again later."
        )

    if isinstance(error, HTTPClientError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="S3 HTTP client error"
        )

    if isinstance(error, WaiterError):
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout while waiting for S3 operation"
        )

    if isinstance(error, ClientError):
        error_code = error.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="S3 bucket not found"
            )
        elif error_code == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="S3 file not found"
            )
        elif error_code in ["AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="S3 authentication error"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"S3 error: {error_code}"
            )

    if isinstance(error, BotoCoreError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="S3 operation failed"
        )

    # Fallback
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred. Please try again later."
    )

# Example usage:
"""
@router.post("/example")
async def example_endpoint(data: SomeSchema, db: AsyncSession = Depends(get_db)):
    try:
        if not validate_data(data):
            raise ValidationError("Invalid input data")
            
        result = await process_data(data)
        if not result:
            raise ResourceNotFoundError("Data not found")
            
        return {"message": "Success", "data": result}
        
    except Exception as e:
        return await handle_exception(e, db)
"""
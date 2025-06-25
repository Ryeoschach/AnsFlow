"""
Authentication dependencies and utilities
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import structlog

from ..config.settings import settings
from ..models.schemas import UserSchema

logger = structlog.get_logger(__name__)

security = HTTPBearer()


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt.access_token_expire_hours)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt.secret_key, 
        algorithm=settings.jwt.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify JWT token and return payload
    """
    try:
        payload = jwt.decode(
            token, 
            settings.jwt.secret_key, 
            algorithms=[settings.jwt.algorithm]
        )
        return payload
    except JWTError as e:
        logger.warning("JWT verification failed", error=str(e))
        raise AuthenticationError("Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserSchema:
    """
    Get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # TODO: Implement user lookup from database
        # For now, return a mock user based on token payload
        user = UserSchema(
            id=user_id,
            username=payload.get("username", "unknown"),
            email=payload.get("email", "unknown@example.com"),
            is_active=True,
            is_superuser=payload.get("is_superuser", False)
        )
        
        return user
        
    except AuthenticationError:
        raise credentials_exception
    except Exception as e:
        logger.error("User authentication failed", error=str(e))
        raise credentials_exception


async def get_current_user_ws(token: str) -> Optional[UserSchema]:
    """
    Get current authenticated user from JWT token for WebSocket connections
    """
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # TODO: Implement user lookup from database
        # For now, return a mock user based on token payload
        user = UserSchema(
            id=user_id,
            username=payload.get("username", "unknown"),
            email=payload.get("email", "unknown@example.com"),
            is_active=True,
            is_superuser=payload.get("is_superuser", False)
        )
        
        return user
        
    except Exception as e:
        logger.warning("WebSocket authentication failed", error=str(e))
        return None


async def get_current_active_user(
    current_user: UserSchema = Depends(get_current_user)
) -> UserSchema:
    """
    Get current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: UserSchema = Depends(get_current_user)
) -> UserSchema:
    """
    Get current superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def verify_api_key(api_key: str) -> bool:
    """
    Verify API key for webhook endpoints
    """
    # TODO: Implement proper API key verification
    # For now, check against a simple configured key
    return api_key == settings.api.webhook_api_key


async def get_api_key_user(api_key: str) -> UserSchema:
    """
    Get user associated with API key
    """
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Return a system user for API key authentication
    return UserSchema(
        id="system",
        username="api_system",
        email="system@ansflow.local",
        is_active=True,
        is_superuser=True
    )

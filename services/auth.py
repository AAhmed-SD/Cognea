from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config.security import security_config
from services.supabase import get_supabase_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        minutes=security_config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, security_config.SECRET_KEY, algorithm=security_config.JWT_ALGORITHM
    )


def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token using Supabase Auth"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            security_config.SECRET_KEY,
            algorithms=[security_config.JWT_ALGORITHM],
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # Get user from Supabase public.users table
    supabase = get_supabase_client()
    result = supabase.table("users").select("*").eq("email", email).execute()

    if not result.data:
        raise credentials_exception

    user_data = result.data[0]

    # Create a simple user object for compatibility
    class User:
        def __init__(self, user_data):
            self.id = user_data["id"]
            self.email = user_data["email"]

    return User(user_data)

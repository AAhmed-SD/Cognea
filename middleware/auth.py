import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config import security as security_config
from services.supabase import get_supabase_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


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

    # Return user data as dict for compatibility with routes
    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "role": user_data.get("role", "user")
    }

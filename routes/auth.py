from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from services.supabase import get_supabase_client
from services.auth import create_access_token, hash_password, get_current_user
from services.email import send_password_reset_email
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, UTC
import secrets
from config.security import security_config, validate_password_strength
from typing import Dict, Any
import jwt

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Security scheme for JWT tokens
security = HTTPBearer()

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/signup", response_model=Dict[str, Any])
def signup(request: UserCreate):
    """Register a new user using Supabase Auth"""
    supabase = get_supabase_client()
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    try:
        # Create user using Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })
        
        if auth_response.user:
            # Create user profile in public.users table
            user_data = {
                "id": auth_response.user.id,
                "email": request.email
            }
            
            result = supabase.table("users").insert(user_data).execute()
            
            # Generate access token
            access_token = create_access_token({"sub": request.email})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {"id": auth_response.user.id, "email": request.email}
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
    except Exception as e:
        if "already registered" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.post("/login", response_model=dict)
def login(request: UserLogin):
    """Login user using Supabase Auth"""
    supabase = get_supabase_client()
    
    try:
        # Authenticate using Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if auth_response.user:
            access_token = create_access_token({"sub": auth_response.user.email})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {"id": auth_response.user.id, "email": auth_response.user.email}
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login using Supabase Auth"""
    supabase = get_supabase_client()
    
    try:
        # Authenticate using Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        if auth_response.user:
            access_token = create_access_token({"sub": auth_response.user.email})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {"id": auth_response.user.id, "email": auth_response.user.email}
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/me", response_model=dict)
def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return {"id": current_user.id, "email": current_user.email}

@router.post("/forgot-password", response_model=dict)
def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email using Supabase Auth"""
    supabase = get_supabase_client()
    
    try:
        # Use Supabase Auth password reset
        supabase.auth.reset_password_email(request.email)
        return {"message": "If an account exists for this email, you will receive a password reset email shortly."}
    except Exception as e:
        # Always return success to prevent email enumeration
        return {"message": "If an account exists for this email, you will receive a password reset email shortly."}

@router.post("/reset-password", response_model=dict)
def reset_password(request: ResetPasswordRequest):
    """Reset password using Supabase Auth"""
    supabase = get_supabase_client()
    
    try:
        # Validate new password strength
        is_valid, error_message = validate_password_strength(request.new_password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Use Supabase Auth to update password
        # Note: This would typically be done through a frontend flow with Supabase Auth
        # For now, we'll return a message indicating the user should use the email link
        return {"message": "Please use the password reset link sent to your email to complete the password reset."}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to reset password") 
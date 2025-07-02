"""
Enhanced authentication service with RBAC, password reset, and email verification
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from services.supabase import get_supabase_client
from services.email_service import email_service
from models.auth import (
    UserRole,
    Permission,
    UserCreate,
    UserLogin,
    UserUpdate,
    PasswordChange,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    EmailVerificationConfirm,
    AuditLogEntry,
    get_user_permissions,
    has_permission,
    can_manage_role,
)

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Enhanced authentication service with Role-Based Access Control (RBAC).

    This service handles all authentication and authorization operations including
    user registration, login, password management, email verification, and role-based
    permissions. It integrates with Supabase for data storage and JWT for token management.

    Features:
    - User registration and login
    - JWT token management (access and refresh tokens)
    - Password hashing and verification
    - Email verification system
    - Password reset functionality
    - Role-based access control
    - User management and permissions
    - Audit logging for security events
    """

    def __init__(self):
        """
        Initialize the authentication service.

        Sets up Supabase client, JWT configuration, and token expiry times.
        Environment variables are used for secure configuration.
        """
        self.supabase = get_supabase_client()
        # JWT secret key for token signing and verification
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")
        # Token expiry times for security
        self.access_token_expiry = timedelta(hours=1)  # Short-lived for security
        self.refresh_token_expiry = timedelta(days=30)  # Long-lived for convenience

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password (str): Plain text password to hash

        Returns:
            str: Hashed password string

        Security Note:
            Uses bcrypt with salt for secure password storage
        """
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against its hash.

        Args:
            plain_password (str): Plain text password to verify
            hashed_password (str): Stored password hash

        Returns:
            bool: True if password matches, False otherwise

        Security Note:
            Uses constant-time comparison to prevent timing attacks
        """
        return pwd_context.verify(plain_password, hashed_password)

    def _create_tokens(self, user_id: str, role: UserRole) -> Dict[str, str]:
        """
        Create JWT access and refresh tokens for a user.

        Args:
            user_id (str): Unique user identifier
            role (UserRole): User's role for authorization

        Returns:
            Dict[str, str]: Dictionary containing access_token and refresh_token

        Security Features:
            - Access tokens are short-lived (1 hour) for security
            - Refresh tokens are long-lived (30 days) for convenience
            - Tokens include user role for authorization
            - Different token types prevent token confusion attacks
        """
        # Access token payload with user info and role
        access_token_payload = {"user_id": user_id, "role": role, "type": "access"}

        # Refresh token payload (minimal for security)
        refresh_token_payload = {"user_id": user_id, "type": "refresh"}

        # Create access token with short expiry
        access_token = jwt.encode(
            access_token_payload,
            self.jwt_secret,
            algorithm="HS256",
            expires_in=int(self.access_token_expiry.total_seconds()),
        )

        # Create refresh token with long expiry
        refresh_token = jwt.encode(
            refresh_token_payload,
            self.jwt_secret,
            algorithm="HS256",
            expires_in=int(self.refresh_token_expiry.total_seconds()),
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

    def _verify_token(
        self, token: str, token_type: str = "access"
    ) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            if payload.get("type") != token_type:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    async def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = (
                self.supabase.table("users")
                .select("*")
                .eq("email", user_data.email)
                .execute()
            )
            if existing_user.data:
                raise ValueError("User with this email already exists")

            # Hash password
            hashed_password = self._hash_password(user_data.password)

            # Create user
            user_record = {
                "email": user_data.email,
                "password_hash": hashed_password,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "role": user_data.role,
                "is_email_verified": False,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = self.supabase.table("users").insert(user_record).execute()

            if not result.data:
                raise ValueError("Failed to create user")

            user = result.data[0]

            # Send email verification
            email_service.send_email_verification(
                user["id"], user["email"], user.get("first_name")
            )

            # Create tokens
            tokens = self._create_tokens(user["id"], user["role"])

            return {
                "user": user,
                "tokens": tokens,
                "message": "User registered successfully. Please check your email for verification.",
            }

        except Exception as e:
            logger.error(f"Failed to register user: {str(e)}")
            raise

    async def login_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """Login a user"""
        try:
            # Find user by email
            result = (
                self.supabase.table("users")
                .select("*")
                .eq("email", login_data.email)
                .execute()
            )

            if not result.data:
                raise ValueError("Invalid email or password")

            user = result.data[0]

            # Verify password
            if not self._verify_password(login_data.password, user["password_hash"]):
                raise ValueError("Invalid email or password")

            # Check if user is active
            if not user.get("is_active", True):
                raise ValueError("Account is deactivated")

            # Update last login
            self.supabase.table("users").update(
                {"last_login": datetime.utcnow().isoformat()}
            ).eq("id", user["id"]).execute()

            # Create tokens
            tokens = self._create_tokens(user["id"], user["role"])

            return {"user": user, "tokens": tokens}

        except Exception as e:
            logger.error(f"Failed to login user: {str(e)}")
            raise

    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = self._verify_token(refresh_token, "refresh")
            if not payload:
                raise ValueError("Invalid refresh token")

            user_id = payload.get("user_id")

            # Get user to check if still active
            result = (
                self.supabase.table("users")
                .select("id, role, is_active")
                .eq("id", user_id)
                .execute()
            )

            if not result.data:
                raise ValueError("User not found")

            user = result.data[0]

            if not user.get("is_active", True):
                raise ValueError("Account is deactivated")

            # Create new tokens
            tokens = self._create_tokens(user["id"], user["role"])

            return tokens

        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            raise

    async def change_password(
        self, user_id: str, password_data: PasswordChange
    ) -> bool:
        """Change user password"""
        try:
            # Get user
            result = (
                self.supabase.table("users")
                .select("password_hash")
                .eq("id", user_id)
                .execute()
            )

            if not result.data:
                raise ValueError("User not found")

            user = result.data[0]

            # Verify current password
            if not self._verify_password(
                password_data.current_password, user["password_hash"]
            ):
                raise ValueError("Current password is incorrect")

            # Hash new password
            new_password_hash = self._hash_password(password_data.new_password)

            # Update password
            self.supabase.table("users").update(
                {
                    "password_hash": new_password_hash,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", user_id).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to change password: {str(e)}")
            raise

    async def request_password_reset(self, reset_data: PasswordResetRequest) -> bool:
        """Request password reset"""
        try:
            # Find user by email
            result = (
                self.supabase.table("users")
                .select("id, email, first_name")
                .eq("email", reset_data.email)
                .execute()
            )

            if not result.data:
                # Don't reveal if user exists or not
                return True

            user = result.data[0]

            # Send password reset email
            success = email_service.send_password_reset_email(
                user["id"], user["email"], user.get("first_name")
            )

            return success

        except Exception as e:
            logger.error(f"Failed to request password reset: {str(e)}")
            return False

    async def reset_password(self, reset_data: PasswordResetConfirm) -> bool:
        """Reset password using token"""
        try:
            # Verify token
            user_id = email_service.verify_password_reset_token(reset_data.token)
            if not user_id:
                raise ValueError("Invalid or expired token")

            # Hash new password
            new_password_hash = self._hash_password(reset_data.new_password)

            # Update password
            self.supabase.table("users").update(
                {
                    "password_hash": new_password_hash,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", user_id).execute()

            # Invalidate token
            email_service.invalidate_token(reset_data.token)

            return True

        except Exception as e:
            logger.error(f"Failed to reset password: {str(e)}")
            raise

    async def request_email_verification(
        self, verification_data: EmailVerificationRequest
    ) -> bool:
        """Request email verification"""
        try:
            # Find user by email
            result = (
                self.supabase.table("users")
                .select("id, email, first_name, is_email_verified")
                .eq("email", verification_data.email)
                .execute()
            )

            if not result.data:
                return False

            user = result.data[0]

            if user.get("is_email_verified"):
                return True  # Already verified

            # Send verification email
            success = email_service.send_email_verification(
                user["id"], user["email"], user.get("first_name")
            )

            return success

        except Exception as e:
            logger.error(f"Failed to request email verification: {str(e)}")
            return False

    async def verify_email(self, verification_data: EmailVerificationConfirm) -> bool:
        """Verify email using token"""
        try:
            # Verify token
            user_id = email_service.verify_email_token(verification_data.token)
            if not user_id:
                raise ValueError("Invalid or expired token")

            # Update user
            self.supabase.table("users").update(
                {"is_email_verified": True, "updated_at": datetime.utcnow().isoformat()}
            ).eq("id", user_id).execute()

            # Invalidate token
            email_service.invalidate_token(verification_data.token)

            return True

        except Exception as e:
            logger.error(f"Failed to verify email: {str(e)}")
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            result = (
                self.supabase.table("users").select("*").eq("id", user_id).execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get user: {str(e)}")
            return None

    async def update_user(
        self, user_id: str, update_data: UserUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update user information"""
        try:
            update_fields = {}

            if update_data.first_name is not None:
                update_fields["first_name"] = update_data.first_name
            if update_data.last_name is not None:
                update_fields["last_name"] = update_data.last_name
            if update_data.email is not None:
                update_fields["email"] = update_data.email
            if update_data.role is not None:
                update_fields["role"] = update_data.role

            if not update_fields:
                return await self.get_user_by_id(user_id)

            update_fields["updated_at"] = datetime.utcnow().isoformat()

            result = (
                self.supabase.table("users")
                .update(update_fields)
                .eq("id", user_id)
                .execute()
            )

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Failed to update user: {str(e)}")
            return None

    async def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False

            user_role = user.get("role", UserRole.FREE_USER)
            return has_permission(user_role, permission)

        except Exception as e:
            logger.error(f"Failed to check permission: {str(e)}")
            return False

    async def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for a user"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return []

            user_role = user.get("role", UserRole.FREE_USER)
            return get_user_permissions(user_role)

        except Exception as e:
            logger.error(f"Failed to get user permissions: {str(e)}")
            return []

    async def assign_role(
        self, user_id: str, new_role: UserRole, assigned_by: str, reason: str = None
    ) -> bool:
        """Assign a role to a user (admin only)"""
        try:
            # Check if assigner has permission
            assigner = await self.get_user_by_id(assigned_by)
            if not assigner:
                return False

            assigner_role = assigner.get("role", UserRole.FREE_USER)
            if not can_manage_role(assigner_role, new_role):
                return False

            # Update user role
            self.supabase.table("users").update(
                {"role": new_role, "updated_at": datetime.utcnow().isoformat()}
            ).eq("id", user_id).execute()

            # Log role assignment
            audit_entry = AuditLogEntry(
                user_id=assigned_by,
                action="role_assignment",
                resource_type="user",
                resource_id=user_id,
                details={"assigned_role": new_role, "reason": reason},
            )

            self.supabase.table("audit_logs").insert(audit_entry.dict()).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to assign role: {str(e)}")
            return False

    async def get_users(
        self, current_user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get list of users (admin only)"""
        try:
            # Check if user has permission
            if not await self.check_permission(current_user_id, Permission.VIEW_USERS):
                return []

            result = (
                self.supabase.table("users")
                .select("*")
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            return []

    async def deactivate_user(
        self, user_id: str, deactivated_by: str, reason: str = None
    ) -> bool:
        """Deactivate a user (admin only)"""
        try:
            # Check if deactivator has permission
            if not await self.check_permission(deactivated_by, Permission.EDIT_USERS):
                return False

            # Update user
            self.supabase.table("users").update(
                {"is_active": False, "updated_at": datetime.utcnow().isoformat()}
            ).eq("id", user_id).execute()

            # Log deactivation
            audit_entry = AuditLogEntry(
                user_id=deactivated_by,
                action="user_deactivation",
                resource_type="user",
                resource_id=user_id,
                details={"reason": reason},
            )

            self.supabase.table("audit_logs").insert(audit_entry.dict()).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to deactivate user: {str(e)}")
            return False

    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        return email_service.cleanup_expired_tokens()


# Global auth service instance
auth_service = AuthService()

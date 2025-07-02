"""
Authentication and authorization models
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC"""

    FREE_USER = "free_user"
    PREMIUM_USER = "premium_user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Permission(str, Enum):
    """System permissions for RBAC"""

    # User management
    VIEW_USERS = "view_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"

    # Content management
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"
    VIEW_CONTENT = "view_content"

    # AI features
    USE_AI_FEATURES = "use_ai_features"
    USE_ADVANCED_AI = "use_advanced_ai"
    UNLIMITED_AI_CALLS = "unlimited_ai_calls"

    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"

    # System administration
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    MANAGE_BILLING = "manage_billing"


class RolePermission(BaseModel):
    """Role-permission mapping"""

    role: UserRole
    permissions: List[Permission]
    description: str


# Define role-permission mappings
ROLE_PERMISSIONS: Dict[UserRole, RolePermission] = {
    UserRole.FREE_USER: RolePermission(
        role=UserRole.FREE_USER,
        permissions=[
            Permission.CREATE_CONTENT,
            Permission.EDIT_CONTENT,
            Permission.VIEW_CONTENT,
            Permission.USE_AI_FEATURES,
        ],
        description="Basic user with limited AI features",
    ),
    UserRole.PREMIUM_USER: RolePermission(
        role=UserRole.PREMIUM_USER,
        permissions=[
            Permission.CREATE_CONTENT,
            Permission.EDIT_CONTENT,
            Permission.DELETE_CONTENT,
            Permission.VIEW_CONTENT,
            Permission.USE_AI_FEATURES,
            Permission.USE_ADVANCED_AI,
            Permission.VIEW_ANALYTICS,
            Permission.EXPORT_DATA,
        ],
        description="Premium user with advanced features",
    ),
    UserRole.ADMIN: RolePermission(
        role=UserRole.ADMIN,
        permissions=[
            Permission.VIEW_USERS,
            Permission.EDIT_USERS,
            Permission.CREATE_CONTENT,
            Permission.EDIT_CONTENT,
            Permission.DELETE_CONTENT,
            Permission.VIEW_CONTENT,
            Permission.USE_AI_FEATURES,
            Permission.USE_ADVANCED_AI,
            Permission.UNLIMITED_AI_CALLS,
            Permission.VIEW_ANALYTICS,
            Permission.EXPORT_DATA,
            Permission.VIEW_LOGS,
        ],
        description="Administrator with user management capabilities",
    ),
    UserRole.SUPER_ADMIN: RolePermission(
        role=UserRole.SUPER_ADMIN,
        permissions=[perm for perm in Permission],
        description="Super administrator with full system access",
    ),
}


class UserCreate(BaseModel):
    """User registration model"""

    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.FREE_USER

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """User login model"""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update model"""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None


class PasswordChange(BaseModel):
    """Password change model"""

    current_password: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request model"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""

    token: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request model"""

    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Email verification confirmation model"""

    token: str


class UserResponse(BaseModel):
    """User response model"""

    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole
    is_email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    permissions: List[Permission] = []


class TokenResponse(BaseModel):
    """Token response model"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""

    refresh_token: str


class PermissionCheck(BaseModel):
    """Permission check model"""

    permission: Permission
    resource_id: Optional[str] = None


class RoleAssignment(BaseModel):
    """Role assignment model"""

    user_id: str
    role: UserRole
    assigned_by: str
    reason: Optional[str] = None


class AuditLogEntry(BaseModel):
    """Audit log entry model"""

    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


def get_user_permissions(role: UserRole) -> List[Permission]:
    """Get permissions for a given role"""
    role_permission = ROLE_PERMISSIONS.get(role)
    return role_permission.permissions if role_permission else []


def has_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """Check if a user role has a specific permission"""
    user_permissions = get_user_permissions(user_role)
    return required_permission in user_permissions


def get_role_hierarchy() -> Dict[UserRole, int]:
    """Get role hierarchy levels (higher number = more privileges)"""
    return {
        UserRole.FREE_USER: 1,
        UserRole.PREMIUM_USER: 2,
        UserRole.ADMIN: 3,
        UserRole.SUPER_ADMIN: 4,
    }


def can_manage_role(manager_role: UserRole, target_role: UserRole) -> bool:
    """Check if a manager can assign/manage a target role"""
    hierarchy = get_role_hierarchy()
    return hierarchy.get(manager_role, 0) > hierarchy.get(target_role, 0)

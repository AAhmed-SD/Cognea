from datetime import datetime

import pytest
from pydantic import ValidationError

from models.auth import (
    ROLE_PERMISSIONS,
    AuditLogEntry,
    EmailVerificationConfirm,
    EmailVerificationRequest,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    Permission,
    PermissionCheck,
    RefreshTokenRequest,
    RoleAssignment,
    RolePermission,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
    UserUpdate,
    can_manage_role,
    get_role_hierarchy,
    get_user_permissions,
    has_permission,
)


def test_user_role_enum() -> None:
    assert UserRole.FREE_USER.value == "free_user"
    assert UserRole.SUPER_ADMIN.value == "super_admin"


def test_permission_enum() -> None:
    assert Permission.VIEW_USERS.value == "view_users"
    assert Permission.MANAGE_BILLING.value == "manage_billing"


def test_role_permission_model() -> None:
    rp = RolePermission(
        role=UserRole.ADMIN, permissions=[Permission.VIEW_USERS], description="desc"
    )
    assert rp.role == UserRole.ADMIN
    assert rp.permissions == [Permission.VIEW_USERS]
    assert rp.description == "desc"


def test_role_permissions_dict() -> None:
    assert UserRole.FREE_USER in ROLE_PERMISSIONS
    assert isinstance(ROLE_PERMISSIONS[UserRole.FREE_USER], RolePermission)
    assert Permission.CREATE_CONTENT in ROLE_PERMISSIONS[UserRole.FREE_USER].permissions
    assert (
        Permission.MANAGE_SYSTEM in ROLE_PERMISSIONS[UserRole.SUPER_ADMIN].permissions
    )


def test_user_create_valid() -> None:
    model = UserCreate(
        email="a@b.com", password="Abcdefg1", first_name="A", last_name="B"
    )
    assert model.email == "a@b.com"
    assert model.role == UserRole.FREE_USER


def test_user_create_invalid_password() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="short1", first_name="A")
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="alllowercase1", first_name="A")
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="ALLUPPERCASE1", first_name="A")
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="NoDigitsHere", first_name="A")


def test_user_login() -> None:
    model = UserLogin(email="a@b.com", password="Abcdefg1")
    assert model.email == "a@b.com"


def test_user_update() -> None:
    model = UserUpdate(
        first_name="A", last_name="B", email="a@b.com", role=UserRole.ADMIN
    )
    assert model.role == UserRole.ADMIN


def test_password_change_valid() -> None:
    model = PasswordChange(current_password="oldpass", new_password="Abcdefg1")
    assert model.new_password == "Abcdefg1"


def test_password_change_invalid() -> None:
    with pytest.raises(ValidationError):
        PasswordChange(current_password="old", new_password="short1")
    with pytest.raises(ValidationError):
        PasswordChange(current_password="old", new_password="alllowercase1")
    with pytest.raises(ValidationError):
        PasswordChange(current_password="old", new_password="ALLUPPERCASE1")
    with pytest.raises(ValidationError):
        PasswordChange(current_password="old", new_password="NoDigitsHere")


def test_password_reset_request() -> None:
    model = PasswordResetRequest(email="a@b.com")
    assert model.email == "a@b.com"


def test_password_reset_confirm_valid() -> None:
    model = PasswordResetConfirm(token="tok", new_password="Abcdefg1")
    assert model.token == "tok"


def test_password_reset_confirm_invalid() -> None:
    with pytest.raises(ValidationError):
        PasswordResetConfirm(token="tok", new_password="short1")


def test_email_verification_request() -> None:
    model = EmailVerificationRequest(email="a@b.com")
    assert model.email == "a@b.com"


def test_email_verification_confirm() -> None:
    model = EmailVerificationConfirm(token="tok")
    assert model.token == "tok"


def test_user_response() -> None:
    now = datetime.utcnow()
    model = UserResponse(
        id="u1",
        email="a@b.com",
        first_name="A",
        last_name="B",
        role=UserRole.ADMIN,
        is_email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now,
        last_login=now,
        permissions=[Permission.VIEW_USERS],
    )
    assert model.role == UserRole.ADMIN
    assert Permission.VIEW_USERS in model.permissions


def test_token_response() -> None:
    model = TokenResponse(access_token="a", refresh_token="r", expires_in=3600)
    assert model.token_type == "bearer"


def test_refresh_token_request() -> None:
    model = RefreshTokenRequest(refresh_token="tok")
    assert model.refresh_token == "tok"


def test_permission_check() -> None:
    model = PermissionCheck(permission=Permission.VIEW_USERS, resource_id="res1")
    assert model.permission == Permission.VIEW_USERS


def test_role_assignment() -> None:
    model = RoleAssignment(
        user_id="u1", role=UserRole.ADMIN, assigned_by="admin", reason="promotion"
    )
    assert model.role == UserRole.ADMIN


def test_audit_log_entry() -> None:
    now = datetime.utcnow()
    entry = AuditLogEntry(
        user_id="u1",
        action="login",
        resource_type="user",
        resource_id="r1",
        details={"ip": "1.2.3.4"},
        ip_address="1.2.3.4",
        user_agent="ua",
        timestamp=now,
    )
    assert entry.action == "login"
    assert entry.timestamp == now


def test_get_user_permissions() -> None:
    perms = get_user_permissions(UserRole.ADMIN)
    assert Permission.VIEW_USERS in perms
    assert isinstance(perms, list)


def test_has_permission() -> None:
    assert has_permission(UserRole.ADMIN, Permission.VIEW_USERS)
    assert not has_permission(UserRole.FREE_USER, Permission.MANAGE_SYSTEM)


def test_get_role_hierarchy() -> None:
    hierarchy = get_role_hierarchy()
    assert hierarchy[UserRole.FREE_USER] < hierarchy[UserRole.ADMIN]
    assert hierarchy[UserRole.SUPER_ADMIN] > hierarchy[UserRole.PREMIUM_USER]


def test_can_manage_role() -> None:
    assert can_manage_role(UserRole.SUPER_ADMIN, UserRole.ADMIN)
    assert not can_manage_role(UserRole.FREE_USER, UserRole.ADMIN)

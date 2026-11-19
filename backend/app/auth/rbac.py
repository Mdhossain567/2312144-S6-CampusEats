"""Centralized Role-Based Access Control (RBAC) and permission constants.

Enforces system roles, permission checks, and administrative safety invariants.
"""
from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import CurrentUser
from app.users.models import AppUser


class UserRole(str, Enum):
    CUSTOMER = "customer"
    KITCHEN_STAFF = "kitchen_staff"
    ADMIN = "admin"


class Permission(str, Enum):
    # Menu permissions
    MENU_READ = "menu:read"
    MENU_MANAGE = "menu:manage"

    # Order permissions
    ORDER_CREATE = "order:create"
    ORDER_READ_OWN = "order:read_own"
    ORDER_MANAGE_STATUS = "order:manage_status"
    ORDER_CANCEL_OWN = "order:cancel_own"

    # Group permissions
    GROUP_CREATE = "group:create"
    GROUP_READ = "group:read"
    GROUP_MANAGE = "group:manage"

    # Admin dashboard & management
    ADMIN_DASHBOARD = "admin:dashboard"
    USER_MANAGE = "user:manage"
    CONTENT_MODERATE = "content:moderate"
    AUDIT_VIEW = "audit:view"
    DATA_EXPORT = "data:export"


# Role-to-permissions mapping matrix
ROLE_PERMISSIONS: dict[str, set[str]] = {
    UserRole.CUSTOMER.value: {
        Permission.MENU_READ.value,
        Permission.ORDER_CREATE.value,
        Permission.ORDER_READ_OWN.value,
        Permission.ORDER_CANCEL_OWN.value,
        Permission.GROUP_CREATE.value,
        Permission.GROUP_READ.value,
    },
    UserRole.KITCHEN_STAFF.value: {
        Permission.MENU_READ.value,
        Permission.ORDER_MANAGE_STATUS.value,
        Permission.GROUP_READ.value,
    },
    UserRole.ADMIN.value: {
        # Admin inherits all permissions
        perm.value for perm in Permission
    },
}


def has_permission(user: AppUser, permission: str | Permission) -> bool:
    perm_val = permission.value if isinstance(permission, Permission) else permission
    user_perms = ROLE_PERMISSIONS.get(user.role, set())
    return perm_val in user_perms


def require_permission(permission: str | Permission):
    """Reusable FastAPI dependency to enforce a specific permission on an endpoint."""
    perm_val = permission.value if isinstance(permission, Permission) else permission

    def dependency(user: CurrentUser) -> AppUser:
        if not has_permission(user, perm_val):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return dependency


def check_admin_safety(actor: AppUser, target: AppUser, action: str) -> None:
    """Enforces safety rules:

    1. An admin cannot ban another admin.
    2. An admin cannot change their own role (self-demotion/lockout protection).
    """
    if action == "ban":
        if target.role == UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot ban another administrator.",
            )
    elif action == "role_change":
        if actor.id == target.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot change their own role.",
            )

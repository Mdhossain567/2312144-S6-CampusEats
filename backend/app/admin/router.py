"""HTTP endpoints for the Admin Dashboard under /api/v1/admin (JSON and CSV)."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Response, status

from app.admin import service
from app.admin.schemas import (
    AdminStats,
    AdminUserDetail,
    AdminUserPage,
    BanRequest,
    BulkActionResponse,
    BulkBanRequest,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUnbanRequest,
    RoleChangeRequest,
)
from app.audit import repository as audit_repo
from app.auth.dependencies import require_roles
from app.database import SessionDep
from app.users.models import AppUser

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Enforce system admin role for all endpoints in this router
AdminUser = Annotated[AppUser, Depends(require_roles("admin"))]


@router.get("/stats", response_model=AdminStats)
def get_dashboard_stats(admin: AdminUser, session: SessionDep):
    """Overview statistics for users, bans, orders, menu items, groups, and 7d growth."""
    return service.get_stats(session)


@router.get("/users", response_model=AdminUserPage)
def list_users(
    admin: AdminUser,
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
):
    """List users with search, role filter, status filter (active/banned), and pagination."""
    return service.list_users(session, offset, limit, q, role, status)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def get_user_detail(user_id: int, admin: AdminUser, session: SessionDep):
    """Detailed user view: active sessions, groups, recent orders, and audit history."""
    return service.get_user_detail(session, user_id)


@router.post("/users/{user_id}/ban", status_code=status.HTTP_204_NO_CONTENT)
def ban_user(user_id: int, data: BanRequest, admin: AdminUser, session: SessionDep):
    """Ban an account with a mandatory reason string (prevents banning another admin)."""
    service.ban_user(session, admin, user_id, data.reason)


@router.post("/users/{user_id}/unban", status_code=status.HTTP_204_NO_CONTENT)
def unban_user(user_id: int, admin: AdminUser, session: SessionDep):
    """Unban an account."""
    service.unban_user(session, admin, user_id)


@router.post("/users/{user_id}/role", status_code=status.HTTP_204_NO_CONTENT)
def change_user_role(user_id: int, data: RoleChangeRequest, admin: AdminUser, session: SessionDep):
    """Change an account's role (prevents changing own role)."""
    service.change_role(session, admin, user_id, data.role)


@router.post("/users/{user_id}/revoke-sessions", status_code=status.HTTP_204_NO_CONTENT)
def revoke_user_sessions(user_id: int, admin: AdminUser, session: SessionDep):
    """Revoke all active sessions for a user."""
    service.revoke_user_sessions(session, admin, user_id)


@router.post("/users/bulk-ban", response_model=BulkActionResponse)
def bulk_ban_users(data: BulkBanRequest, admin: AdminUser, session: SessionDep):
    """Bulk ban multiple accounts (skips fellow admins and self)."""
    return service.bulk_ban(session, admin, data.user_ids, data.reason)


@router.post("/users/bulk-unban", response_model=BulkActionResponse)
def bulk_unban_users(data: BulkUnbanRequest, admin: AdminUser, session: SessionDep):
    """Bulk unban multiple accounts."""
    return service.bulk_unban(session, admin, data.user_ids)


# ── Content Moderation ────────────────────────────────────────────────────────


@router.get("/content")
def list_content(
    admin: AdminUser,
    session: SessionDep,
    type: str = Query("orders", pattern="^(orders|menu|groups)$"),
    q: Optional[str] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List records across the platform (orders, menu items, or groups) with filtering."""
    return service.list_content(session, type, q, offset, limit)


@router.delete("/content/{content_type}/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content_item(
    content_type: str, content_id: int, admin: AdminUser, session: SessionDep
):
    """Moderation action: delete a specific order, menu item, or group."""
    service.delete_content_item(session, admin, content_type, content_id)


@router.post("/content/bulk-delete", response_model=BulkDeleteResponse)
def bulk_delete_content(data: BulkDeleteRequest, admin: AdminUser, session: SessionDep):
    """Moderation action: bulk delete multiple records."""
    return service.bulk_delete_content(session, admin, data.type, data.ids)


# ── Activity / Audit Log ──────────────────────────────────────────────────────


@router.get("/audit-logs")
def list_audit_logs(
    admin: AdminUser,
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    q: Optional[str] = None,
):
    """Query activity audit logs with action filters, user filter, and search."""
    items, total = audit_repo.list_audit_logs(session, offset, limit, action, user_id, q)
    return {"items": items, "total": total, "offset": offset, "limit": limit}


# ── Security View ─────────────────────────────────────────────────────────────


@router.get("/security")
def get_security_view(admin: AdminUser, session: SessionDep):
    """Security view aggregating failed logins by IP address and by account."""
    return audit_repo.get_security_failed_logins(session)


# ── CSV Exports ───────────────────────────────────────────────────────────────


@router.get("/export/users")
def export_users(admin: AdminUser, session: SessionDep):
    csv_data = service.export_users_csv(session, admin)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=campuseats_users.csv"},
    )


@router.get("/export/orders")
def export_orders(admin: AdminUser, session: SessionDep):
    csv_data = service.export_orders_csv(session, admin)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=campuseats_orders.csv"},
    )


@router.get("/export/audit-logs")
def export_audit_logs(admin: AdminUser, session: SessionDep):
    csv_data = service.export_audit_logs_csv(session, admin)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=campuseats_audit_logs.csv"},
    )

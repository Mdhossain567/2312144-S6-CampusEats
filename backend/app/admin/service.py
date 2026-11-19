"""Business operations for the Admin Dashboard and Content Moderation."""
import csv
import io
from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, col, desc, select

from app.audit import repository as audit_repo
from app.audit.models import AuditLog
from app.audit.repository import log_event
from app.auth.rbac import check_admin_safety
from app.clock import utc_now
from app.groups.models import GroupMember, MealGroup
from app.menu_items.models import MenuItem
from app.orders.models import CustomerOrder
from app.users import repository as user_repo
from app.users import session_repository as sess_repo
from app.users.models import AppUser
from app.users.schemas import SessionRead
from app.users.session_model import UserSession
from app.admin.schemas import (
    AdminStats,
    AdminUserDetail,
    AdminUserPage,
    AdminUserRead,
    BulkActionResponse,
    BulkDeleteResponse,
)


def get_stats(session: Session) -> AdminStats:
    now = utc_now()
    seven_days_ago = now - timedelta(days=7)

    total_users = session.exec(select(func.count(AppUser.id))).one()
    banned_users = session.exec(
        select(func.count(AppUser.id)).where(AppUser.is_banned == True)  # noqa: E712
    ).one()
    total_orders = session.exec(select(func.count(CustomerOrder.id))).one()
    total_menu_items = session.exec(select(func.count(MenuItem.id))).one()
    total_groups = session.exec(select(func.count(MealGroup.id))).one()

    new_users_7d = session.exec(
        select(func.count(AppUser.id)).where(AppUser.created_at >= seven_days_ago)
    ).one()
    new_orders_7d = session.exec(
        select(func.count(CustomerOrder.id)).where(CustomerOrder.created_at >= seven_days_ago)
    ).one()

    return AdminStats(
        total_users=total_users,
        banned_users=banned_users,
        total_orders=total_orders,
        total_menu_items=total_menu_items,
        total_groups=total_groups,
        new_users_7d=new_users_7d,
        new_orders_7d=new_orders_7d,
    )


def list_users(
    session: Session,
    offset: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> AdminUserPage:
    statement = select(AppUser)

    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            col(AppUser.name).ilike(term) | col(AppUser.email).ilike(term)
        )

    if role:
        statement = statement.where(AppUser.role == role)

    if status_filter == "banned":
        statement = statement.where(AppUser.is_banned == True)  # noqa: E712
    elif status_filter == "active":
        statement = statement.where(AppUser.is_banned == False)  # noqa: E712

    count_stmt = select(func.count()).select_from(statement.subquery())
    total = session.exec(count_stmt).one()

    statement = statement.order_by(desc(AppUser.created_at)).offset(offset).limit(limit)
    users = session.exec(statement).all()

    items = []
    for u in users:
        sessions_count = len(sess_repo.list_active(session, u.id))
        orders_count = session.exec(
            select(func.count(CustomerOrder.id)).where(CustomerOrder.user_id == u.id)
        ).one()
        items.append(
            AdminUserRead(
                id=u.id,
                name=u.name,
                email=u.email,
                role=u.role,
                is_active=u.is_active,
                is_banned=u.is_banned,
                banned_at=u.banned_at,
                ban_reason=u.ban_reason,
                failed_logins=u.failed_logins,
                last_login_at=u.last_login_at,
                created_at=u.created_at,
                active_sessions_count=sessions_count,
                orders_count=orders_count,
            )
        )

    return AdminUserPage(items=items, total=total, offset=offset, limit=limit)


def get_user_detail(session: Session, user_id: int) -> AdminUserDetail:
    u = user_repo.get(session, user_id)
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    active_sessions = sess_repo.list_active(session, u.id)
    sessions_read = [
        SessionRead(
            id=s.id,
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            created_at=s.created_at,
            expires_at=s.expires_at,
            is_current=False,
        )
        for s in active_sessions
    ]

    # Recent orders
    orders = session.exec(
        select(CustomerOrder)
        .where(CustomerOrder.user_id == u.id)
        .order_by(desc(CustomerOrder.created_at))
        .limit(10)
    ).all()
    recent_orders = [
        {"id": o.id, "total": o.total, "status": o.status, "created_at": o.created_at.isoformat()}
        for o in orders
    ]

    # Joined groups
    groups_stmt = (
        select(MealGroup, GroupMember.role)
        .join(GroupMember, GroupMember.group_id == MealGroup.id)
        .where(GroupMember.user_id == u.id)
    )
    groups = [
        {"id": g.id, "name": g.name, "role": role}
        for g, role in session.exec(groups_stmt).all()
    ]

    # Recent audit logs
    logs = session.exec(
        select(AuditLog)
        .where(AuditLog.user_id == u.id)
        .order_by(desc(AuditLog.created_at))
        .limit(15)
    ).all()
    recent_activity = [
        {"action": l.action, "details": l.details, "ip_address": l.ip_address, "created_at": l.created_at.isoformat()}
        for l in logs
    ]

    return AdminUserDetail(
        id=u.id,
        name=u.name,
        email=u.email,
        role=u.role,
        is_active=u.is_active,
        is_banned=u.is_banned,
        banned_at=u.banned_at,
        ban_reason=u.ban_reason,
        failed_logins=u.failed_logins,
        last_login_at=u.last_login_at,
        created_at=u.created_at,
        active_sessions_count=len(sessions_read),
        orders_count=len(orders),
        sessions=sessions_read,
        recent_activity=recent_activity,
        recent_orders=recent_orders,
        groups=groups,
    )


def ban_user(session: Session, actor: AppUser, target_user_id: int, reason: str) -> None:
    target = user_repo.get(session, target_user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # Safety check: Cannot ban another admin
    check_admin_safety(actor, target, action="ban")

    target.is_banned = True
    target.banned_at = utc_now()
    target.ban_reason = reason.strip()
    user_repo.save(session, target)

    # Invalidate all active sessions immediately
    for s in sess_repo.list_active(session, target.id):
        sess_repo.revoke(session, s)

    log_event(
        session,
        action="USER_BAN",
        user_id=actor.id,
        user_email=actor.email,
        resource_type="app_user",
        resource_id=str(target.id),
        details=f"Banned user {target.email}. Reason: {reason}",
    )


def unban_user(session: Session, actor: AppUser, target_user_id: int) -> None:
    target = user_repo.get(session, target_user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    target.is_banned = False
    target.banned_at = None
    target.ban_reason = None
    user_repo.save(session, target)

    log_event(
        session,
        action="USER_UNBAN",
        user_id=actor.id,
        user_email=actor.email,
        resource_type="app_user",
        resource_id=str(target.id),
        details=f"Unbanned user {target.email}",
    )


def change_role(session: Session, actor: AppUser, target_user_id: int, new_role: str) -> None:
    target = user_repo.get(session, target_user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # Safety check: Admin cannot change their own role
    check_admin_safety(actor, target, action="role_change")

    old_role = target.role
    target.role = new_role
    user_repo.save(session, target)

    log_event(
        session,
        action="ROLE_CHANGE",
        user_id=actor.id,
        user_email=actor.email,
        resource_type="app_user",
        resource_id=str(target.id),
        details=f"Changed role of {target.email} from {old_role} to {new_role}",
    )


def revoke_user_sessions(session: Session, actor: AppUser, target_user_id: int) -> int:
    target = user_repo.get(session, target_user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    count = 0
    for s in sess_repo.list_active(session, target.id):
        sess_repo.revoke(session, s)
        count += 1

    log_event(
        session,
        action="SESSIONS_REVOKE",
        user_id=actor.id,
        user_email=actor.email,
        resource_type="app_user",
        resource_id=str(target.id),
        details=f"Revoked {count} active sessions for {target.email}",
    )
    return count


def bulk_ban(session: Session, actor: AppUser, user_ids: list[int], reason: str) -> BulkActionResponse:
    affected = 0
    skipped = 0

    for uid in user_ids:
        u = user_repo.get(session, uid)
        if u is None or u.role == "admin" or u.id == actor.id or u.is_banned:
            skipped += 1
            continue
        u.is_banned = True
        u.banned_at = utc_now()
        u.ban_reason = reason.strip()
        user_repo.save(session, u)
        for s in sess_repo.list_active(session, u.id):
            sess_repo.revoke(session, s)
        affected += 1

    log_event(
        session,
        action="BULK_BAN",
        user_id=actor.id,
        user_email=actor.email,
        details=f"Bulk banned {affected} users (skipped {skipped}). Reason: {reason}",
    )
    return BulkActionResponse(affected=affected, skipped=skipped)


def bulk_unban(session: Session, actor: AppUser, user_ids: list[int]) -> BulkActionResponse:
    affected = 0
    skipped = 0

    for uid in user_ids:
        u = user_repo.get(session, uid)
        if u is None or not u.is_banned:
            skipped += 1
            continue
        u.is_banned = False
        u.banned_at = None
        u.ban_reason = None
        user_repo.save(session, u)
        affected += 1

    log_event(
        session,
        action="BULK_UNBAN",
        user_id=actor.id,
        user_email=actor.email,
        details=f"Bulk unbanned {affected} users (skipped {skipped})",
    )
    return BulkActionResponse(affected=affected, skipped=skipped)


# ── Content Moderation ────────────────────────────────────────────────────────


def list_content(session: Session, content_type: str, search: Optional[str] = None, offset: int = 0, limit: int = 50) -> dict:
    if content_type == "orders":
        stmt = select(CustomerOrder)
        count_stmt = select(func.count(CustomerOrder.id))
        total = session.exec(count_stmt).one()
        orders = session.exec(stmt.order_by(desc(CustomerOrder.created_at)).offset(offset).limit(limit)).all()
        items = [{"id": o.id, "title": f"Order #{o.id}", "user_id": o.user_id, "total": o.total, "status": o.status, "created_at": o.created_at.isoformat()} for o in orders]
        return {"items": items, "total": total}

    elif content_type == "menu":
        stmt = select(MenuItem)
        if search:
            stmt = stmt.where(col(MenuItem.name).ilike(f"%{search.strip()}%"))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = session.exec(count_stmt).one()
        menu_items = session.exec(stmt.order_by(MenuItem.name).offset(offset).limit(limit)).all()
        items = [{"id": m.id, "title": m.name, "category": m.category, "price": m.price, "available": m.available} for m in menu_items]
        return {"items": items, "total": total}

    elif content_type == "groups":
        stmt = select(MealGroup)
        if search:
            stmt = stmt.where(col(MealGroup.name).ilike(f"%{search.strip()}%"))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = session.exec(count_stmt).one()
        groups = session.exec(stmt.order_by(MealGroup.name).offset(offset).limit(limit)).all()
        items = [{"id": g.id, "title": g.name, "owner_id": g.owner_id, "description": g.description, "created_at": g.created_at.isoformat()} for g in groups]
        return {"items": items, "total": total}

    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid content type")


def delete_content_item(session: Session, actor: AppUser, content_type: str, content_id: int) -> None:
    if content_type == "orders":
        order = session.get(CustomerOrder, content_id)
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        session.delete(order)
    elif content_type == "menu":
        from app.menu_items import repository as m_repo
        item = m_repo.get(session, content_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Menu item not found")
        m_repo.delete(session, item)
    elif content_type == "groups":
        from app.groups import repository as g_repo
        group = g_repo.get_group(session, content_id)
        if not group:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")
        g_repo.delete_group(session, group)
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid content type")

    session.commit()
    log_event(
        session,
        action="CONTENT_DELETE",
        user_id=actor.id,
        user_email=actor.email,
        resource_type=content_type,
        resource_id=str(content_id),
        details=f"Admin deleted {content_type} item #{content_id}",
    )


def bulk_delete_content(session: Session, actor: AppUser, content_type: str, ids: list[int]) -> BulkDeleteResponse:
    deleted = 0
    for cid in ids:
        try:
            delete_content_item(session, actor, content_type, cid)
            deleted += 1
        except Exception:
            continue
    return BulkDeleteResponse(deleted=deleted)


# ── CSV Exports ───────────────────────────────────────────────────────────────


def export_users_csv(session: Session, actor: AppUser) -> str:
    users = session.exec(select(AppUser).order_by(AppUser.id)).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Role", "Active", "Banned", "Ban Reason", "Created At", "Last Login"])
    for u in users:
        writer.writerow([u.id, u.name, u.email, u.role, u.is_active, u.is_banned, u.ban_reason or "", u.created_at.isoformat(), u.last_login_at.isoformat() if u.last_login_at else ""])

    log_event(session, action="EXPORT_CSV", user_id=actor.id, user_email=actor.email, details="Exported users CSV")
    return output.getvalue()


def export_orders_csv(session: Session, actor: AppUser) -> str:
    orders = session.exec(select(CustomerOrder).order_by(CustomerOrder.id)).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "User ID", "Status", "Total", "Created At", "Updated At"])
    for o in orders:
        writer.writerow([o.id, o.user_id, o.status, o.total, o.created_at.isoformat(), o.updated_at.isoformat()])

    log_event(session, action="EXPORT_CSV", user_id=actor.id, user_email=actor.email, details="Exported orders CSV")
    return output.getvalue()


def export_audit_logs_csv(session: Session, actor: AppUser) -> str:
    logs = session.exec(select(AuditLog).order_by(desc(AuditLog.created_at))).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Log ID", "Action", "User ID", "User Email", "Resource Type", "Resource ID", "IP Address", "Created At", "Details"])
    for l in logs:
        writer.writerow([l.id, l.action, l.user_id or "", l.user_email or "", l.resource_type or "", l.resource_id or "", l.ip_address or "", l.created_at.isoformat(), l.details or ""])

    log_event(session, action="EXPORT_CSV", user_id=actor.id, user_email=actor.email, details="Exported audit logs CSV")
    return output.getvalue()

"""Database operations for audit logs."""
from typing import Optional

from sqlmodel import Session, col, desc, select

from app.audit.models import AuditLog


def log_event(
    session: Session,
    action: str,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[str] = None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        user_id=user_id,
        user_email=user_email,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def list_audit_logs(
    session: Session,
    offset: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    search: Optional[str] = None,
) -> tuple[list[AuditLog], int]:
    statement = select(AuditLog)
    if action:
        statement = statement.where(AuditLog.action == action)
    if user_id:
        statement = statement.where(AuditLog.user_id == user_id)
    if search:
        search_term = f"%{search.strip()}%"
        statement = statement.where(
            col(AuditLog.user_email).ilike(search_term)
            | col(AuditLog.details).ilike(search_term)
            | col(AuditLog.ip_address).ilike(search_term)
            | col(AuditLog.action).ilike(search_term)
        )

    from sqlalchemy import func
    count_statement = select(func.count()).select_from(statement.subquery())
    total = session.exec(count_statement).one()

    statement = statement.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
    items = session.exec(statement).all()
    return list(items), total


def get_security_failed_logins(session: Session) -> dict:
    """Aggregate failed login attempts by IP address and by account/email."""
    from sqlalchemy import func

    # By IP
    ip_query = (
        select(
            AuditLog.ip_address,
            func.count(AuditLog.id).label("count"),
            func.max(AuditLog.created_at).label("last_attempt"),
        )
        .where(AuditLog.action == "FAILED_LOGIN")
        .group_by(AuditLog.ip_address)
        .order_by(desc("count"))
        .limit(20)
    )
    by_ip = [
        {"ip_address": row[0] or "unknown", "count": row[1], "last_attempt": row[2]}
        for row in session.exec(ip_query).all()
    ]

    # By User Email
    email_query = (
        select(
            AuditLog.user_email,
            func.count(AuditLog.id).label("count"),
            func.max(AuditLog.created_at).label("last_attempt"),
        )
        .where(AuditLog.action == "FAILED_LOGIN")
        .group_by(AuditLog.user_email)
        .order_by(desc("count"))
        .limit(20)
    )
    by_email = [
        {"email": row[0] or "unknown", "count": row[1], "last_attempt": row[2]}
        for row in session.exec(email_query).all()
    ]

    return {"by_ip": by_ip, "by_account": by_email}

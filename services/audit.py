from models.audit_log import AuditLog, AuditAction
from models.database import SessionLocal
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def log_audit_event(
    user_id: Optional[str],
    action: AuditAction,
    resource: str,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> None:
    """Log an audit event to the database."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
        logger.info(f"Audit log: {action} {resource} {resource_id} by {user_id}")
    except Exception as exc:
        logger.error(f"Failed to log audit event: {exc}")
        db.rollback()
    finally:
        if close_db:
            db.close()

def extract_request_context(request: Request) -> Dict[str, Any]:
    """Extract context info from FastAPI request for audit logging."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }

def log_audit_from_request(
    request: Request,
    user_id: Optional[str],
    action: AuditAction,
    resource: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> None:
    ctx = extract_request_context(request)
    log_audit_event(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
        details=details,
        db=db
    ) 
from enum import Enum
from services.supabase import get_supabase_client
from typing import Optional, Dict, Any
from fastapi import Request
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"


def log_audit_event(
    user_id: Optional[str],
    action: AuditAction,
    resource: str,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    db: Optional[Any] = None,  # Keep for compatibility but not used
) -> None:
    """Log an audit event to the database using Supabase."""
    try:
        supabase = get_supabase_client()

        audit_data = {
            "user_id": user_id,
            "action": action.value,
            "resource": resource,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Insert audit log into Supabase
        result = supabase.table("audit_logs").insert(audit_data).execute()  # noqa: F841

        logger.info(f"Audit log: {action} {resource} {resource_id} by {user_id}")
    except Exception as exc:
        logger.error(f"Failed to log audit event: {exc}")
        # Don't fail the main operation if audit logging fails
        # This could happen if the audit_logs table doesn't exist yet


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
    db: Optional[Any] = None,
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
        db=db,
    )

from fastapi import Request, Depends
from typing import Optional, Dict, Any
from services.audit import log_audit_from_request, AuditAction

class AuditLogger:
    def __init__(self, action: AuditAction, resource: str):
        self.action = action
        self.resource = resource

    async def __call__(
        self,
        request: Request,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        log_audit_from_request(
            request=request,
            user_id=user_id,
            action=self.action,
            resource=self.resource,
            resource_id=resource_id,
            details=details
        )

# Usage example in a route:
# from services.audit_dependency import AuditLogger
# @router.post("/something", dependencies=[Depends(AuditLogger(AuditAction.CREATE, "something"))]) 
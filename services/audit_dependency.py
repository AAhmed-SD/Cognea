from typing import Any

from fastapi import Request

from services.audit import AuditAction, log_audit_from_request


class AuditLogger:
    def __init__(self, action: AuditAction, resource: str):
    pass
        self.action = action
        self.resource = resource

    async def __call__(
        self,
        request: Request,
        user_id: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
    pass
        log_audit_from_request(
            request=request,
            user_id=user_id,
            action=self.action,
            resource=self.resource,
            resource_id=resource_id,
            details=details,
        )


# Usage example in a route:
# from services.audit_dependency import AuditLogger
# @router.post("/something", dependencies=[Depends(AuditLogger(AuditAction.CREATE, "something"))])

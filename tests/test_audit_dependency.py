from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request

from services.audit import AuditAction
from services.audit_dependency import AuditLogger


@pytest.mark.asyncio
async def test_audit_logger_calls_log_audit_from_request():
    mock_request = MagicMock(spec=Request)
    action = AuditAction.CREATE
    resource = "test_resource"
    logger = AuditLogger(action, resource)

    with patch("services.audit_dependency.log_audit_from_request") as mock_log:
        await logger(
            mock_request, user_id="user1", resource_id="res1", details={"foo": "bar"}
        )
        mock_log.assert_called_once_with(
            request=mock_request,
            user_id="user1",
            action=action,
            resource=resource,
            resource_id="res1",
            details={"foo": "bar"},
        )


@pytest.mark.asyncio
async def test_audit_logger_with_minimal_args():
    mock_request = MagicMock(spec=Request)
    action = AuditAction.UPDATE
    resource = "thing"
    logger = AuditLogger(action, resource)

    with patch("services.audit_dependency.log_audit_from_request") as mock_log:
        await logger(mock_request)
        mock_log.assert_called_once_with(
            request=mock_request,
            user_id=None,
            action=action,
            resource=resource,
            resource_id=None,
            details=None,
        )


@pytest.mark.asyncio
async def test_audit_logger_with_partial_args():
    mock_request = MagicMock(spec=Request)
    action = AuditAction.DELETE
    resource = "item"
    logger = AuditLogger(action, resource)

    with patch("services.audit_dependency.log_audit_from_request") as mock_log:
        await logger(mock_request, user_id="u2")
        mock_log.assert_called_once_with(
            request=mock_request,
            user_id="u2",
            action=action,
            resource=resource,
            resource_id=None,
            details=None,
        )

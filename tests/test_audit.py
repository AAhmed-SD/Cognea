from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import Request

from services.audit import (
    AuditAction,
    extract_request_context,
    log_audit_event,
    log_audit_from_request,
)


class TestAuditAction:
    """Test AuditAction enum"""

    def test_audit_action_values(self):
        """Test that all AuditAction values are correct"""
        assert AuditAction.CREATE.value == "create"
        assert AuditAction.READ.value == "read"
        assert AuditAction.UPDATE.value == "update"
        assert AuditAction.DELETE.value == "delete"
        assert AuditAction.LOGIN.value == "login"
        assert AuditAction.LOGOUT.value == "logout"
        assert AuditAction.SIGNUP.value == "signup"

    def test_audit_action_enumeration(self):
        """Test that all audit actions are properly enumerated"""
        actions = list(AuditAction)
        assert len(actions) == 7
        assert AuditAction.CREATE in actions
        assert AuditAction.READ in actions
        assert AuditAction.UPDATE in actions
        assert AuditAction.DELETE in actions
        assert AuditAction.LOGIN in actions
        assert AuditAction.LOGOUT in actions
        assert AuditAction.SIGNUP in actions


class TestLogAuditEvent:
    """Test log_audit_event function"""

    @patch("services.audit.get_supabase_client")
    @patch("services.audit.logger")
    def test_log_audit_event_success(self, mock_logger, mock_get_supabase):
        """Test successful audit event logging"""
        # Mock Supabase client
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        # Mock the insert chain
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        # Test data
        user_id = "user123"
        action = AuditAction.CREATE
        resource = "users"
        resource_id = "new_user_456"
        ip_address = "192.168.1.1"
        user_agent = "Mozilla/5.0"
        details = {"field": "value"}

        with patch("services.audit.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            log_audit_event(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details,
            )

            # Verify Supabase was called correctly
            mock_supabase.table.assert_called_once_with("audit_logs")
            mock_table.insert.assert_called_once()

            # Verify the audit data
            call_args = mock_table.insert.call_args[0][0]
            assert call_args["user_id"] == user_id
            assert call_args["action"] == action.value
            assert call_args["resource"] == resource
            assert call_args["resource_id"] == resource_id
            assert call_args["ip_address"] == ip_address
            assert call_args["user_agent"] == user_agent
            assert call_args["details"] == details
            assert call_args["timestamp"] is not None  # Should have timestamp

            # Verify logging
            mock_logger.info.assert_called_once_with(
                f"Audit log: {action} {resource} {resource_id} by {user_id}"
            )

    @patch("services.audit.get_supabase_client")
    @patch("services.audit.logger")
    def test_log_audit_event_minimal_data(self, mock_logger, mock_get_supabase):
        """Test audit event logging with minimal data"""
        # Mock Supabase client
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        # Mock the insert chain
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        # Test with minimal data
        user_id = None
        action = AuditAction.READ
        resource = "users"

        with patch("services.audit.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            log_audit_event(
                user_id=user_id,
                action=action,
                resource=resource,
            )

            # Verify the audit data
            call_args = mock_table.insert.call_args[0][0]
            assert call_args["user_id"] is None
            assert call_args["action"] == action.value
            assert call_args["resource"] == resource
            assert call_args["resource_id"] is None
            assert call_args["ip_address"] is None
            assert call_args["user_agent"] is None
            assert call_args["details"] is None
            assert call_args["timestamp"] is not None  # Should have timestamp

            # Verify logging
            mock_logger.info.assert_called_once_with(
                f"Audit log: {action} {resource} None by None"
            )

    @patch("services.audit.get_supabase_client")
    @patch("services.audit.logger")
    def test_log_audit_event_supabase_error(self, mock_logger, mock_get_supabase):
        """Test audit event logging when Supabase fails"""
        # Mock Supabase client to raise an exception
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table.side_effect = Exception("Database connection failed")

        # Test data
        user_id = "user123"
        action = AuditAction.UPDATE
        resource = "users"

        log_audit_event(
            user_id=user_id,
            action=action,
            resource=resource,
        )

        # Verify error was logged but didn't raise exception
        mock_logger.error.assert_called_once_with(
            "Failed to log audit event: Database connection failed"
        )

    @patch("services.audit.get_supabase_client")
    @patch("services.audit.logger")
    def test_log_audit_event_all_actions(self, mock_logger, mock_get_supabase):
        """Test audit event logging for all action types"""
        # Mock Supabase client
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        # Mock the insert chain
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        # Test all actions
        actions = [
            AuditAction.CREATE,
            AuditAction.READ,
            AuditAction.UPDATE,
            AuditAction.DELETE,
            AuditAction.LOGIN,
            AuditAction.LOGOUT,
            AuditAction.SIGNUP,
        ]

        with patch("services.audit.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            for action in actions:
                log_audit_event(
                    user_id="user123",
                    action=action,
                    resource="test_resource",
                )

                # Verify the action was logged correctly
                call_args = mock_table.insert.call_args[0][0]
                assert call_args["action"] == action.value

                # Reset for next iteration
                mock_table.insert.reset_mock()
                mock_logger.info.reset_mock()


class TestExtractRequestContext:
    """Test extract_request_context function"""

    def test_extract_request_context_with_client(self):
        """Test extracting context from request with client"""
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.100"
        mock_request.headers.get.return_value = "Mozilla/5.0 (Test Browser)"

        context = extract_request_context(mock_request)

        assert context["ip_address"] == "192.168.1.100"
        assert context["user_agent"] == "Mozilla/5.0 (Test Browser)"
        mock_request.headers.get.assert_called_once_with("user-agent")

    def test_extract_request_context_without_client(self):
        """Test extracting context from request without client"""
        # Mock request without client
        mock_request = MagicMock(spec=Request)
        mock_request.client = None
        mock_request.headers.get.return_value = "Mozilla/5.0 (Test Browser)"

        context = extract_request_context(mock_request)

        assert context["ip_address"] is None
        assert context["user_agent"] == "Mozilla/5.0 (Test Browser)"

    def test_extract_request_context_without_user_agent(self):
        """Test extracting context from request without user agent"""
        # Mock request without user agent
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.100"
        mock_request.headers.get.return_value = None

        context = extract_request_context(mock_request)

        assert context["ip_address"] == "192.168.1.100"
        assert context["user_agent"] is None

    def test_extract_request_context_empty_request(self):
        """Test extracting context from empty request"""
        # Mock request with no client and no user agent
        mock_request = MagicMock(spec=Request)
        mock_request.client = None
        mock_request.headers.get.return_value = None

        context = extract_request_context(mock_request)

        assert context["ip_address"] is None
        assert context["user_agent"] is None


class TestLogAuditFromRequest:
    """Test log_audit_from_request function"""

    @patch("services.audit.log_audit_event")
    def test_log_audit_from_request_success(self, mock_log_audit_event):
        """Test successful audit logging from request"""
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.100"
        mock_request.headers.get.return_value = "Mozilla/5.0 (Test Browser)"

        # Test data
        user_id = "user123"
        action = AuditAction.DELETE
        resource = "users"
        resource_id = "user_456"
        details = {"reason": "inactive account"}

        log_audit_from_request(
            request=mock_request,
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
        )

        # Verify log_audit_event was called with correct parameters
        mock_log_audit_event.assert_called_once_with(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Test Browser)",
            details=details,
            db=None,
        )

    @patch("services.audit.log_audit_event")
    def test_log_audit_from_request_minimal_data(self, mock_log_audit_event):
        """Test audit logging from request with minimal data"""
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.client = None
        mock_request.headers.get.return_value = None

        # Test with minimal data
        user_id = None
        action = AuditAction.READ
        resource = "public_data"

        log_audit_from_request(
            request=mock_request,
            user_id=user_id,
            action=action,
            resource=resource,
        )

        # Verify log_audit_event was called with correct parameters
        mock_log_audit_event.assert_called_once_with(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=None,
            ip_address=None,
            user_agent=None,
            details=None,
            db=None,
        )

    @patch("services.audit.log_audit_event")
    def test_log_audit_from_request_with_db(self, mock_log_audit_event):
        """Test audit logging from request with db parameter"""
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.100"
        mock_request.headers.get.return_value = "Mozilla/5.0 (Test Browser)"

        # Mock database
        mock_db = MagicMock()

        # Test data
        user_id = "user123"
        action = AuditAction.CREATE
        resource = "posts"

        log_audit_from_request(
            request=mock_request,
            user_id=user_id,
            action=action,
            resource=resource,
            db=mock_db,
        )

        # Verify log_audit_event was called with db parameter
        mock_log_audit_event.assert_called_once_with(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=None,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Test Browser)",
            details=None,
            db=mock_db,
        )


class TestAuditIntegration:
    """Integration tests for audit functionality"""

    @patch("services.audit.get_supabase_client")
    @patch("services.audit.logger")
    def test_full_audit_flow(self, mock_logger, mock_get_supabase):
        """Test complete audit flow from request to database"""
        # Mock Supabase client
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        # Mock the insert chain
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.100"
        mock_request.headers.get.return_value = "Mozilla/5.0 (Test Browser)"

        # Test data
        user_id = "user123"
        action = AuditAction.LOGIN
        resource = "auth"
        details = {"method": "password"}

        with patch("services.audit.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            # Test the full flow
            log_audit_from_request(
                request=mock_request,
                user_id=user_id,
                action=action,
                resource=resource,
                details=details,
            )

            # Verify the audit data was logged correctly
            call_args = mock_table.insert.call_args[0][0]
            assert call_args["user_id"] == user_id
            assert call_args["action"] == action.value
            assert call_args["resource"] == resource
            assert call_args["ip_address"] == "192.168.1.100"
            assert call_args["user_agent"] == "Mozilla/5.0 (Test Browser)"
            assert call_args["details"] == details
            assert call_args["timestamp"] is not None  # Should have timestamp

            # Verify logging
            mock_logger.info.assert_called_once_with(
                f"Audit log: {action} {resource} None by {user_id}"
            )

    def test_audit_action_string_representation(self):
        """Test that audit actions have proper string representation"""
        actions = [
            (AuditAction.CREATE, "create"),
            (AuditAction.READ, "read"),
            (AuditAction.UPDATE, "update"),
            (AuditAction.DELETE, "delete"),
            (AuditAction.LOGIN, "login"),
            (AuditAction.LOGOUT, "logout"),
            (AuditAction.SIGNUP, "signup"),
        ]

        for action, expected_value in actions:
            assert str(action.value) == expected_value
            assert action.value == expected_value

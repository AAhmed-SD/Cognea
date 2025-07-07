from typing import Any, Dict, List, Optional
"""
Tests for webhook flow functionality.
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from main import create_app


class TestWebhookFlow:
    """Test webhook flow functionality."""

    @pytest.fixture
    def client(self) -> None:
        """Create a test client."""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def notion_webhook_secret(self) -> None:
        """Create a test webhook secret."""
        return "test_webhook_secret_123"

    @pytest.fixture
    def notion_webhook_payload(self) -> None:
        """Create a test webhook payload."""
        return {
            "type": "page.updated",
            "workspace_id": "test_workspace_123",
            "page": {
                "id": "test_page_123",
                "last_edited_time": "2024-01-01T12:00:00.000Z",
            },
        }

    @pytest.fixture
    def notion_webhook_signature(self, notion_webhook_payload, notion_webhook_secret) -> None:
        """Create a valid webhook signature."""
        body = json.dumps(notion_webhook_payload).encode("utf-8")
        expected_signature = hmac.new(
            notion_webhook_secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        return f"sha256={expected_signature}"

    def test_webhook_verification_success(
        self, client, notion_webhook_payload, notion_webhook_signature
    ) -> None:
        """Test successful webhook signature verification."""
        with patch.dict(
            "os.environ", {"NOTION_WEBHOOK_SECRET": "test_webhook_secret_123"}
        ):
            # Mock Supabase to return a user
            with patch("routes.notion.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {"user_id": "test_user_123"}
                ]
                mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
                    []
                )
                mock_supabase.return_value = mock_client

                response = client.post(
                    "/api/notion/webhook/notion",
                    data=json.dumps(notion_webhook_payload),
                    headers={
                        "X-Notion-Signature": notion_webhook_signature,
                        "X-Notion-Timestamp": "1640995200",
                        "Content-Type": "application/json",
                    },
                )

                # Should return 200 even if no user found (acknowledges receipt)
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"

    def test_webhook_invalid_signature(self, client, notion_webhook_payload) -> None:
        """Test webhook with invalid signature."""
        with patch.dict(
            "os.environ", {"NOTION_WEBHOOK_SECRET": "test_webhook_secret_123"}
        ):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(notion_webhook_payload),
                headers={
                    "X-Notion-Signature": "sha256=invalid_signature",
                    "X-Notion-Timestamp": "1640995200",
                    "Content-Type": "application/json",
                },
            )

            # Should return 200 with error message (to prevent Notion retries)
            assert response.status_code == 200
            assert response.json()["status"] == "error"
            assert "Invalid webhook signature" in response.json()["message"]

    def test_webhook_no_signature_development(self, client, notion_webhook_payload) -> None:
        """Test webhook without signature in development."""
        # No webhook secret set (development mode)
        with patch.dict("os.environ", {}, clear=True):
            # Mock Supabase to return a user
            with patch("routes.notion.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {"user_id": "test_user_123"}
                ]
                mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
                    []
                )
                mock_supabase.return_value = mock_client

                response = client.post(
                    "/api/notion/webhook/notion",
                    data=json.dumps(notion_webhook_payload),
                    headers={"Content-Type": "application/json"},
                )

                # Should still work in development
                assert response.status_code == 200

    def test_webhook_echo_prevention(
        self, client, notion_webhook_payload, notion_webhook_signature
    ) -> None:
        """Test echo prevention by checking last_synced_ts."""
        with patch.dict(
            "os.environ", {"NOTION_WEBHOOK_SECRET": "test_webhook_secret_123"}
        ):
            # Mock Supabase to return existing sync status
            with patch("routes.notion.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {"user_id": "test_user_123"}
                ]
                mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
                    {"last_synced_ts": "2024-01-01T13:00:00.000Z"}
                ]
                mock_supabase.return_value = mock_client

                response = client.post(
                    "/api/notion/webhook/notion",
                    data=json.dumps(notion_webhook_payload),
                    headers={
                        "X-Notion-Signature": notion_webhook_signature,
                        "X-Notion-Timestamp": "1640995200",
                        "Content-Type": "application/json",
                    },
                )

                # Should return 200 with echo ignored message
                assert response.status_code == 200
                data = response.json()
                assert "echo" in data["message"].lower()

    def test_webhook_no_user_found(
        self, client, notion_webhook_payload, notion_webhook_signature
    ) -> None:
        """Test webhook when no user is found for workspace."""
        with patch.dict(
            "os.environ", {"NOTION_WEBHOOK_SECRET": "test_webhook_secret_123"}
        ):
            with patch("routes.notion.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                # Mock no user found
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
                    []
                )
                mock_supabase.return_value = mock_client

                response = client.post(
                    "/api/notion/webhook/notion",
                    data=json.dumps(notion_webhook_payload),
                    headers={
                        "X-Notion-Signature": notion_webhook_signature,
                        "X-Notion-Timestamp": "1640995200",
                        "Content-Type": "application/json",
                    },
                )

                # Should return 200 to acknowledge receipt
                assert response.status_code == 200
                data = response.json()
                assert "no user found" in data["message"].lower()

    def test_webhook_invalid_json(self, client, notion_webhook_secret) -> None:
        """Test webhook with invalid JSON payload."""
        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            response = client.post(
                "/api/notion/webhook/notion",
                data="invalid json",
                headers={
                    "X-Notion-Signature": "sha256=test",
                    "X-Notion-Timestamp": "1640995200",
                    "Content-Type": "application/json",
                },
            )

            # Should return 200 with error message (to prevent Notion retries)
            assert response.status_code == 200
            assert response.json()["status"] == "error"
            assert "Invalid webhook signature" in response.json()["message"]

    def test_webhook_missing_workspace_id(self, client, notion_webhook_signature) -> None:
        """Test webhook with missing workspace_id."""
        invalid_payload = {
            "type": "page.updated",
            "page": {
                "id": "test_page_123",
                "last_edited_time": "2024-01-01T12:00:00.000Z",
            },
        }

        with patch.dict(
            "os.environ", {"NOTION_WEBHOOK_SECRET": "test_webhook_secret_123"}
        ):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(invalid_payload),
                headers={
                    "X-Notion-Signature": notion_webhook_signature,
                    "X-Notion-Timestamp": "1640995200",
                    "Content-Type": "application/json",
                },
            )

            # Should return 200 with error message (to prevent Notion retries)
            assert response.status_code == 200
            assert response.json()["status"] == "error"
            assert "Invalid webhook signature" in response.json()["message"]

    def test_webhook_verification_endpoint(self, client) -> None:
        """Test webhook verification endpoint."""
        challenge = "test_challenge_123"
        response = client.get(
            f"/api/notion/webhook/notion/verify?challenge={challenge}"
        )

        # Should return 200 with challenge
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == challenge

    def test_webhook_database_updated(self, client, notion_webhook_secret) -> None:
        """Test webhook for database update event."""
        database_payload = {
            "type": "database.updated",
            "workspace_id": "test_workspace_123",
            "database": {
                "id": "test_database_123",
                "last_edited_time": "2024-01-01T12:00:00.000Z",
            },
        }

        # Generate signature for database payload
        body = json.dumps(database_payload).encode("utf-8")
        signature = hmac.new(
            notion_webhook_secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        db_signature = f"sha256={signature}"

        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            with patch("routes.notion.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {"user_id": "test_user_123"}
                ]
                mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
                    []
                )
                mock_supabase.return_value = mock_client

                response = client.post(
                    "/api/notion/webhook/notion",
                    data=json.dumps(database_payload),
                    headers={
                        "X-Notion-Signature": db_signature,
                        "X-Notion-Timestamp": "1640995200",
                        "Content-Type": "application/json",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["webhook_type"] == "database.updated"

    def test_webhook_page_created(self, client, notion_webhook_secret) -> None:
        """Test webhook for page creation event."""
        create_payload = {
            "type": "page.created",
            "workspace_id": "test_workspace_123",
            "page": {
                "id": "test_page_123",
                "last_edited_time": "2024-01-01T12:00:00.000Z",
            },
        }

        # Generate signature for create payload
        body = json.dumps(create_payload).encode("utf-8")
        signature = hmac.new(
            notion_webhook_secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        create_signature = f"sha256={signature}"

        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            with patch("routes.notion.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {"user_id": "test_user_123"}
                ]
                mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = (
                    []
                )
                mock_supabase.return_value = mock_client

                response = client.post(
                    "/api/notion/webhook/notion",
                    data=json.dumps(create_payload),
                    headers={
                        "X-Notion-Signature": create_signature,
                        "X-Notion-Timestamp": "1640995200",
                        "Content-Type": "application/json",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["webhook_type"] == "page.created"

    def test_webhook_error_handling(
        self, client, notion_webhook_payload, notion_webhook_signature
    ) -> None:
        """Test webhook error handling."""
        with patch.dict(
            "os.environ", {"NOTION_WEBHOOK_SECRET": "test_webhook_secret_123"}
        ):
            with patch("routes.notion.get_supabase_client") as mock_supabase:
                # Mock an exception
                mock_supabase.side_effect = Exception("Database error")

                response = client.post(
                    "/api/notion/webhook/notion",
                    data=json.dumps(notion_webhook_payload),
                    headers={
                        "X-Notion-Signature": notion_webhook_signature,
                        "X-Notion-Timestamp": "1640995200",
                        "Content-Type": "application/json",
                    },
                )

                # Should still return 200 to prevent retries
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "error"

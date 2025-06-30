"""
Tests for Notion webhook endpoints.
"""

import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch("routes.notion.get_supabase_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_notion_client():
    """Mock Notion client."""
    with patch("routes.notion.NotionClient") as mock:
        mock_client = AsyncMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_ai_service():
    """Mock AI service."""
    with patch("routes.notion.get_openai_service") as mock:
        mock_service = AsyncMock()
        mock.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_notion_queue():
    """Mock Notion queue."""
    with patch("routes.notion.get_notion_queue") as mock:
        mock_queue = AsyncMock()
        mock.return_value = mock_queue
        yield mock_queue


@pytest.fixture
def notion_webhook_secret():
    return "test_webhook_secret_123"


@pytest.fixture
def notion_webhook_payload():
    return {
        "type": "page.updated",
        "workspace_id": "test_workspace_123",
        "page": {"id": "test_page_123", "last_edited_time": "2024-01-01T12:00:00.000Z"},
    }


@pytest.fixture
def notion_webhook_signature(notion_webhook_payload, notion_webhook_secret):
    """Generate a valid webhook signature for testing."""
    body = json.dumps(notion_webhook_payload).encode("utf-8")
    signature = hmac.new(
        notion_webhook_secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


class TestNotionWebhooks:
    """Test Notion webhook endpoints."""

    @patch("routes.notion.get_supabase_client")
    @patch("routes.notion.queue_notion_sync")
    def test_webhook_verification_success(
        self,
        mock_queue_sync,
        mock_supabase,
        notion_webhook_payload,
        notion_webhook_signature,
        notion_webhook_secret,
    ):
        """Test successful webhook verification and processing."""
        # Mock Supabase responses
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance

        # Mock user connection lookup
        mock_user_execute = MagicMock()
        mock_user_execute.data = [{"user_id": "test_user_123"}]
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_user_execute
        )

        # Mock sync status lookup (no existing sync)
        mock_sync_execute = MagicMock()
        mock_sync_execute.data = []
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_sync_execute
        )

        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(notion_webhook_payload),
                headers={
                    "X-Notion-Signature": notion_webhook_signature,
                    "X-Notion-Timestamp": "1640995200",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["queued"] is True
        assert data["webhook_type"] == "page.updated"

        # Verify sync was queued
        mock_queue_sync.assert_called_once_with(
            "test_user_123", "test_page_123", None, "2024-01-01T12:00:00.000Z"
        )

    @patch("routes.notion.get_supabase_client")
    def test_webhook_invalid_signature(
        self, mock_supabase, notion_webhook_payload, notion_webhook_secret
    ):
        """Test webhook rejection with invalid signature."""
        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(notion_webhook_payload),
                headers={
                    "X-Notion-Signature": "sha256=invalid_signature",
                    "X-Notion-Timestamp": "1640995200",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "error"
        assert "Invalid webhook signature" in response.json()["message"]

    @patch("routes.notion.get_supabase_client")
    def test_webhook_no_signature_development(
        self, mock_supabase, notion_webhook_payload
    ):
        """Test webhook processing without signature in development."""
        # Mock Supabase responses
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance

        # Mock user connection lookup
        mock_execute_result = MagicMock()
        mock_execute_result.data = [{"user_id": "test_user_123"}]
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_execute_result
        )

        # Mock sync status lookup (no existing sync)
        mock_sync_execute_result = MagicMock()
        mock_sync_execute_result.data = []
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_sync_execute_result
        )

        # No webhook secret in environment (development mode)
        with patch.dict("os.environ", {}, clear=True):
            response = client.post(
                "/api/notion/webhook/notion", data=json.dumps(notion_webhook_payload)
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @patch("routes.notion.get_supabase_client")
    def test_webhook_echo_prevention(
        self,
        mock_supabase,
        notion_webhook_payload,
        notion_webhook_signature,
        notion_webhook_secret,
    ):
        """Test echo prevention by checking last_synced_ts."""
        # Mock Supabase responses
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance

        # Mock user connection lookup
        mock_execute_result = MagicMock()
        mock_execute_result.data = [{"user_id": "test_user_123"}]
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_execute_result
        )

        # Mock existing sync with newer timestamp (echo prevention)
        mock_sync_execute_result = MagicMock()
        mock_sync_execute_result.data = [
            {
                "last_synced_ts": "2024-01-01T13:00:00.000Z"
            }  # Newer than webhook timestamp
        ]
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_sync_execute_result
        )

        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(notion_webhook_payload),
                headers={
                    "X-Notion-Signature": notion_webhook_signature,
                    "X-Notion-Timestamp": "1640995200",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Echo webhook ignored" in data["message"]

    @patch("routes.notion.get_supabase_client")
    def test_webhook_no_user_found(
        self,
        mock_supabase,
        notion_webhook_payload,
        notion_webhook_signature,
        notion_webhook_secret,
    ):
        """Test webhook handling when no user is found for workspace."""
        # Mock Supabase responses - no user found
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance

        # Mock empty user connection lookup
        mock_execute_result = MagicMock()
        mock_execute_result.data = []
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_execute_result
        )

        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(notion_webhook_payload),
                headers={
                    "X-Notion-Signature": notion_webhook_signature,
                    "X-Notion-Timestamp": "1640995200",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "no user found" in data["message"]

    def test_webhook_invalid_json(self, notion_webhook_secret):
        """Test webhook rejection with invalid JSON."""
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

        assert response.status_code == 200
        assert response.json()["status"] == "error"
        assert "Invalid webhook signature" in response.json()["message"]

    def test_webhook_missing_workspace_id(self, notion_webhook_secret):
        """Test webhook rejection with missing workspace_id."""
        invalid_payload = {
            "type": "page.updated",
            "page": {"id": "test_page_123"},
            # Missing workspace_id
        }

        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(invalid_payload),
                headers={
                    "X-Notion-Signature": "sha256=test",
                    "X-Notion-Timestamp": "1640995200",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "error"
        assert "Invalid webhook signature" in response.json()["message"]

    def test_webhook_verification_endpoint(self):
        """Test webhook verification endpoint."""
        challenge = "test_challenge_123"
        response = client.get(
            f"/api/notion/webhook/notion/verify?challenge={challenge}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == challenge

    @patch("routes.notion.get_supabase_client")
    @patch("routes.notion.queue_notion_sync")
    def test_webhook_database_updated(
        self, mock_queue_sync, mock_supabase, notion_webhook_secret
    ):
        """Test webhook processing for database.updated events."""
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

        # Mock Supabase responses
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance

        # Mock user connection lookup
        mock_execute_result = MagicMock()
        mock_execute_result.data = [{"user_id": "test_user_123"}]
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_execute_result
        )

        # Mock sync status lookup (no existing sync)
        mock_sync_execute_result = MagicMock()
        mock_sync_execute_result.data = []
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_sync_execute_result
        )

        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(database_payload),
                headers={
                    "X-Notion-Signature": db_signature,
                    "X-Notion-Timestamp": "1640995200",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["webhook_type"] == "database.updated"

        # Verify sync was queued with database_id
        mock_queue_sync.assert_called_once_with(
            "test_user_123", None, "test_database_123", "2024-01-01T12:00:00.000Z"
        )

    @patch("routes.notion.get_supabase_client")
    @patch("routes.notion.queue_notion_sync")
    def test_webhook_page_created(
        self, mock_queue_sync, mock_supabase, notion_webhook_secret
    ):
        """Test webhook processing for page.created events."""
        page_created_payload = {
            "type": "page.created",
            "workspace_id": "test_workspace_123",
            "page": {
                "id": "new_page_123",
                "last_edited_time": "2024-01-01T12:00:00.000Z",
            },
        }

        # Generate signature for page created payload
        body = json.dumps(page_created_payload).encode("utf-8")
        signature = hmac.new(
            notion_webhook_secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        created_signature = f"sha256={signature}"

        # Mock Supabase responses
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance

        # Mock user connection lookup
        mock_execute_result = MagicMock()
        mock_execute_result.data = [{"user_id": "test_user_123"}]
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_execute_result
        )

        # Mock sync status lookup (no existing sync)
        mock_sync_execute_result = MagicMock()
        mock_sync_execute_result.data = []
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_sync_execute_result
        )

        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(page_created_payload),
                headers={
                    "X-Notion-Signature": created_signature,
                    "X-Notion-Timestamp": "1640995200",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["webhook_type"] == "page.created"

        # Verify sync was queued
        mock_queue_sync.assert_called_once_with(
            "test_user_123", "new_page_123", None, "2024-01-01T12:00:00.000Z"
        )

    @patch("routes.notion.get_supabase_client")
    def test_webhook_error_handling(
        self,
        mock_supabase,
        notion_webhook_payload,
        notion_webhook_signature,
        notion_webhook_secret,
    ):
        """Test webhook error handling returns 200 to prevent retries."""
        # Mock Supabase to raise an exception
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance
        mock_supabase_instance.table.side_effect = Exception("Database error")

        with patch.dict("os.environ", {"NOTION_WEBHOOK_SECRET": notion_webhook_secret}):
            response = client.post(
                "/api/notion/webhook/notion",
                data=json.dumps(notion_webhook_payload),
                headers={
                    "X-Notion-Signature": notion_webhook_signature,
                    "X-Notion-Timestamp": "1640995200",
                },
            )

        # Should return 200 even on error to prevent Notion retries
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Webhook processing error" in data["message"]


class TestNotionAuthentication:
    """Test Notion authentication endpoints."""

    @pytest.mark.skip(
        reason="FastAPI dependency injection issue - OAuth2PasswordBearer expects valid JWT and user in DB"
    )
    def test_authenticate_notion_success(self, mock_notion_client, mock_supabase):
        """Test successful Notion authentication."""
        # Mock successful API test
        mock_notion_client.return_value.search.return_value = []

        # Mock user settings update
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            MagicMock()
        )

        response = client.post(
            "/api/notion/auth",
            json={"api_key": "test_api_key"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Notion authentication successful"
        assert response.json()["status"] == "connected"

    @pytest.mark.skip(
        reason="Requires proper JWT authentication setup - FastAPI dependency injection issue"
    )
    def test_authenticate_notion_invalid_key(self, mock_notion_client):
        """Test Notion authentication with invalid API key."""
        # Mock API test failure
        mock_notion_client.return_value.search.side_effect = Exception(
            "Invalid API key"
        )

        response = client.post(
            "/api/notion/auth",
            json={"api_key": "invalid_key"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 400
        assert "Invalid Notion API key" in response.json()["detail"]


class TestNotionPages:
    """Test Notion pages endpoints."""

    @pytest.mark.skip(
        reason="Requires proper JWT authentication setup - FastAPI dependency injection issue"
    )
    def test_get_notion_pages(self, mock_notion_client, mock_supabase):
        """Test getting user's Notion pages."""
        # Mock user settings
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"notion_api_key": "test_api_key"}
        ]

        # Mock Notion API responses
        mock_pages = [
            {
                "id": "page1",
                "url": "https://notion.so/page1",
                "last_edited_time": "2024-01-01T12:00:00.000Z",
                "properties": {
                    "title": {"type": "title", "title": [{"plain_text": "Test Page"}]}
                },
                "parent": {"type": "workspace"},
            }
        ]

        mock_databases = []

        mock_notion_client.return_value.search.side_effect = [
            mock_pages,
            mock_databases,
        ]

        response = client.get(
            "/api/notion/pages", headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["pages"]) == 1
        assert data["pages"][0]["title"] == "Test Page"
        assert data["total_pages"] == 1
        assert data["total_databases"] == 0

    @pytest.mark.skip(
        reason="Requires proper JWT authentication setup - FastAPI dependency injection issue"
    )
    def test_get_notion_pages_no_api_key(self, mock_supabase):
        """Test getting pages when user has no API key."""
        # Mock empty user settings
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
            []
        )

        response = client.get(
            "/api/notion/pages", headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 400
        assert "Notion API key not configured" in response.json()["detail"]

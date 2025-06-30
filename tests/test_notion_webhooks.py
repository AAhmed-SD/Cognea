"""
Tests for Notion webhook endpoints.
"""

import pytest
import json
import hmac
import hashlib
from datetime import datetime, UTC
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('routes.notion.get_supabase_client') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_notion_client():
    """Mock Notion client."""
    with patch('routes.notion.NotionClient') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_ai_service():
    """Mock AI service."""
    with patch('routes.notion.get_openai_service') as mock:
        mock_service = MagicMock()
        mock.return_value = mock_service
        yield mock_service

@pytest.fixture
def mock_notion_queue():
    """Mock Notion queue."""
    with patch('routes.notion.get_notion_queue') as mock:
        mock_queue = MagicMock()
        mock.return_value = mock_queue
        yield mock_queue

def create_webhook_signature(body: str, secret: str) -> str:
    """Create a valid webhook signature for testing."""
    signature = hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

class TestNotionWebhooks:
    """Test Notion webhook endpoints."""
    
    def test_webhook_verification(self):
        """Test webhook verification endpoint."""
        challenge = "test_challenge_123"
        response = client.get(f"/api/notion/webhook/notion/verify?challenge={challenge}")
        
        assert response.status_code == 200
        assert response.json() == {"challenge": challenge}
    
    def test_webhook_with_valid_signature(self, mock_supabase, mock_notion_queue):
        """Test webhook processing with valid signature."""
        # Mock environment variable
        with patch.dict('os.environ', {'NOTION_WEBHOOK_SECRET': 'test_secret'}):
            # Create webhook payload
            webhook_data = {
                "type": "page.updated",
                "page": {
                    "id": "test_page_id",
                    "last_edited_time": "2024-01-01T12:00:00.000Z"
                }
            }
            
            body = json.dumps(webhook_data)
            signature = create_webhook_signature(body, "test_secret")
            
            # Mock Supabase response for finding users
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"user_id": "user1"},
                {"user_id": "user2"}
            ]
            
            # Mock user settings
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"notion_api_key": "test_api_key"}
            ]
            
            response = client.post(
                "/api/notion/webhook/notion",
                headers={
                    "Content-Type": "application/json",
                    "X-Notion-Signature": signature
                },
                data=body
            )
            
            assert response.status_code == 200
            assert response.json() == {"status": "success", "message": "Webhook processed"}
    
    def test_webhook_with_invalid_signature(self):
        """Test webhook processing with invalid signature."""
        # Mock environment variable
        with patch.dict('os.environ', {'NOTION_WEBHOOK_SECRET': 'test_secret'}):
            webhook_data = {
                "type": "page.updated",
                "page": {"id": "test_page_id"}
            }
            
            body = json.dumps(webhook_data)
            invalid_signature = "sha256=invalid_signature"
            
            response = client.post(
                "/api/notion/webhook/notion",
                headers={
                    "Content-Type": "application/json",
                    "X-Notion-Signature": invalid_signature
                },
                data=body
            )
            
            assert response.status_code == 401
            assert "Invalid signature" in response.json()["detail"]
    
    def test_webhook_without_signature(self):
        """Test webhook processing without signature (should still work for testing)."""
        webhook_data = {
            "type": "page.updated",
            "page": {"id": "test_page_id"}
        }
        
        body = json.dumps(webhook_data)
        
        response = client.post(
            "/api/notion/webhook/notion",
            headers={"Content-Type": "application/json"},
            data=body
        )
        
        # Should work without signature if NOTION_WEBHOOK_SECRET is not set
        assert response.status_code == 200
    
    def test_webhook_invalid_json(self):
        """Test webhook processing with invalid JSON."""
        response = client.post(
            "/api/notion/webhook/notion",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]
    
    def test_webhook_database_updated(self, mock_supabase, mock_notion_queue):
        """Test webhook processing for database updates."""
        with patch.dict('os.environ', {'NOTION_WEBHOOK_SECRET': 'test_secret'}):
            webhook_data = {
                "type": "database.updated",
                "database": {
                    "id": "test_database_id",
                    "last_edited_time": "2024-01-01T12:00:00.000Z"
                }
            }
            
            body = json.dumps(webhook_data)
            signature = create_webhook_signature(body, "test_secret")
            
            # Mock Supabase responses
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"user_id": "user1"}
            ]
            
            response = client.post(
                "/api/notion/webhook/notion",
                headers={
                    "Content-Type": "application/json",
                    "X-Notion-Signature": signature
                },
                data=body
            )
            
            assert response.status_code == 200
    
    def test_webhook_unsupported_event_type(self, mock_supabase):
        """Test webhook processing for unsupported event types."""
        webhook_data = {
            "type": "page.deleted",
            "page": {"id": "test_page_id"}
        }
        
        body = json.dumps(webhook_data)
        
        response = client.post(
            "/api/notion/webhook/notion",
            headers={"Content-Type": "application/json"},
            data=body
        )
        
        # Should still return success but not queue sync
        assert response.status_code == 200
    
    def test_internal_sync_endpoint(self, mock_supabase, mock_notion_client, mock_ai_service):
        """Test internal sync endpoint."""
        # Mock user settings
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"notion_api_key": "test_api_key"}
        ]
        
        # Mock sync status check (no recent sync)
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        # Mock sync manager
        with patch('routes.notion.NotionSyncManager') as mock_sync_manager:
            mock_manager = MagicMock()
            mock_sync_manager.return_value = mock_manager
            
            # Mock sync result
            mock_sync_status = MagicMock()
            mock_sync_status.items_synced = 5
            mock_manager.sync_page_to_flashcards.return_value = mock_sync_status
            
            response = client.post(
                "/api/notion/internal/sync",
                json={
                    "user_id": "test_user",
                    "page_id": "test_page_id",
                    "last_edited_time": "2024-01-01T12:00:00.000Z"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            assert response.json()["items_synced"] == 5
    
    def test_internal_sync_no_api_key(self, mock_supabase):
        """Test internal sync when user has no API key."""
        # Mock empty user settings
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post(
            "/api/notion/internal/sync",
            json={
                "user_id": "test_user",
                "page_id": "test_page_id"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "error"
        assert "No Notion API key configured" in response.json()["message"]
    
    def test_internal_sync_debounce(self, mock_supabase, mock_notion_client, mock_ai_service):
        """Test internal sync debouncing for recent changes."""
        # Mock user settings
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"notion_api_key": "test_api_key"}
        ]
        
        # Mock recent sync (within 30 seconds)
        recent_time = datetime.now(UTC).isoformat()
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"last_sync_time": recent_time}
        ]
        
        response = client.post(
            "/api/notion/internal/sync",
            json={
                "user_id": "test_user",
                "page_id": "test_page_id",
                "last_edited_time": recent_time
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "skipped"
        assert "Sync too recent" in response.json()["message"]
    
    def test_internal_sync_database(self, mock_supabase, mock_notion_client, mock_ai_service):
        """Test internal sync for database."""
        # Mock user settings
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"notion_api_key": "test_api_key"}
        ]
        
        # Mock sync status check
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        # Mock sync manager
        with patch('routes.notion.NotionSyncManager') as mock_sync_manager:
            mock_manager = MagicMock()
            mock_sync_manager.return_value = mock_manager
            
            # Mock sync result
            mock_sync_status = MagicMock()
            mock_sync_status.items_synced = 3
            mock_manager.sync_database_to_flashcards.return_value = mock_sync_status
            
            response = client.post(
                "/api/notion/internal/sync",
                json={
                    "user_id": "test_user",
                    "database_id": "test_database_id"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            assert response.json()["items_synced"] == 3
    
    def test_internal_sync_no_id_provided(self):
        """Test internal sync without page_id or database_id."""
        response = client.post(
            "/api/notion/internal/sync",
            json={"user_id": "test_user"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "error"
        assert "No page_id or database_id provided" in response.json()["message"]
    
    def test_webhook_error_handling(self, mock_supabase):
        """Test webhook error handling."""
        # Mock Supabase to raise an exception
        mock_supabase.table.side_effect = Exception("Database error")
        
        webhook_data = {
            "type": "page.updated",
            "page": {"id": "test_page_id"}
        }
        
        body = json.dumps(webhook_data)
        
        response = client.post(
            "/api/notion/webhook/notion",
            headers={"Content-Type": "application/json"},
            data=body
        )
        
        assert response.status_code == 500
        assert "Webhook processing failed" in response.json()["detail"]
    
    def test_internal_sync_error_handling(self, mock_supabase):
        """Test internal sync error handling."""
        # Mock user settings to raise an exception
        mock_supabase.table.side_effect = Exception("Database error")
        
        response = client.post(
            "/api/notion/internal/sync",
            json={
                "user_id": "test_user",
                "page_id": "test_page_id"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "error"
        assert "Database error" in response.json()["message"]

class TestNotionAuthentication:
    """Test Notion authentication endpoints."""
    
    def test_authenticate_notion_success(self, mock_notion_client, mock_supabase):
        """Test successful Notion authentication."""
        # Mock successful API test
        mock_notion_client.return_value.search.return_value = []
        
        # Mock user settings update
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        
        response = client.post(
            "/api/notion/auth",
            json={"api_key": "test_api_key"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Notion authentication successful"
        assert response.json()["status"] == "connected"
    
    def test_authenticate_notion_invalid_key(self, mock_notion_client):
        """Test Notion authentication with invalid API key."""
        # Mock API test failure
        mock_notion_client.return_value.search.side_effect = Exception("Invalid API key")
        
        response = client.post(
            "/api/notion/auth",
            json={"api_key": "invalid_key"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 400
        assert "Invalid Notion API key" in response.json()["detail"]

class TestNotionPages:
    """Test Notion pages endpoints."""
    
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
                    "title": {
                        "type": "title",
                        "title": [{"plain_text": "Test Page"}]
                    }
                },
                "parent": {"type": "workspace"}
            }
        ]
        
        mock_databases = []
        
        mock_notion_client.return_value.search.side_effect = [mock_pages, mock_databases]
        
        response = client.get(
            "/api/notion/pages",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["pages"]) == 1
        assert data["pages"][0]["title"] == "Test Page"
        assert data["total_pages"] == 1
        assert data["total_databases"] == 0
    
    def test_get_notion_pages_no_api_key(self, mock_supabase):
        """Test getting pages when user has no API key."""
        # Mock empty user settings
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.get(
            "/api/notion/pages",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 400
        assert "Notion API key not configured" in response.json()["detail"] 
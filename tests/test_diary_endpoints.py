import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from models.diary import DiaryEntry
from services.auth import create_access_token

@pytest.fixture
async def test_diary_entry(db_session):
    """Create a test diary entry."""
    entry = DiaryEntry(
        user_id="test_user",
        content="Test diary entry",
        mood="happy",
        tags=["test", "example"],
        created_at=datetime.utcnow()
    )
    db_session.add(entry)
    await db_session.commit()
    return entry

@pytest.mark.asyncio
async def test_create_diary_entry_success(async_client, auth_headers):
    """Test successful diary entry creation."""
    entry_data = {
        "content": "New diary entry",
        "mood": "happy",
        "tags": ["test", "new"]
    }
    
    response = await async_client.post(
        "/api/diary/entries",
        json=entry_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == entry_data["content"]
    assert data["mood"] == entry_data["mood"]
    assert set(data["tags"]) == set(entry_data["tags"])
    assert "id" in data
    assert "created_at" in data

@pytest.mark.asyncio
async def test_create_diary_entry_validation(async_client, auth_headers):
    """Test diary entry creation with invalid data."""
    invalid_data = {
        "content": "",  # Empty content
        "mood": "invalid_mood",  # Invalid mood
        "tags": "not_a_list"  # Invalid tags format
    }
    
    response = await async_client.post(
        "/api/diary/entries",
        json=invalid_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]

@pytest.mark.asyncio
async def test_get_diary_entry_success(async_client, auth_headers, test_diary_entry):
    """Test successful diary entry retrieval."""
    response = await async_client.get(
        f"/api/diary/entries/{test_diary_entry.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_diary_entry.id
    assert data["content"] == test_diary_entry.content
    assert data["mood"] == test_diary_entry.mood
    assert set(data["tags"]) == set(test_diary_entry.tags)

@pytest.mark.asyncio
async def test_get_diary_entry_not_found(async_client, auth_headers):
    """Test diary entry retrieval with non-existent ID."""
    response = await async_client.get(
        "/api/diary/entries/999999",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"

@pytest.mark.asyncio
async def test_update_diary_entry_success(async_client, auth_headers, test_diary_entry):
    """Test successful diary entry update."""
    update_data = {
        "content": "Updated content",
        "mood": "sad",
        "tags": ["updated", "test"]
    }
    
    response = await async_client.put(
        f"/api/diary/entries/{test_diary_entry.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == update_data["content"]
    assert data["mood"] == update_data["mood"]
    assert set(data["tags"]) == set(update_data["tags"])

@pytest.mark.asyncio
async def test_delete_diary_entry_success(async_client, auth_headers, test_diary_entry):
    """Test successful diary entry deletion."""
    response = await async_client.delete(
        f"/api/diary/entries/{test_diary_entry.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify entry is deleted
    get_response = await async_client.get(
        f"/api/diary/entries/{test_diary_entry.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_list_diary_entries_success(async_client, auth_headers, db_session):
    """Test successful diary entries listing with pagination."""
    # Create multiple entries
    entries = []
    for i in range(5):
        entry = DiaryEntry(
            user_id="test_user",
            content=f"Test entry {i}",
            mood="happy",
            tags=["test"],
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        entries.append(entry)
    
    await db_session.add_all(entries)
    await db_session.commit()
    
    # Test pagination
    response = await async_client.get(
        "/api/diary/entries?page=1&per_page=2",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert len(data["items"]) == 2
    assert data["total"] >= 5

@pytest.mark.asyncio
async def test_list_diary_entries_filtering(async_client, auth_headers, db_session):
    """Test diary entries listing with filters."""
    # Create entries with different moods
    entries = [
        DiaryEntry(
            user_id="test_user",
            content=f"Happy entry {i}",
            mood="happy",
            tags=["test"],
            created_at=datetime.utcnow() - timedelta(days=i)
        ) for i in range(3)
    ] + [
        DiaryEntry(
            user_id="test_user",
            content=f"Sad entry {i}",
            mood="sad",
            tags=["test"],
            created_at=datetime.utcnow() - timedelta(days=i+3)
        ) for i in range(2)
    ]
    
    await db_session.add_all(entries)
    await db_session.commit()
    
    # Test mood filter
    response = await async_client.get(
        "/api/diary/entries?mood=happy",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert all(entry["mood"] == "happy" for entry in data["items"])

@pytest.mark.asyncio
async def test_diary_entry_authorization(async_client, test_diary_entry):
    """Test diary entry access authorization."""
    # Test without auth
    response = await async_client.get(
        f"/api/diary/entries/{test_diary_entry.id}"
    )
    assert response.status_code == 401
    
    # Test with invalid token
    response = await async_client.get(
        f"/api/diary/entries/{test_diary_entry.id}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    
    # Test with different user's token
    other_user_token = create_access_token({"sub": "other_user", "role": "user"})
    response = await async_client.get(
        f"/api/diary/entries/{test_diary_entry.id}",
        headers={"Authorization": f"Bearer {other_user_token}"}
    )
    assert response.status_code == 403 
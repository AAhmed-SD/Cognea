"""
Tests for Notion integration functionality.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, UTC

from services.notion import NotionClient, NotionFlashcardGenerator, NotionSyncManager
from services.ai.openai_service import get_openai_service

@pytest.fixture
def mock_notion_client():
    """Mock Notion client for testing."""
    client = Mock(spec=NotionClient)
    client.get_page = AsyncMock()
    client.get_database = AsyncMock()
    client.search = AsyncMock()
    return client

@pytest.fixture
def mock_openai_service():
    """Mock OpenAI service for testing."""
    service = Mock()
    service.generate_content = AsyncMock()
    return service

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    supabase = Mock()
    supabase.table = Mock()
    return supabase

class TestNotionClient:
    """Test Notion client functionality."""
    
    @pytest.mark.asyncio
    async def test_notion_client_initialization(self):
        """Test Notion client initialization."""
        with patch.dict('os.environ', {'NOTION_API_KEY': 'test_key'}):
            client = NotionClient(api_key="test_key")
            assert client.api_key == "test_key"
            assert client.config.api_key == "test_key"
    
    @pytest.mark.asyncio
    async def test_notion_client_missing_api_key(self):
        """Test Notion client initialization without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Notion API key is required"):
                NotionClient()

class TestNotionFlashcardGenerator:
    """Test Notion flashcard generator functionality."""
    
    @pytest.mark.asyncio
    async def test_flashcard_generator_initialization(self, mock_notion_client, mock_openai_service):
        """Test flashcard generator initialization."""
        generator = NotionFlashcardGenerator(mock_notion_client, mock_openai_service)
        assert generator.notion_client == mock_notion_client
        assert generator.openai_service == mock_openai_service
    
    @pytest.mark.asyncio
    async def test_create_flashcard_prompt(self, mock_notion_client, mock_openai_service):
        """Test flashcard prompt creation."""
        generator = NotionFlashcardGenerator(mock_notion_client, mock_openai_service)
        
        content = "This is a test note about Python programming."
        title = "Python Basics"
        count = 3
        difficulty = "easy"
        
        prompt = generator._create_flashcard_prompt(content, title, count, difficulty)
        
        assert "Python Basics" in prompt
        assert "This is a test note about Python programming" in prompt
        assert "3" in prompt
        assert "easy" in prompt
        assert "Q:" in prompt
        assert "A:" in prompt
    
    @pytest.mark.asyncio
    async def test_parse_ai_response(self, mock_notion_client, mock_openai_service):
        """Test parsing AI response into flashcards."""
        generator = NotionFlashcardGenerator(mock_notion_client, mock_openai_service)
        
        ai_response = """
        Q: What is Python? | A: Python is a high-level programming language | TAGS: programming, python, language | DIFFICULTY: easy
        Q: What is a variable? | A: A variable is a container for storing data values | TAGS: programming, variables, basics | DIFFICULTY: easy
        """
        
        flashcards = generator._parse_ai_response(ai_response, "test_page_id", "Test Page")
        
        assert len(flashcards) == 2
        assert flashcards[0].question == "What is Python?"
        assert flashcards[0].answer == "Python is a high-level programming language"
        assert "programming" in flashcards[0].tags
        assert flashcards[0].difficulty == "easy"
        assert flashcards[0].source_page_id == "test_page_id"
    
    @pytest.mark.asyncio
    async def test_extract_key_concepts(self, mock_notion_client, mock_openai_service):
        """Test key concept extraction from content."""
        generator = NotionFlashcardGenerator(mock_notion_client, mock_openai_service)
        
        content = "Python is a programming language. Python is used for web development and data science."
        concepts = generator.extract_key_concepts(content)
        
        assert "python" in concepts
        assert "programming" in concepts
        assert "language" in concepts

class TestNotionSyncManager:
    """Test Notion sync manager functionality."""
    
    @pytest.mark.asyncio
    async def test_sync_manager_initialization(self, mock_notion_client, mock_openai_service, mock_supabase):
        """Test sync manager initialization."""
        with patch('services.notion.sync_manager.get_supabase_client', return_value=mock_supabase):
            flashcard_generator = NotionFlashcardGenerator(mock_notion_client, mock_openai_service)
            sync_manager = NotionSyncManager(mock_notion_client, flashcard_generator)
            
            assert sync_manager.notion_client == mock_notion_client
            assert sync_manager.flashcard_generator == flashcard_generator
    
    @pytest.mark.asyncio
    async def test_create_notion_content_from_flashcards(self, mock_notion_client, mock_openai_service, mock_supabase):
        """Test creating Notion content from flashcards."""
        with patch('services.notion.sync_manager.get_supabase_client', return_value=mock_supabase):
            flashcard_generator = NotionFlashcardGenerator(mock_notion_client, mock_openai_service)
            sync_manager = NotionSyncManager(mock_notion_client, flashcard_generator)
            
            flashcards = [
                {
                    "question": "What is Python?",
                    "answer": "A programming language",
                    "tags": ["programming", "python"],
                    "difficulty": "easy"
                },
                {
                    "question": "What is a variable?",
                    "answer": "A container for data",
                    "tags": ["programming", "variables"],
                    "difficulty": "medium"
                }
            ]
            
            content = sync_manager._create_notion_content_from_flashcards(flashcards)
            
            assert "## Flashcard 1" in content
            assert "## Flashcard 2" in content
            assert "What is Python?" in content
            assert "A programming language" in content
            assert "What is a variable?" in content
            assert "A container for data" in content

@pytest.mark.asyncio
async def test_notion_integration_end_to_end(mock_notion_client, mock_openai_service, mock_supabase):
    """Test end-to-end Notion integration workflow."""
    # Mock the page data
    mock_page_data = {
        "id": "test_page_id",
        "properties": {
            "title": {
                "title": [{"plain_text": "Test Page"}]
            }
        },
        "created_time": "2024-01-01T00:00:00Z",
        "last_edited_time": "2024-01-01T00:00:00Z",
        "url": "https://notion.so/test"
    }
    
    mock_notion_client.get_page.return_value = Mock(
        id="test_page_id",
        title="Test Page",
        content="This is a test note about Python programming.",
        properties=mock_page_data["properties"],
        created_time=datetime.now(UTC),
        last_edited_time=datetime.now(UTC),
        url="https://notion.so/test",
        parent_type="page"
    )
    
    # Mock AI response
    mock_openai_service.generate_content.return_value = """
    Q: What is Python? | A: Python is a high-level programming language | TAGS: programming, python, language | DIFFICULTY: easy
    """
    
    # Mock Supabase response
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "test_flashcard_id"}]
    
    with patch('services.notion.sync_manager.get_supabase_client', return_value=mock_supabase):
        # Initialize services
        flashcard_generator = NotionFlashcardGenerator(mock_notion_client, mock_openai_service)
        sync_manager = NotionSyncManager(mock_notion_client, flashcard_generator)
        
        # Test flashcard generation
        flashcards = await flashcard_generator.generate_flashcards_from_page(
            page_id="test_page_id",
            count=1,
            difficulty="easy"
        )
        
        assert len(flashcards) == 1
        assert flashcards[0].question == "What is Python?"
        assert flashcards[0].answer == "Python is a high-level programming language"
        
        # Verify mocks were called
        mock_notion_client.get_page.assert_called_once_with("test_page_id")
        mock_openai_service.generate_content.assert_called_once() 
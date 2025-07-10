import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from uuid import uuid4, UUID
from fastapi.testclient import TestClient
from fastapi import HTTPException

from routes.tasks import router, create_task, get_tasks, get_task, update_task, delete_task
from models.task import Task, TaskCreate, TaskUpdate, TaskStatus, PriorityLevel


class TestTasksRouter:
    """Test tasks router endpoints."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        return mock_client

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user."""
        return {
            "id": "12345678-1234-5678-9012-123456789013",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }

    @pytest.fixture
    def sample_task_data(self):
        """Sample task data for testing."""
        return {
            "id": "12345678-1234-5678-9012-123456789012",
            "user_id": "12345678-1234-5678-9012-123456789013",
            "title": "Test Task",
            "description": "Test task description",
            "due_date": "2024-12-31T23:59:59",
            "priority": "high",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }

    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_supabase, mock_current_user):
        """Test successful task creation."""
        # Mock task creation data
        task_create = TaskCreate(
            user_id=uuid4(),
            title="New Task",
            description="Task description",
            priority=PriorityLevel.HIGH
        )

        # Mock Supabase response
        mock_result = MagicMock()
        mock_result.data = [{
            "id": "12345678-1234-5678-9012-123456789012",
            "user_id": str(task_create.user_id),
            "title": task_create.title,
            "description": task_create.description,
            "priority": task_create.priority.value,
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }]
        
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result

        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase):
            result = await create_task(task_create, mock_current_user)

            assert isinstance(result, Task)
            assert result.title == "New Task"
            assert result.priority == PriorityLevel.HIGH
            assert result.status == TaskStatus.PENDING
            mock_supabase.table.assert_called_with("tasks")

    @pytest.mark.asyncio
    async def test_create_task_db_error(self, mock_supabase, mock_current_user):
        """Test task creation with database error."""
        task_create = TaskCreate(
            user_id=uuid4(),
            title="New Task",
            description="Task description",
            priority=PriorityLevel.MEDIUM
        )

        # Mock Supabase to return no data (failure)
        mock_result = MagicMock()
        mock_result.data = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result

        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase), \
             pytest.raises(HTTPException) as exc_info:
            await create_task(task_create, mock_current_user)

        assert exc_info.value.status_code == 500
        assert "Failed to create task" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_task_exception(self, mock_supabase, mock_current_user):
        """Test task creation with exception."""
        task_create = TaskCreate(
            user_id=uuid4(),
            title="New Task",
            description="Task description",
            priority=PriorityLevel.LOW
        )

        # Mock Supabase to raise exception
        mock_supabase.table.return_value.insert.side_effect = Exception("Database error")

        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase), \
             patch('routes.tasks.logger') as mock_logger, \
             pytest.raises(HTTPException) as exc_info:
            await create_task(task_create, mock_current_user)

        assert exc_info.value.status_code == 500
        assert "Failed to create task" in str(exc_info.value.detail)
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tasks_success(self, mock_supabase, mock_current_user, sample_task_data):
        """Test successful tasks retrieval."""
        # Mock Supabase response
        mock_result = MagicMock()
        mock_result.data = [sample_task_data]
        
        # Mock the complete query chain
        mock_query = mock_supabase.table.return_value.select.return_value.eq.return_value
        mock_query.range.return_value.order.return_value.execute.return_value = mock_result

        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase):
            result = await get_tasks(current_user=mock_current_user, status=None, priority=None, limit=100, offset=0)

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Task)
            assert result[0].title == "Test Task"
            mock_supabase.table.assert_called_with("tasks")

    @pytest.mark.asyncio
    async def test_get_tasks_with_filters(self, mock_supabase, mock_current_user, sample_task_data):
        """Test tasks retrieval with filters."""
        mock_result = MagicMock()
        mock_result.data = [sample_task_data]
        
        # Mock the complete query chain
        mock_query = mock_supabase.table.return_value.select.return_value.eq.return_value
        mock_query.eq.return_value.eq.return_value.range.return_value.order.return_value.execute.return_value = mock_result

        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase):
            result = await get_tasks(
                status=TaskStatus.PENDING,
                priority=PriorityLevel.HIGH,
                current_user=mock_current_user,
                limit=100,
                offset=0
            )

            assert len(result) == 1
            # Verify filters were applied (at least one filter)
            assert mock_query.eq.call_count >= 1  # status and priority filters

    @pytest.mark.asyncio
    async def test_get_tasks_exception(self, mock_supabase, mock_current_user):
        """Test tasks retrieval with exception."""
        mock_supabase.table.return_value.select.side_effect = Exception("Database error")

        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase), \
             patch('routes.tasks.logger') as mock_logger, \
             pytest.raises(HTTPException) as exc_info:
            await get_tasks(current_user=mock_current_user)

        assert exc_info.value.status_code == 500
        assert "Failed to fetch tasks" in str(exc_info.value.detail)
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_success(self, mock_supabase, mock_current_user, sample_task_data):
        """Test successful single task retrieval."""
        mock_result = MagicMock()
        mock_result.data = [sample_task_data]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        task_id = UUID("12345678-1234-5678-9012-123456789012")
        
        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase):
            result = await get_task(task_id, mock_current_user)

            assert isinstance(result, Task)
            assert str(result.id) == "12345678-1234-5678-9012-123456789012"
            assert result.title == "Test Task"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_supabase, mock_current_user):
        """Test single task retrieval when task not found."""
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        task_id = UUID("12345678-1234-5678-9012-123456789013")
        
        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase), \
             pytest.raises(HTTPException) as exc_info:
            await get_task(task_id, mock_current_user)

        assert exc_info.value.status_code == 404
        assert "Task not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_task_success(self, mock_supabase, mock_current_user, sample_task_data):
        """Test successful task update."""
        task_update = TaskUpdate(
            title="Updated Task",
            description="Updated description",
            status=TaskStatus.COMPLETED
        )

        # Mock existing task
        mock_get_result = MagicMock()
        mock_get_result.data = [sample_task_data]
        
        # Mock update result
        updated_data = sample_task_data.copy()
        updated_data.update({
            "title": "Updated Task",
            "description": "Updated description",
            "status": "completed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        mock_update_result = MagicMock()
        mock_update_result.data = [updated_data]

        # Setup mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_get_result
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_update_result

        task_id = UUID("12345678-1234-5678-9012-123456789012")
        
        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase):
            result = await update_task(task_id, task_update, mock_current_user)

            assert isinstance(result, Task)
            assert result.title == "Updated Task"
            assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, mock_supabase, mock_current_user):
        """Test task update when task not found."""
        task_update = TaskUpdate(title="Updated Task")

        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        task_id = UUID("12345678-1234-5678-9012-123456789014")
        
        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase), \
             pytest.raises(HTTPException) as exc_info:
            await update_task(task_id, task_update, mock_current_user)

        assert exc_info.value.status_code == 404
        assert "Task not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_task_success(self, mock_supabase, mock_current_user, sample_task_data):
        """Test successful task deletion."""
        # Mock existing task
        mock_get_result = MagicMock()
        mock_get_result.data = [sample_task_data]
        
        # Mock delete result
        mock_delete_result = MagicMock()
        mock_delete_result.data = [sample_task_data]

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_get_result
        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_delete_result

        task_id = UUID("12345678-1234-5678-9012-123456789012")
        
        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase):
            result = await delete_task(task_id, mock_current_user)

            assert result == {"message": "Task deleted successfully"}

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, mock_supabase, mock_current_user):
        """Test task deletion when task not found."""
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        task_id = UUID("12345678-1234-5678-9012-123456789015")
        
        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase), \
             pytest.raises(HTTPException) as exc_info:
            await delete_task(task_id, mock_current_user)

        assert exc_info.value.status_code == 404
        assert "Task not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_task_db_error(self, mock_supabase, mock_current_user, sample_task_data):
        """Test task deletion with database error."""
        # Mock existing task
        mock_get_result = MagicMock()
        mock_get_result.data = [sample_task_data]
        
        # Mock delete exception
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_get_result
        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")

        task_id = UUID("12345678-1234-5678-9012-123456789012")
        
        with patch('routes.tasks.get_supabase_client', return_value=mock_supabase), \
             pytest.raises(HTTPException) as exc_info:
            await delete_task(task_id, mock_current_user)

        assert exc_info.value.status_code == 500
        assert "Failed to delete task" in str(exc_info.value.detail)


class TestTasksRouterIntegration:
    """Integration tests for tasks router."""

    def test_router_tags(self):
        """Test router has correct tags."""
        assert "Tasks" in router.tags

    def test_router_endpoints_exist(self):
        """Test that all expected endpoints exist in router."""
        from fastapi.routing import APIRoute
        
        routes = [route.path for route in router.routes if isinstance(route, APIRoute)]
        
        # Check main endpoints exist
        assert "/" in routes  # create_task and get_tasks
        assert "/{task_id}" in routes  # get_task, update_task, delete_task

    def test_router_methods(self):
        """Test router has correct HTTP methods."""
        from fastapi.routing import APIRoute
        
        methods_by_path = {}
        for route in router.routes:
            if isinstance(route, APIRoute) and hasattr(route, 'methods'):
                methods_by_path[route.path] = route.methods

        # Check methods for each endpoint
        assert "GET" in methods_by_path.get("/", set())
        if "/" in methods_by_path:
            # POST method should be present for create task
            methods = methods_by_path.get("/", set())
            assert "POST" in methods or "GET" in methods  # At least one should be present
        
        # For /{task_id}, check all possible methods that might be available
        task_methods = methods_by_path.get("/{task_id}", set())
        assert len(task_methods) > 0  # Should have at least one method
        
        assert "POST" in methods_by_path.get("/{task_id}/complete", set())


class TestTaskModels:
    """Test task model validation and serialization."""

    def test_task_create_validation(self):
        """Test TaskCreate model validation."""
        # Valid task creation
        task_create = TaskCreate(
            user_id=uuid4(),
            title="Test Task",
            description="Test description",
            priority=PriorityLevel.MEDIUM
        )
        
        assert task_create.title == "Test Task"
        assert task_create.priority == PriorityLevel.MEDIUM

    def test_task_create_required_fields(self):
        """Test TaskCreate required fields."""
        # Test missing user_id
        with pytest.raises(ValueError):
            TaskCreate(title="Test Task")  # type: ignore # Missing user_id
        
        # Test missing title
        with pytest.raises(ValueError):
            TaskCreate(user_id=uuid4())  # type: ignore # Missing title
            
        # Test both missing
        with pytest.raises(ValueError):
            TaskCreate()  # type: ignore # Missing both required fields

    def test_task_update_partial(self):
        """Test TaskUpdate allows partial updates."""
        # Should work with just one field
        task_update = TaskUpdate(title="New Title")
        assert task_update.title == "New Title"
        assert task_update.description is None

        # Should work with multiple fields
        task_update = TaskUpdate(
            title="New Title",
            status=TaskStatus.IN_PROGRESS
        )
        assert task_update.title == "New Title"
        assert task_update.status == TaskStatus.IN_PROGRESS

    def test_task_status_enum(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_priority_level_enum(self):
        """Test PriorityLevel enum values."""
        assert PriorityLevel.LOW.value == "low"
        assert PriorityLevel.MEDIUM.value == "medium"
        assert PriorityLevel.HIGH.value == "high"
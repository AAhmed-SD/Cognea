import uuid
from datetime import datetime, timedelta, UTC

import pytest
from pydantic import ValidationError

from models.task import Task, TaskCreate, TaskStatus, PriorityLevel


def _fake_datetime():
    return datetime(2025, 1, 1, tzinfo=UTC)


class TestTaskModelValidation:
    def test_task_create_validation_success(self):
        t = TaskCreate(
            title="Test task",
            description="desc",
            due_date=_fake_datetime() + timedelta(days=1),
            priority=PriorityLevel.HIGH,
            user_id=uuid.uuid4(),
        )
        assert t.priority == PriorityLevel.HIGH

    def test_task_create_title_constraints(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="", user_id=uuid.uuid4())

    def test_task_status_defaults(self):
        task = Task(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title="Task",
            description=None,
            created_at=_fake_datetime(),
            updated_at=_fake_datetime(),
            due_date=None,
        )
        assert task.status == TaskStatus.PENDING
        assert task.priority == PriorityLevel.MEDIUM

    def test_task_update_optional_fields(self):
        from models.task import TaskUpdate

        up = TaskUpdate(title="New title", status=TaskStatus.COMPLETED)
        assert up.title == "New title"
        assert up.status == TaskStatus.COMPLETED
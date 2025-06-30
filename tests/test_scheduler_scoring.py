"""
Tests for scheduler scoring functionality.
"""

import pytest
from datetime import datetime, timedelta, UTC
from services.scheduler import SchedulerService
from models.task import Task, TaskPriority, TaskStatus
from models.schedule_block import ScheduleBlock


class TestSchedulerScoring:
    """Test scheduler scoring algorithms."""

    @pytest.fixture
    def scheduler(self):
        """Create a scheduler service instance."""
        return SchedulerService()

    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks for testing."""
        return [
            Task(
                id="task1",
                user_id="user1",
                title="Urgent Task",
                description="High priority task",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                due_date=datetime.now(UTC) + timedelta(hours=2),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            Task(
                id="task2",
                user_id="user1",
                title="Medium Task",
                description="Medium priority task",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                due_date=datetime.now(UTC) + timedelta(days=1),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            Task(
                id="task3",
                user_id="user1",
                title="Low Task",
                description="Low priority task",
                status=TaskStatus.PENDING,
                priority=TaskPriority.LOW,
                due_date=datetime.now(UTC) + timedelta(days=3),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]

    def test_calculate_task_score_priority(self, scheduler, sample_tasks):
        """Test that task scoring considers priority correctly."""
        high_priority_task = sample_tasks[0]
        medium_priority_task = sample_tasks[1]
        low_priority_task = sample_tasks[2]

        # Test with same slot and energy
        slot = {
            "start_time": datetime.now(UTC) + timedelta(hours=1),
            "end_time": datetime.now(UTC) + timedelta(hours=2),
            "duration_minutes": 60,
        }
        energy = 0.8

        high_score = scheduler.calculate_task_score(high_priority_task, slot, energy)
        medium_score = scheduler.calculate_task_score(medium_priority_task, slot, energy)
        low_score = scheduler.calculate_task_score(low_priority_task, slot, energy)

        # High priority should score higher than medium, which should score higher than low
        assert high_score > medium_score
        assert medium_score > low_score

    def test_calculate_task_score_due_date(self, scheduler):
        """Test that task scoring considers due date urgency."""
        now = datetime.now(UTC)
        
        urgent_task = Task(
            id="urgent",
            user_id="user1",
            title="Urgent Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            due_date=now + timedelta(hours=1),
            created_at=now,
            updated_at=now,
        )
        
        non_urgent_task = Task(
            id="non_urgent",
            user_id="user1",
            title="Non-urgent Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            due_date=now + timedelta(days=7),
            created_at=now,
            updated_at=now,
        )

        slot = {
            "start_time": now + timedelta(hours=1),
            "end_time": now + timedelta(hours=2),
            "duration_minutes": 60,
        }
        energy = 0.8

        urgent_score = scheduler.calculate_task_score(urgent_task, slot, energy)
        non_urgent_score = scheduler.calculate_task_score(non_urgent_task, slot, energy)

        # Urgent task should score higher
        assert urgent_score > non_urgent_score

    def test_calculate_task_score_energy(self, scheduler, sample_tasks):
        """Test that task scoring considers user energy levels."""
        task = sample_tasks[0]  # High priority task
        slot = {
            "start_time": datetime.now(UTC) + timedelta(hours=1),
            "end_time": datetime.now(UTC) + timedelta(hours=2),
            "duration_minutes": 60,
        }

        high_energy_score = scheduler.calculate_task_score(task, slot, 0.9)
        low_energy_score = scheduler.calculate_task_score(task, slot, 0.3)

        # High energy should result in higher scores for high-priority tasks
        assert high_energy_score > low_energy_score

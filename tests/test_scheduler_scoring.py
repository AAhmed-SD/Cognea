"""
Tests for scheduler scoring functionality.
"""

import pytest
from datetime import datetime, timedelta, UTC
from services.scheduler import SimpleScheduler, Task, TimeSlot


@pytest.fixture
def scheduler():
    return SimpleScheduler()


@pytest.fixture
def sample_tasks():
    now = datetime.now(UTC)
    return [
        Task(
            id="task1",
            title="High Priority Task",
            description="Important task",
            priority="high",
            estimated_minutes=30,
            category="work",
            due_date=now + timedelta(hours=2),
            energy_requirement=5,
        ),
        Task(
            id="task2",
            title="Medium Priority Task",
            description="Regular task",
            priority="medium",
            estimated_minutes=60,
            category="personal",
            due_date=now + timedelta(days=1),
            energy_requirement=5,
        ),
        Task(
            id="task3",
            title="Low Priority Task",
            description="Low priority task",
            priority="low",
            estimated_minutes=45,
            category="learning",
            due_date=now + timedelta(days=3),
            energy_requirement=5,
        ),
    ]


class TestSchedulerScoring:
    """Test scheduler scoring algorithms."""

    def test_calculate_task_score_priority(self, scheduler, sample_tasks):
        """Test that task scoring considers priority."""
        now = datetime.now(UTC)
        time_slot = TimeSlot(
            start_time=now,
            end_time=now + timedelta(hours=1),
            duration_minutes=60,
            energy_level=5,
        )

        # High priority task should score higher than low priority
        high_score = scheduler.calculate_task_score(sample_tasks[0], time_slot)
        low_score = scheduler.calculate_task_score(sample_tasks[2], time_slot)

        assert high_score > low_score

    def test_calculate_task_score_length(self, scheduler):
        """Test that task scoring considers task length (shorter tasks score higher)."""
        now = datetime.now(UTC)

        short_task = Task(
            id="short",
            title="Short Task",
            description="Short task",
            priority="medium",
            estimated_minutes=15,
            category="work",
            due_date=now + timedelta(hours=1),
            energy_requirement=5,
        )

        long_task = Task(
            id="long",
            title="Long Task",
            description="Long task",
            priority="medium",
            estimated_minutes=120,
            category="work",
            due_date=now + timedelta(days=7),
            energy_requirement=5,
        )

        time_slot = TimeSlot(
            start_time=now,
            end_time=now + timedelta(hours=1),
            duration_minutes=60,
            energy_level=5,
        )

        short_score = scheduler.calculate_task_score(short_task, time_slot)
        long_score = scheduler.calculate_task_score(long_task, time_slot)

        # Shorter task should score higher
        assert short_score > long_score

    def test_calculate_task_score_energy(self, scheduler):
        """Test that task scoring considers energy compatibility."""
        now = datetime.now(UTC)

        high_energy_task = Task(
            id="high_energy",
            title="High Energy Task",
            description="High energy task",
            priority="medium",
            estimated_minutes=30,
            category="work",
            due_date=now + timedelta(hours=1),
            energy_requirement=8,
        )

        high_energy_slot = TimeSlot(
            start_time=now,
            end_time=now + timedelta(hours=1),
            duration_minutes=60,
            energy_level=8,
        )

        low_energy_slot = TimeSlot(
            start_time=now,
            end_time=now + timedelta(hours=1),
            duration_minutes=60,
            energy_level=2,
        )

        # High energy task should score better in high energy slot
        high_energy_score = scheduler.calculate_task_score(
            high_energy_task, high_energy_slot
        )
        low_energy_score = scheduler.calculate_task_score(
            high_energy_task, low_energy_slot
        )

        assert high_energy_score > low_energy_score

    def test_calculate_task_score_time_of_day(self, scheduler):
        """Test that task scoring considers time of day."""
        now = datetime.now(UTC)

        task = Task(
            id="test_task",
            title="Test Task",
            description="Test task",
            priority="medium",
            estimated_minutes=30,
            category="work",
            due_date=now + timedelta(hours=1),
            energy_requirement=5,
        )

        # Morning slot (should get energy boost)
        morning_slot = TimeSlot(
            start_time=now.replace(hour=9),
            end_time=now.replace(hour=10),
            duration_minutes=60,
            energy_level=5,
        )

        # Afternoon slot (should get energy penalty)
        afternoon_slot = TimeSlot(
            start_time=now.replace(hour=15),
            end_time=now.replace(hour=16),
            duration_minutes=60,
            energy_level=5,
        )

        morning_score = scheduler.calculate_task_score(task, morning_slot)
        afternoon_score = scheduler.calculate_task_score(task, afternoon_slot)

        # Morning should score higher due to energy boost
        assert morning_score > afternoon_score

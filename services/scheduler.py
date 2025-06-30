"""
Simple scheduler algorithm for Cognie.
Scores tasks by priority × (1/length) × availability, with energy feedback support.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


@dataclass
class TimeSlot:
    """Represents a time slot for scheduling."""

    start_time: datetime
    end_time: datetime
    duration_minutes: int
    energy_level: int = 5  # 1-10 scale
    focus_type: str = "deep_work"  # deep_work, meeting, break, learning


@dataclass
class Task:
    """Represents a task for scheduling."""

    id: str
    title: str
    description: str
    priority: str  # low, medium, high, urgent
    estimated_minutes: int
    category: str
    due_date: Optional[datetime] = None
    energy_requirement: int = 5  # 1-10 scale
    focus_type: str = "deep_work"


class SchedulerConfig(BaseModel):
    """Scheduler configuration."""

    model_config = ConfigDict(from_attributes=True)

    # Priority weights
    priority_weights: Dict[str, float] = {
        "urgent": 4.0,
        "high": 3.0,
        "medium": 2.0,
        "low": 1.0,
    }

    # Energy multipliers
    energy_multipliers: Dict[str, float] = {
        "deep_work": 1.5,
        "learning": 1.2,
        "meeting": 1.0,
        "break": 0.5,
    }

    # Time of day preferences
    morning_energy_boost: float = 1.2  # Tasks in morning get energy boost
    afternoon_energy_penalty: float = 0.8  # Tasks in afternoon get energy penalty

    # Minimum break duration
    min_break_minutes: int = 15


class SimpleScheduler:
    """Simple scheduler using priority × (1/length) × availability scoring."""

    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()

    def calculate_task_score(
        self, task: Task, time_slot: TimeSlot, user_energy: int = 5
    ) -> float:
        """Calculate task score using priority × (1/length) × availability formula."""

        # Priority weight
        priority_weight = self.config.priority_weights.get(task.priority, 1.0)

        # Length factor (shorter tasks get higher scores)
        length_factor = 1.0 / max(task.estimated_minutes, 1)

        # Availability factor (how well task fits in time slot)
        availability_factor = self._calculate_availability_factor(task, time_slot)

        # Energy factor (match task energy requirement with time slot energy level)
        energy_factor = self._calculate_energy_factor(
            task, time_slot, time_slot.energy_level
        )

        # Time of day factor
        time_factor = self._calculate_time_factor(time_slot)

        # Calculate final score
        score = (
            priority_weight
            * length_factor
            * availability_factor
            * energy_factor
            * time_factor
        )

        return score

    def _calculate_availability_factor(self, task: Task, time_slot: TimeSlot) -> float:
        """Calculate how well a task fits in the time slot."""
        # Perfect fit if task duration <= slot duration
        if task.estimated_minutes <= time_slot.duration_minutes:
            return 1.0

        # Penalty for tasks that don't fit
        fit_ratio = time_slot.duration_minutes / task.estimated_minutes
        return max(fit_ratio, 0.1)  # Minimum 10% score

    def _calculate_energy_factor(
        self, task: Task, time_slot: TimeSlot, user_energy: int
    ) -> float:
        """Calculate energy compatibility factor."""
        # Energy compatibility (closer energy levels = higher score)
        energy_diff = abs(task.energy_requirement - user_energy)
        energy_compatibility = max(1.0 - (energy_diff / 10.0), 0.1)

        # Focus type multiplier
        focus_multiplier = self.config.energy_multipliers.get(task.focus_type, 1.0)

        return energy_compatibility * focus_multiplier

    def _calculate_time_factor(self, time_slot: TimeSlot) -> float:
        """Calculate time of day factor."""
        hour = time_slot.start_time.hour

        if 6 <= hour < 12:  # Morning
            return self.config.morning_energy_boost
        elif 14 <= hour < 18:  # Afternoon
            return self.config.afternoon_energy_penalty
        else:  # Evening/Night
            return 1.0

    def schedule_tasks(
        self, tasks: List[Task], time_slots: List[TimeSlot], user_energy: int = 5
    ) -> List[Dict[str, Any]]:
        """Schedule tasks into time slots using greedy algorithm."""

        # Sort tasks by priority first
        sorted_tasks = sorted(
            tasks,
            key=lambda t: self.config.priority_weights.get(t.priority, 1.0),
            reverse=True,
        )

        # Sort time slots by start time
        sorted_slots = sorted(time_slots, key=lambda s: s.start_time)

        schedule = []
        used_slots = set()

        for task in sorted_tasks:
            best_slot = None
            best_score = 0

            # Find the best time slot for this task
            for i, slot in enumerate(sorted_slots):
                if i in used_slots:
                    continue

                score = self.calculate_task_score(task, slot, user_energy)

                if (
                    score > best_score
                    and task.estimated_minutes <= slot.duration_minutes
                ):
                    best_score = score
                    best_slot = (i, slot)

            if best_slot:
                slot_index, slot = best_slot
                used_slots.add(slot_index)

                schedule.append(
                    {
                        "task": task,
                        "time_slot": slot,
                        "score": best_score,
                        "start_time": slot.start_time,
                        "end_time": slot.start_time
                        + timedelta(minutes=task.estimated_minutes),
                    }
                )

        return schedule

    def optimize_schedule(
        self, current_schedule: List[Dict], user_energy: int = 5
    ) -> List[Dict]:
        """Optimize an existing schedule based on user energy."""

        # Extract tasks and time slots
        tasks = [item["task"] for item in current_schedule]
        time_slots = [item["time_slot"] for item in current_schedule]

        # Re-schedule with current energy level
        optimized_schedule = self.schedule_tasks(tasks, time_slots, user_energy)

        return optimized_schedule

    def add_breaks(
        self, schedule: List[Dict], min_break_minutes: int = None
    ) -> List[Dict]:
        """Add breaks between tasks to prevent burnout."""

        if min_break_minutes is None:
            min_break_minutes = self.config.min_break_minutes

        schedule_with_breaks = []

        for i, item in enumerate(schedule):
            schedule_with_breaks.append(item)

            # Add break after task (except the last one)
            if i < len(schedule) - 1:
                next_task_start = schedule[i + 1]["start_time"]
                current_task_end = item["end_time"]

                # Check if there's enough time for a break
                time_between = (next_task_start - current_task_end).total_seconds() / 60

                if time_between >= min_break_minutes:
                    break_slot = TimeSlot(
                        start_time=current_task_end,
                        end_time=current_task_end
                        + timedelta(minutes=min_break_minutes),
                        duration_minutes=min_break_minutes,
                        energy_level=1,
                        focus_type="break",
                    )

                    schedule_with_breaks.append(
                        {
                            "task": Task(
                                id="break",
                                title="Break",
                                description="Take a short break",
                                priority="low",
                                estimated_minutes=min_break_minutes,
                                category="break",
                                energy_requirement=1,
                                focus_type="break",
                            ),
                            "time_slot": break_slot,
                            "score": 0.1,
                            "start_time": break_slot.start_time,
                            "end_time": break_slot.end_time,
                        }
                    )

        return schedule_with_breaks

    def get_schedule_insights(self, schedule: List[Dict]) -> Dict[str, Any]:
        """Generate insights about the schedule."""

        if not schedule:
            return {"message": "No tasks scheduled"}

        total_tasks = len([item for item in schedule if item["task"].id != "break"])
        total_breaks = len([item for item in schedule if item["task"].id == "break"])
        total_duration = sum(
            item["task"].estimated_minutes
            for item in schedule
            if item["task"].id != "break"
        )

        # Priority distribution
        priority_counts = {}
        for item in schedule:
            if item["task"].id != "break":
                priority = item["task"].priority
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Focus type distribution
        focus_counts = {}
        for item in schedule:
            if item["task"].id != "break":
                focus_type = item["task"].focus_type
                focus_counts[focus_type] = focus_counts.get(focus_type, 0) + 1

        return {
            "total_tasks": total_tasks,
            "total_breaks": total_breaks,
            "total_duration_minutes": total_duration,
            "priority_distribution": priority_counts,
            "focus_type_distribution": focus_counts,
            "schedule_efficiency": self._calculate_schedule_efficiency(schedule),
        }

    def _calculate_schedule_efficiency(self, schedule: List[Dict]) -> float:
        """Calculate schedule efficiency score."""
        if not schedule:
            return 0.0

        # Calculate average task score
        task_scores = [item["score"] for item in schedule if item["task"].id != "break"]

        if not task_scores:
            return 0.0

        return sum(task_scores) / len(task_scores)


# Global instance
scheduler = SimpleScheduler()

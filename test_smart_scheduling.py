#!/usr/bin/env python3
"""
Test Smart Scheduling System
Demonstrates the AI-powered smart scheduling capabilities.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai.smart_scheduler import get_smart_scheduler


async def test_smart_scheduling():
    """Test the smart scheduling system"""
    print("🧠 Testing Smart Scheduling System...")
    print("=" * 60)

    scheduler = get_smart_scheduler()

    # Test data
    exam_dates = [
        {
            "date": "2024-02-15",
            "subject": "Organic Chemistry",
            "topics": ["Alkanes", "Alkenes", "Alkynes", "Reactions"],
            "weight": 0.4,
        },
        {
            "date": "2024-02-22",
            "subject": "Calculus",
            "topics": ["Derivatives", "Integration", "Applications"],
            "weight": 0.3,
        },
        {
            "date": "2024-03-01",
            "subject": "Physics",
            "topics": ["Mechanics", "Thermodynamics", "Waves"],
            "weight": 0.3,
        },
    ]

    flashcard_performance = {
        "Organic Chemistry": {
            "total_cards": 150,
            "correct_answers": 89,
            "accuracy": 0.59,
            "difficulty_level": "high",
            "last_reviewed": "2024-01-20",
        },
        "Calculus": {
            "total_cards": 120,
            "correct_answers": 95,
            "accuracy": 0.79,
            "difficulty_level": "medium",
            "last_reviewed": "2024-01-22",
        },
        "Physics": {
            "total_cards": 100,
            "correct_answers": 72,
            "accuracy": 0.72,
            "difficulty_level": "medium",
            "last_reviewed": "2024-01-21",
        },
    }

    available_time = {
        "monday": 3,
        "tuesday": 2,
        "wednesday": 4,
        "thursday": 2,
        "friday": 3,
        "saturday": 5,
        "sunday": 4,
    }

    study_preferences = {
        "preferred_session_length": 45,
        "break_duration": 15,
        "preferred_time": "evening",
        "learning_style": "visual",
        "difficulty_preference": "progressive",
    }

    # Test 1: Generate Study Schedule
    print("\n1. Testing Study Schedule Generation...")
    try:
        schedule_result = await scheduler.generate_study_schedule(
            user_id="test_user_123",
            exam_dates=exam_dates,
            flashcard_performance=flashcard_performance,
            available_time=available_time,
            study_preferences=study_preferences,
        )

        if schedule_result["success"]:
            print("✅ Study schedule generated successfully!")
            print(f"   Model used: {schedule_result['model_used']}")
            print(f"   Provider: {schedule_result['provider']}")
            print(f"   Cost: £{schedule_result['cost_usd']:.6f}")
            print(f"   Quality score: {schedule_result['quality_score']:.2f}")

            # Show sample of the schedule
            schedule = schedule_result["schedule"]
            if "daily_schedule" in schedule and schedule["daily_schedule"]:
                print(f"   Days planned: {len(schedule['daily_schedule'])}")
                if "recommendations" in schedule:
                    print(f"   Recommendations: {len(schedule['recommendations'])}")
        else:
            print(
                f"❌ Schedule generation failed: {schedule_result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        print(f"❌ Schedule generation test failed: {e}")

    # Test 2: Memory Pattern Analysis
    print("\n2. Testing Memory Pattern Analysis...")
    try:
        flashcard_history = [
            {
                "flashcard_id": "fc_001",
                "topic": "Organic Chemistry",
                "correct": True,
                "timestamp": "2024-01-20T10:30:00",
                "review_count": 3,
            },
            {
                "flashcard_id": "fc_002",
                "topic": "Organic Chemistry",
                "correct": False,
                "timestamp": "2024-01-20T10:35:00",
                "review_count": 5,
            },
            {
                "flashcard_id": "fc_003",
                "topic": "Calculus",
                "correct": True,
                "timestamp": "2024-01-22T14:20:00",
                "review_count": 2,
            },
        ]

        study_sessions = [
            {
                "session_id": "ss_001",
                "date": "2024-01-20",
                "duration_minutes": 90,
                "topics": ["Organic Chemistry"],
                "flashcards_reviewed": 25,
                "accuracy": 0.68,
            },
            {
                "session_id": "ss_002",
                "date": "2024-01-22",
                "duration_minutes": 60,
                "topics": ["Calculus"],
                "flashcards_reviewed": 20,
                "accuracy": 0.85,
            },
        ]

        memory_result = await scheduler.analyze_memory_patterns(
            user_id="test_user_123",
            flashcard_history=flashcard_history,
            study_sessions=study_sessions,
        )

        if memory_result["success"]:
            print("✅ Memory analysis completed successfully!")
            print(f"   Model used: {memory_result['model_used']}")
            print(f"   Provider: {memory_result['provider']}")
            print(f"   Cost: £{memory_result['cost_usd']:.6f}")
            print(f"   Quality score: {memory_result['quality_score']:.2f}")

            analysis = memory_result["analysis"]
            if "difficult_topics" in analysis:
                print(
                    f"   Difficult topics identified: {len(analysis['difficult_topics'])}"
                )
            if "recommendations" in analysis:
                print(
                    f"   Recommendations provided: {len(analysis['recommendations'])}"
                )
        else:
            print(
                f"❌ Memory analysis failed: {memory_result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        print(f"❌ Memory analysis test failed: {e}")

    # Test 3: Revision Planning
    print("\n3. Testing Revision Planning...")
    try:
        exam_date = datetime(2024, 2, 15)
        topics = ["Alkanes", "Alkenes", "Alkynes", "Reactions"]
        current_progress = {
            "Alkanes": 0.75,
            "Alkenes": 0.45,
            "Alkynes": 0.30,
            "Reactions": 0.60,
        }
        available_days = 25

        revision_result = await scheduler.generate_revision_plan(
            user_id="test_user_123",
            exam_date=exam_date,
            topics=topics,
            current_progress=current_progress,
            available_days=available_days,
        )

        if revision_result["success"]:
            print("✅ Revision plan generated successfully!")
            print(f"   Model used: {revision_result['model_used']}")
            print(f"   Provider: {revision_result['provider']}")
            print(f"   Cost: £{revision_result['cost_usd']:.6f}")
            print(f"   Quality score: {revision_result['quality_score']:.2f}")

            revision_plan = revision_result["revision_plan"]
            if "revision_schedule" in revision_plan:
                print(
                    f"   Revision days planned: {len(revision_plan['revision_schedule'])}"
                )
            if "mock_exam_schedule" in revision_plan:
                print(
                    f"   Mock exams scheduled: {len(revision_plan['mock_exam_schedule'])}"
                )
        else:
            print(
                f"❌ Revision planning failed: {revision_result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        print(f"❌ Revision planning test failed: {e}")

    print("\n" + "=" * 60)
    print("🎯 Smart Scheduling Test Summary")
    print("=" * 60)
    print("The smart scheduling system provides:")
    print("✅ Personalized study schedules based on exam dates")
    print("✅ Memory pattern analysis for optimal learning")
    print("✅ Intelligent revision planning with progress tracking")
    print("✅ Cost-effective AI routing (Claude → DeepSeek → OpenAI)")
    print("✅ Quality assurance with automatic fallbacks")
    print("\nNext steps:")
    print("1. Set up API keys for Claude and DeepSeek")
    print("2. Integrate with your existing flashcard system")
    print("3. Connect to your calendar/exam management system")
    print("4. Deploy to your student testers")


def main():
    """Main test function"""
    print("🚀 Smart Scheduling System Test Suite")
    print("=" * 60)

    asyncio.run(test_smart_scheduling())

    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    main()

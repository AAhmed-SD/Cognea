#!/usr/bin/env python3
"""
Test script to verify database operations work with new models and routers.
"""
import asyncio
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.task import TaskCreate, TaskStatus, PriorityLevel
from models.goal import GoalCreate


def get_supabase_service_client():
    """Get Supabase client with service role key for testing."""
    import os
    from supabase import create_client

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set"
        )

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


async def test_database_operations():
    """Test basic database operations."""
    print("🧪 Testing Database Operations")
    print("=" * 40)

    try:
        # Use service client to bypass RLS for testing
        supabase = get_supabase_service_client()

        # Test 1: Check if tables exist
        print("\n1. Testing table existence...")

        # Test tasks table
        try:
            result = supabase.table("tasks").select("id").limit(1).execute()
            print("✅ Tasks table exists")
        except Exception as e:
            print(f"❌ Tasks table error: {e}")
            return False

        # Test goals table
        try:
            result = supabase.table("goals").select("id").limit(1).execute()
            print("✅ Goals table exists")
        except Exception as e:
            print(f"❌ Goals table error: {e}")
            return False

        # Test 2: Create a test task
        print("\n2. Testing task creation...")
        test_user_id = str(uuid4())  # Generate a test user ID

        task_data = {
            "user_id": test_user_id,
            "title": "Test Task - Database Operations",
            "description": "This is a test task to verify database operations work",
            "priority": PriorityLevel.HIGH.value,
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            result = supabase.table("tasks").insert(task_data).execute()
            if result.data:
                print("✅ Task created successfully")
                task_id = result.data[0]["id"]
                print(f"   Task ID: {task_id}")
            else:
                print("❌ Failed to create task")
                return False
        except Exception as e:
            print(f"❌ Task creation error: {e}")
            return False

        # Test 3: Create a test goal
        print("\n3. Testing goal creation...")

        goal_data = {
            "user_id": test_user_id,
            "title": "Test Goal - Database Operations",
            "description": "This is a test goal to verify database operations work",
            "priority": PriorityLevel.MEDIUM.value,
            "status": "Not Started",
            "progress": 0,
            "is_starred": False,
            "analytics": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            result = supabase.table("goals").insert(goal_data).execute()
            if result.data:
                print("✅ Goal created successfully")
                goal_id = result.data[0]["id"]
                print(f"   Goal ID: {goal_id}")
            else:
                print("❌ Failed to create goal")
                return False
        except Exception as e:
            print(f"❌ Goal creation error: {e}")
            return False

        # Test 4: Read the created task
        print("\n4. Testing task retrieval...")
        try:
            result = supabase.table("tasks").select("*").eq("id", task_id).execute()
            if result.data:
                task = result.data[0]
                print("✅ Task retrieved successfully")
                print(f"   Title: {task['title']}")
                print(f"   Status: {task['status']}")
                print(f"   Priority: {task['priority']}")
            else:
                print("❌ Failed to retrieve task")
                return False
        except Exception as e:
            print(f"❌ Task retrieval error: {e}")
            return False

        # Test 5: Update the task
        print("\n5. Testing task update...")
        update_data = {
            "status": TaskStatus.COMPLETED.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            result = (
                supabase.table("tasks").update(update_data).eq("id", task_id).execute()
            )
            if result.data:
                print("✅ Task updated successfully")
                print(f"   New status: {result.data[0]['status']}")
            else:
                print("❌ Failed to update task")
                return False
        except Exception as e:
            print(f"❌ Task update error: {e}")
            return False

        # Test 6: Clean up test data
        print("\n6. Cleaning up test data...")
        try:
            # Delete test task
            supabase.table("tasks").delete().eq("id", task_id).execute()
            print("✅ Test task deleted")

            # Delete test goal
            supabase.table("goals").delete().eq("id", goal_id).execute()
            print("✅ Test goal deleted")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

        print("\n🎉 All database operations tests passed!")
        return True

    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False


async def test_model_validation():
    """Test Pydantic model validation."""
    print("\n🧪 Testing Model Validation")
    print("=" * 40)

    try:
        # Test TaskCreate model
        print("\n1. Testing TaskCreate model...")

        # Valid task
        valid_task = TaskCreate(  # noqa: F841
            user_id=uuid4(),
            title="Valid Task",
            description="This is a valid task",
            priority=PriorityLevel.MEDIUM,
        )
        print("✅ Valid TaskCreate model created")

        # Test GoalCreate model
        print("\n2. Testing GoalCreate model...")

        valid_goal = GoalCreate(  # noqa: F841
            user_id=uuid4(),
            title="Valid Goal",
            description="This is a valid goal",
            priority=PriorityLevel.HIGH,
            is_starred=True,
        )
        print("✅ Valid GoalCreate model created")

        print("\n🎉 All model validation tests passed!")
        return True

    except Exception as e:
        print(f"❌ Model validation test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Database and Model Tests")
    print("=" * 50)

    # Test model validation first
    model_success = await test_model_validation()

    # Test database operations
    db_success = await test_database_operations()

    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Model Validation: {'✅ PASSED' if model_success else '❌ FAILED'}")
    print(f"Database Operations: {'✅ PASSED' if db_success else '❌ FAILED'}")

    if model_success and db_success:
        print("\n🎉 All tests passed! Your backend is ready for development.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

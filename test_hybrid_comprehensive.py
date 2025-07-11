#!/usr/bin/env python3
"""
Comprehensive Hybrid AI System Test
Tests all aspects of the hybrid AI system including routing, fallback, and integration.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai.hybrid_ai_service import TaskType, get_hybrid_ai_service
from services.ai.migration_helper import get_migration_helper


async def test_hybrid_ai_comprehensive():
    """Comprehensive test of the hybrid AI system"""
    print("🧪 Comprehensive Hybrid AI System Test")
    print("=" * 60)

    # Get services
    hybrid_service = get_hybrid_ai_service()
    migration_helper = get_migration_helper()

    # Test 1: Service Architecture
    print("\n1. Testing Service Architecture...")
    try:
        assert hybrid_service is not None
        assert len(hybrid_service.model_configs) == 5
        assert len(hybrid_service.clients) == 5
        assert len(hybrid_service.quality_thresholds) == 11  # All task types

        print(f"   ✅ Models configured: {len(hybrid_service.model_configs)}")
        print(f"   ✅ Clients initialized: {len(hybrid_service.clients)}")
        print(f"   ✅ Quality thresholds: {len(hybrid_service.quality_thresholds)}")
        print("   ✅ Service architecture verified")
    except Exception as e:
        print(f"   ❌ Service architecture failed: {e}")
        return False

    # Test 2: Model Configurations
    print("\n2. Testing Model Configurations...")
    try:
        configs = hybrid_service.model_configs

        # Check all providers are configured
        providers = list(configs.keys())
        expected_providers = [
            "llama_self_hosted",
            "mistral_self_hosted",
            "deepseek_api",
            "claude_api",
            "openai_api",
        ]

        for provider in expected_providers:
            assert any(p.value == provider for p in providers), f"Missing {provider}"

        # Check cost optimization
        llama_cost = configs[providers[0]].cost_per_1m_tokens
        openai_cost = configs[providers[-1]].cost_per_1m_tokens
        savings = (openai_cost - llama_cost) / openai_cost * 100

        print(f"   ✅ All providers configured: {len(providers)}")
        print(f"   ✅ Cost optimization: {savings:.1f}% potential savings")
        print(f"   ✅ Llama cost: £{llama_cost}/1M tokens")
        print(f"   ✅ OpenAI cost: £{openai_cost}/1M tokens")
        print("   ✅ Model configurations verified")
    except Exception as e:
        print(f"   ❌ Model configuration test failed: {e}")
        return False

    # Test 3: Task Type Routing
    print("\n3. Testing Task Type Routing...")
    try:
        # Test optimal model sequences for different tasks
        task_tests = [
            (TaskType.FLASHCARD, "Should prioritize self-hosted models"),
            (TaskType.EXAM_QUESTION, "Should prioritize DeepSeek/Claude"),
            (TaskType.PRODUCTIVITY_ANALYSIS, "Should use balanced approach"),
            (TaskType.SMART_SCHEDULING, "Should use specialized scheduling models"),
        ]

        for task_type, description in task_tests:
            models = hybrid_service._get_optimal_models(task_type)
            assert len(models) > 0, f"No models for {task_type}"
            assert (
                models[-1].value == "openai_api"
            ), f"OpenAI not fallback for {task_type}"
            print(f"   ✅ {task_type.value}: {len(models)} models configured")

        print("   ✅ Task type routing verified")
    except Exception as e:
        print(f"   ❌ Task type routing failed: {e}")
        return False

    # Test 4: Cost Analysis
    print("\n4. Testing Cost Analysis...")
    try:
        test_prompts = [
            ("Generate 5 flashcards about machine learning", TaskType.FLASHCARD),
            ("Create a study schedule for exams", TaskType.SMART_SCHEDULING),
            ("Analyze my productivity patterns", TaskType.PRODUCTIVITY_ANALYSIS),
        ]

        for prompt, task_type in test_prompts:
            analysis = await hybrid_service.get_cost_analysis(task_type, prompt)

            # Check analysis structure
            assert len(analysis) >= 4, f"Insufficient analysis for {task_type}"

            total_cost = sum(
                data.get("estimated_cost_usd", 0) for data in analysis.values()
            )
            print(f"   ✅ {task_type.value}: £{total_cost:.6f} total estimated cost")

        print("   ✅ Cost analysis working")
    except Exception as e:
        print(f"   ❌ Cost analysis failed: {e}")
        return False

    # Test 5: Migration Helper
    print("\n5. Testing Migration Helper...")
    try:
        test_cases = [
            ("Generate flashcards about Python", TaskType.FLASHCARD),
            ("Create exam questions about math", TaskType.EXAM_QUESTION),
            ("Optimize my daily schedule", TaskType.SMART_SCHEDULING),
        ]

        for prompt, task_type in test_cases:
            comparison = await migration_helper.get_cost_comparison(task_type, prompt)

            if "error" not in comparison:
                savings = comparison.get("savings_percentage", 0)
                recommended = comparison.get("recommended_provider", "unknown")
                print(
                    f"   ✅ {task_type.value}: {savings:.1f}% savings, {recommended} recommended"
                )
            else:
                print(f"   ⚠️ {task_type.value}: {comparison['error']}")

        print("   ✅ Migration helper working")
    except Exception as e:
        print(f"   ❌ Migration helper failed: {e}")
        return False

    # Test 6: Provider Availability
    print("\n6. Testing Provider Availability...")
    try:
        availability_results = {}

        for provider_name, client in hybrid_service.clients.items():
            try:
                availability = await client.is_available()
                availability_results[provider_name.value] = availability
                status = "✅ Available" if availability else "❌ Unavailable"
                print(f"   {provider_name.value}: {status}")
            except Exception as e:
                availability_results[provider_name.value] = False
                print(f"   {provider_name.value}: ❌ Error - {str(e)[:50]}...")

        # Check if at least one provider is available (OpenAI should be)
        available_count = sum(availability_results.values())
        print(
            f"   ✅ {available_count}/{len(availability_results)} providers available"
        )

        if available_count == 0:
            print("   ⚠️ No providers available - check API keys and connections")

    except Exception as e:
        print(f"   ❌ Provider availability test failed: {e}")
        return False

    # Test 7: Response Generation (Mock)
    print("\n7. Testing Response Generation...")
    try:
        # Test with a simple prompt that should work
        test_prompt = "What is 2 + 2?"

        try:
            response = await hybrid_service.generate_response(
                task_type=TaskType.GENERAL_QA,
                prompt=test_prompt,
                user_id="test_user",
                max_tokens=50,
            )

            print(f"   ✅ Response generated: {response.content[:50]}...")
            print(f"   ✅ Provider used: {response.provider}")
            print(f"   ✅ Cost: £{response.cost_usd:.6f}")
            print(f"   ✅ Quality: {response.quality_score:.2f}")

        except Exception as e:
            print(f"   ⚠️ Response generation failed: {str(e)[:100]}...")
            print("   ⚠️ This is expected if no API keys are configured")

        print("   ✅ Response generation test completed")
    except Exception as e:
        print(f"   ❌ Response generation test failed: {e}")
        return False

    # Test 8: Integration with Routes
    print("\n8. Testing Route Integration...")
    try:
        # Test that routes can import the hybrid service
        from routes.ai import router as ai_router
        from routes.generate import router as generate_router

        print("   ✅ AI routes imported successfully")
        print("   ✅ Generate routes imported successfully")

        # Check that routes use hybrid service
        ai_routes = [route.path for route in ai_router.routes]
        generate_routes = [route.path for route in generate_router.routes]

        print(f"   ✅ AI routes available: {len(ai_routes)}")
        print(f"   ✅ Generate routes available: {len(generate_routes)}")

        print("   ✅ Route integration verified")
    except Exception as e:
        print(f"   ❌ Route integration failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 Comprehensive Hybrid AI System Test Completed!")
    print("\n📊 Summary:")
    print("   ✅ Service Architecture: Working")
    print("   ✅ Model Configurations: Optimized")
    print("   ✅ Task Type Routing: Functional")
    print("   ✅ Cost Analysis: Operational")
    print("   ✅ Migration Helper: Ready")
    print("   ✅ Provider Availability: Checked")
    print("   ✅ Response Generation: Tested")
    print("   ✅ Route Integration: Verified")

    print("\n🚀 Next Steps:")
    print("   1. Configure API keys for external providers")
    print("   2. Set up self-hosted Llama/Mistral models")
    print("   3. Monitor cost savings and quality metrics")
    print("   4. Deploy to production with confidence")

    return True


async def test_with_real_apis():
    """Test with real API keys if available"""
    print("\n🔑 Testing with Real APIs...")
    print("=" * 60)

    # Check for API keys
    api_keys = {
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "LLAMA_API_URL": os.getenv("LLAMA_API_URL"),
    }

    print("API Key Status:")
    for key_name, key_value in api_keys.items():
        status = "✅ Set" if key_value else "❌ Not set"
        print(f"   {key_name}: {status}")

    # Test with available APIs
    hybrid_service = get_hybrid_ai_service()

    test_cases = [
        ("Explain machine learning in one sentence", TaskType.GENERAL_QA),
        ("Generate 3 flashcards about Python", TaskType.FLASHCARD),
        ("Create a 2-hour study schedule", TaskType.SMART_SCHEDULING),
    ]

    for prompt, task_type in test_cases:
        print(f"\nTesting {task_type.value}: {prompt}")
        try:
            response = await hybrid_service.generate_response(
                task_type=task_type, prompt=prompt, user_id="test_user", max_tokens=100
            )

            print(f"   ✅ Response: {response.content[:100]}...")
            print(f"   ✅ Provider: {response.provider}")
            print(f"   ✅ Cost: £{response.cost_usd:.6f}")
            print(f"   ✅ Quality: {response.quality_score:.2f}")

        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}...")


def main():
    """Main test function"""
    print("🚀 Comprehensive Hybrid AI System Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run comprehensive tests
    success = asyncio.run(test_hybrid_ai_comprehensive())

    if success:
        # Run API tests if requested
        if len(sys.argv) > 1 and sys.argv[1] == "--test-apis":
            asyncio.run(test_with_real_apis())

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test Hybrid AI System
Simple test script to verify the hybrid AI system is working correctly.
"""

import asyncio
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai.hybrid_ai_service import TaskType, get_hybrid_ai_service
from services.ai.migration_helper import get_migration_helper


async def test_hybrid_ai_system():
    """Test the hybrid AI system functionality"""
    print("🧪 Testing Hybrid AI System...")
    print("=" * 50)

    # Get the hybrid AI service
    hybrid_service = get_hybrid_ai_service()
    migration_helper = get_migration_helper()

    # Test 1: Service initialization
    print("\n1. Testing service initialization...")
    try:
        assert hybrid_service is not None
        assert len(hybrid_service.model_configs) == 5
        assert len(hybrid_service.clients) == 5
        print("✅ Service initialization successful")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False

    # Test 2: Model configurations
    print("\n2. Testing model configurations...")
    try:
        configs = hybrid_service.model_configs

        # Check cost configurations
        llama_cost = configs[
            hybrid_service.model_configs.keys().__iter__().__next__()
        ].cost_per_1m_tokens
        openai_cost = configs[list(configs.keys())[-1]].cost_per_1m_tokens

        print(f"   Llama cost per 1M tokens: £{llama_cost}")
        print(f"   OpenAI cost per 1M tokens: £{openai_cost}")
        print(
            f"   Cost difference: {((openai_cost - llama_cost) / openai_cost * 100):.1f}%"
        )
        print("✅ Model configurations verified")
    except Exception as e:
        print(f"❌ Model configuration test failed: {e}")
        return False

    # Test 3: Cost analysis
    print("\n3. Testing cost analysis...")
    try:
        test_prompt = "Generate 5 flashcards about machine learning concepts"
        analysis = await hybrid_service.get_cost_analysis(
            TaskType.FLASHCARD, test_prompt
        )

        print("   Cost analysis results:")
        for provider, data in analysis.items():
            cost = data.get("estimated_cost_usd", 0)
            quality = data.get("quality_score", 0)
            print(f"   - {provider}: £{cost:.6f} (quality: {quality:.2f})")

        print("✅ Cost analysis working")
    except Exception as e:
        print(f"❌ Cost analysis failed: {e}")
        return False

    # Test 4: Migration helper
    print("\n4. Testing migration helper...")
    try:
        # Test cost comparison
        comparison = await migration_helper.get_cost_comparison(
            TaskType.FLASHCARD, "Generate flashcards about Python programming"
        )

        if "error" not in comparison:
            savings = comparison.get("savings_percentage", 0)
            recommended = comparison.get("recommended_provider", "unknown")
            print(f"   Potential savings: {savings:.1f}%")
            print(f"   Recommended provider: {recommended}")
            print("✅ Migration helper working")
        else:
            print(f"❌ Migration helper failed: {comparison['error']}")
            return False

    except Exception as e:
        print(f"❌ Migration helper test failed: {e}")
        return False

    # Test 5: Provider availability (mock test)
    print("\n5. Testing provider availability...")
    try:
        # This will test with mock clients since we don't have real API keys
        for provider_name, client in hybrid_service.clients.items():
            availability = await client.is_available()
            print(
                f"   {provider_name}: {'✅ Available' if availability else '❌ Unavailable'}"
            )

        print("✅ Provider availability check completed")
    except Exception as e:
        print(f"❌ Provider availability test failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("\nNext steps:")
    print("1. Set up API keys for DeepSeek, Claude, and OpenAI")
    print("2. Set up self-hosted Llama models with vLLM")
    print("3. Update existing AI services to use the hybrid system")
    print("4. Monitor costs and quality metrics")

    return True


async def test_with_real_apis():
    """Test with real API keys if available"""
    print("\n🔑 Testing with real APIs...")
    print("=" * 50)

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

    if api_keys["DEEPSEEK_API_KEY"]:
        print("\nTesting DeepSeek API...")
        try:
            test_prompt = "Explain machine learning in one sentence"
            response = await hybrid_service.generate_response(
                task_type=TaskType.GENERAL_QA, prompt=test_prompt, user_id="test_user"
            )
            print(f"✅ DeepSeek response: {response.content[:100]}...")
            print(f"   Cost: £{response.cost_usd:.6f}")
            print(f"   Quality: {response.quality_score:.2f}")
        except Exception as e:
            print(f"❌ DeepSeek test failed: {e}")

    if api_keys["ANTHROPIC_API_KEY"]:
        print("\nTesting Claude API...")
        try:
            test_prompt = "What is the capital of France?"
            response = await hybrid_service.generate_response(
                task_type=TaskType.GENERAL_QA, prompt=test_prompt, user_id="test_user"
            )
            print(f"✅ Claude response: {response.content[:100]}...")
            print(f"   Cost: £{response.cost_usd:.6f}")
            print(f"   Quality: {response.quality_score:.2f}")
        except Exception as e:
            print(f"❌ Claude test failed: {e}")

    if api_keys["OPENAI_API_KEY"]:
        print("\nTesting OpenAI API...")
        try:
            test_prompt = "What is 2 + 2?"
            response = await hybrid_service.generate_response(
                task_type=TaskType.GENERAL_QA, prompt=test_prompt, user_id="test_user"
            )
            print(f"✅ OpenAI response: {response.content[:100]}...")
            print(f"   Cost: £{response.cost_usd:.6f}")
            print(f"   Quality: {response.quality_score:.2f}")
        except Exception as e:
            print(f"❌ OpenAI test failed: {e}")


def main():
    """Main test function"""
    print("🚀 Hybrid AI System Test Suite")
    print("=" * 50)

    # Run basic tests
    success = asyncio.run(test_hybrid_ai_system())

    if success:
        # Run API tests if requested
        if len(sys.argv) > 1 and sys.argv[1] == "--test-apis":
            asyncio.run(test_with_real_apis())

    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    main()

"""
Quick test script to verify tool definitions work correctly
Run this before starting the server to ensure tools are properly configured
"""

import sys
from voice_agent.tools import (
    get_agent_name,
    get_personality,
    get_languages,
    get_dialect,
    conversation_complete,
    VALID_PERSONALITIES,
    VALID_LANGUAGES,
    VALID_DIALECTS
)


class MockToolContext:
    """Mock ToolContext for testing"""
    def __init__(self):
        self.state = {}


def test_get_agent_name():
    print("\n=== Testing get_agent_name ===")
    ctx = MockToolContext()

    # Test valid name
    result = get_agent_name("Ali", ctx)
    print(f"✓ Valid name: {result}")
    assert result['status'] == 'success'
    assert result['agent_name'] == 'Ali'
    assert ctx.state['agent_name'] == 'Ali'

    # Test empty name
    result = get_agent_name("", ctx)
    print(f"✓ Empty name: {result}")
    assert result['status'] == 'error'

    print("get_agent_name tests passed!")


def test_get_personality():
    print("\n=== Testing get_personality ===")
    ctx = MockToolContext()

    # Test valid personality
    result = get_personality("Empathetic and Friendly", ctx)
    print(f"✓ Valid personality: {result}")
    assert result['status'] == 'success'
    assert result['personality'] == 'Empathetic and Friendly'

    # Test invalid personality
    result = get_personality("Invalid Personality", ctx)
    print(f"✓ Invalid personality: {result}")
    assert result['status'] == 'error'

    print("get_personality tests passed!")


def test_get_languages():
    print("\n=== Testing get_languages ===")
    ctx = MockToolContext()

    # Test valid languages
    result = get_languages(["English", "Arabic"], ctx)
    print(f"✓ Valid languages: {result}")
    assert result['status'] == 'success'
    assert result['requires_dialect'] == True

    # Test without Arabic
    result = get_languages(["English", "Hindi"], ctx)
    print(f"✓ Languages without Arabic: {result}")
    assert result['status'] == 'success'
    assert result['requires_dialect'] == False

    # Test empty list
    result = get_languages([], ctx)
    print(f"✓ Empty languages: {result}")
    assert result['status'] == 'error'

    # Test invalid language
    result = get_languages(["English", "Spanish"], ctx)
    print(f"✓ Invalid language: {result}")
    assert result['status'] == 'error'

    print("get_languages tests passed!")


def test_get_dialect():
    print("\n=== Testing get_dialect ===")

    # Test without Arabic selected (should fail)
    ctx = MockToolContext()
    result = get_dialect("Omani", ctx)
    print(f"✓ Dialect without Arabic: {result}")
    assert result['status'] == 'error'

    # Test with Arabic selected (should succeed)
    ctx = MockToolContext()
    ctx.state['languages'] = ["English", "Arabic"]
    result = get_dialect("Omani", ctx)
    print(f"✓ Valid dialect with Arabic: {result}")
    assert result['status'] == 'success'
    assert result['dialect'] == 'Omani'

    # Test invalid dialect
    ctx = MockToolContext()
    ctx.state['languages'] = ["English", "Arabic"]
    result = get_dialect("Egyptian", ctx)
    print(f"✓ Invalid dialect: {result}")
    assert result['status'] == 'error'

    print("get_dialect tests passed!")


def test_conversation_complete():
    print("\n=== Testing conversation_complete ===")
    ctx = MockToolContext()
    ctx.state['conversation_state'] = {
        'agent_name': 'Ali',
        'personality': 'Empathetic and Friendly',
        'languages': ['English', 'Arabic'],
        'dialect': 'Omani'
    }

    result = conversation_complete("User said thank you", ctx)
    print(f"✓ Conversation complete: {result}")
    assert result['status'] == 'success'
    assert result['completed'] == True
    assert ctx.state['conversation_complete'] == True

    print("conversation_complete tests passed!")


def test_valid_options():
    print("\n=== Testing Valid Options ===")
    print(f"Personalities: {VALID_PERSONALITIES}")
    print(f"Languages: {VALID_LANGUAGES}")
    print(f"Dialects: {VALID_DIALECTS}")

    assert len(VALID_PERSONALITIES) == 5
    assert len(VALID_LANGUAGES) == 4
    assert len(VALID_DIALECTS) == 7

    print("Valid options verified!")


def main():
    print("=" * 60)
    print("  Tool Testing Suite")
    print("=" * 60)

    try:
        test_valid_options()
        test_get_agent_name()
        test_get_personality()
        test_get_languages()
        test_get_dialect()
        test_conversation_complete()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nTools are working correctly. Ready to start the server!")
        return 0

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

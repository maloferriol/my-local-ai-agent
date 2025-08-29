#!/usr/bin/env python3
# flake8: noqa
"""
Test script to verify the new separated structure works correctly.

Run:
    python3 -m tests.test_structure
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all the new modules can be imported correctly."""
    try:
        print("Testing imports...")

        # Test CLI module
        from cli.main import create_parser

        print("✓ CLI module imported successfully")

        # Test core modules
        #
        from core.agent import Agent
        from core.conversation import ConversationManager, Conversation, Message

        print("✓ Core modules imported successfully")

        # Test that we can create instances
        parser = create_parser()
        print("✓ Parser created successfully")

        print("\n🎉 All imports successful! The new structure is working correctly.")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_parser():
    """Test the argument parser functionality."""
    try:
        from cli.main import create_parser

        parser = create_parser()

        # Test help
        help_output = parser.format_help()
        if "My Local AI Agent" in help_output:
            print("✓ Parser help text is correct")
        else:
            print("❌ Parser help text is incorrect")
            return False

        # Test argument parsing
        test_args = ["--model", "llama2:7b", "--no-stream"]
        parsed = parser.parse_args(test_args)

        if parsed.model == "llama2:7b" and parsed.stream == False:
            print("✓ Argument parsing works correctly")
        else:
            print("❌ Argument parsing failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing the new separated structure...\n")

    print(f"Path parent parent: {str(Path(__file__).parent.parent / 'src')}")

    success = True
    success &= test_imports()
    success &= test_parser()

    if success:
        print("\n✅ All tests passed! The new structure is ready to use.")
        print("\nYou can now run the application using:")
        print("  python -m src.cli.main")
        print("  python -m src.cli.main --help")
        print("  python -m src.cli.main -m llama2:7b --no-stream")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

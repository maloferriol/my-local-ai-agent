#!/usr/bin/env python3
"""
Main entry point for the AI agent application.
This file now serves as a simple entry point that delegates to the CLI module.

Run: python -m src.main
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    # Import and run the CLI main function
    from cli.main import main

    main()
else:
    # When imported as a module, provide access to the main components
    from core.agent import Agent
    from core.conversation import ConversationManager, Conversation, ChatMessage

    __all__ = ["Agent", "ConversationManager", "Conversation", "ChatMessage"]

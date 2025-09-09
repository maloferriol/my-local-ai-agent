"""
Conversation management module.
Handles conversation state, history, metadata, and persistence.
"""

import json
import logging

from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models import Conversation, ChatMessage, Role


conversation_logger = logging.getLogger("conversations_logger")

NO_ACTIVE_CONVERSATION_MESSAGE = "No active conversation. Call start_new_conversation() first."


class ConversationManager:
    """
    Manages conversation lifecycle, state, and persistence.
    Provides high-level operations for conversation management.
    """

    def __init__(self, db_manager, init_conversation: Conversation = None):
        """
        Initialize the conversation manager.

        Args:
            db_manager: Database manager instance for persistence
        """
        self.db_manager = db_manager
        self.current_conversation: Optional[Conversation] = init_conversation
        self.conversation_history: List[Conversation] = []

        conversation_logger.info("Conversation manager initialized")

    def start_new_conversation(self, model: str = None, title: str = None) -> int:
        """_
        Start a new conversation.

        Args:
            model: The AI model being used
            title: Optional title for the conversation

        Returns:
            The conversation ID
        """
        # Create conversation in database
        conversation_id = self.db_manager.create_conversation(title=title)

        print(f"[CONV MANAGER] Created new conversation with ID: {conversation_id}")

        # Create conversation object
        now = datetime.now()
        self.current_conversation = Conversation(
            id=conversation_id,
            created_at=now,
            updated_at=now,
            title=title,
            model=model,
            metadata={},
        )

        # Add to history
        self.conversation_history.append(self.current_conversation)

        conversation_logger.info(
            "Started new conversation with ID: %s", conversation_id
        )
        return conversation_id

    def add_user_message(self, content: str, model: str = None) -> ChatMessage:
        """
        Add a user message to the current conversation.

        Args:
            content: The message content
            model: The AI model being used

        Returns:
            The created message object
        """
        if not self.current_conversation:
            raise RuntimeError(NO_ACTIVE_CONVERSATION_MESSAGE)

        message = ChatMessage(
            role=Role.USER, content=content, timestamp=datetime.now(), model=model
        )

        # Add to current conversation
        self.current_conversation.add_message(message)

        # Store in database
        step = self.current_conversation.get_message_count()
        print("step", step)
        conversation_id = (self.current_conversation.id,)
        print("conversation_id", conversation_id)
        self.db_manager.insert_message(
            conversation_id=self.current_conversation.id,
            step=step,
            role=Role.USER.value,
            content=content,
            model=model,
        )

        conversation_logger.debug(
            "Added user message: %s",
            content[:50] + "..." if len(content) > 50 else content,
        )
        return message

    def add_assistant_message(
        self,
        content: str,
        thinking: str = None,
        model: str = None,
        tool_calls: List[Dict] = None,
    ) -> ChatMessage:
        """
        Add an assistant message to the current conversation.

        Args:
            content: The message content
            thinking: The assistant's thinking process
            model: The AI model being used
            tool_calls: A list of tool calls made by the assistant

        Returns:
            The created message object
        """
        if not self.current_conversation:
            raise RuntimeError(NO_ACTIVE_CONVERSATION_MESSAGE)

        message = ChatMessage(
            role=Role.ASSISTANT,
            content=content,
            timestamp=datetime.now(),
            thinking=thinking,
            model=model,
            tool_calls=tool_calls,
        )

        # Add to current conversation
        self.current_conversation.add_message(message)

        # Store in database
        step = self.current_conversation.get_message_count()
        self.db_manager.insert_message(
            conversation_id=self.current_conversation.id,
            step=step,
            role=Role.ASSISTANT.value,
            content=content,
            thinking=thinking,
            tool_calls=json.dumps(tool_calls) if tool_calls else "",
            model=model,
        )

        conversation_logger.debug(
            "Added assistant message: %s",
            content[:50] + "..." if len(content) > 50 else content,
        )
        return message

    def add_tool_message(
        self, content: str, tool_name: str, model: str = None
    ) -> ChatMessage:
        """
        Add a tool message to the current conversation.

        Args:
            content: The tool result content
            tool_name: The name of the tool that was called
            model: The AI model being used

        Returns:
            The created message object
        """
        if not self.current_conversation:
            raise RuntimeError(NO_ACTIVE_CONVERSATION_MESSAGE)

        message = ChatMessage(
            role=Role.TOOL,
            content=content,
            timestamp=datetime.now(),
            tool_name=tool_name,
            model=model,
        )

        # Add to current conversation
        self.current_conversation.add_message(message)

        # Store in database
        step = self.current_conversation.get_message_count()
        self.db_manager.insert_message(
            conversation_id=self.current_conversation.id,
            step=step,
            role=Role.TOOL.value,
            content=content,
            tool_name=tool_name,
            model=model,
        )

        conversation_logger.debug(
            "Added tool message from %s: %s",
            tool_name,
            content[:50] + "..." if len(content) > 50 else content,
        )
        return message

    def get_current_conversation(self) -> Optional[Conversation]:
        """Get the current active conversation."""
        return self.current_conversation

    def get_conversation_history(self, limit: int = None) -> List[Conversation]:
        """
        Get conversation history.

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversations
        """
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history.copy()

    def load_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """
        Load a specific conversation by ID.

        Args:
            conversation_id: The ID of the conversation to load

        Returns:
            The loaded conversation or None if not found
        """
        # Load from database
        conversation_data = self.db_manager.get_conversation(conversation_id)
        if not conversation_data:
            conversation_logger.warning("Conversation %s not found", conversation_id)
            print(f"Conversation {conversation_id} not found")
            return None

        # Create conversation object
        conversation = Conversation(
            id=conversation_id,
            created_at=conversation_data.get("timestamp"),
            updated_at=conversation_data.get("timestamp"),
            title=conversation_data.get("title"),
        )

        # Load messages
        messages_data = self.db_manager.get_messages(conversation_id)
        for msg_data in messages_data:
            tool_calls = None
            if msg_data.get("tool_calls"):
                try:
                    tool_calls = json.loads(msg_data["tool_calls"])
                except json.JSONDecodeError:
                    conversation_logger.warning("Could not decode tool_calls JSON.")
            message = ChatMessage(
                id=msg_data["id"],
                role=Role(msg_data["role"]),
                content=msg_data["content"],
                timestamp=msg_data.get("timestamp", datetime.now()),
                thinking=msg_data.get("thinking"),
                tool_calls=tool_calls,
                tool_name=msg_data.get("tool_name"),
                model=msg_data.get("model"),
            )
            conversation.messages.append(message)

        # Set as current conversation
        self.current_conversation = conversation

        conversation_logger.info(
            "Loaded conversation %s with %d messages",
            conversation_id,
            len(conversation.messages),
        )
        return conversation

    def update_conversation_title(self, title: str):
        """
        Update the title of the current conversation.

        Args:
            title: New title for the conversation
        """
        if not self.current_conversation:
            raise RuntimeError("No active conversation")

        self.current_conversation.title = title
        self.current_conversation.updated_at = datetime.now()

        # Update in database if method exists
        if hasattr(self.db_manager, "update_conversation_title"):
            self.db_manager.update_conversation_title(
                self.current_conversation.id, title
            )

        conversation_logger.info("Updated conversation title to: %s", title)

    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation.

        Returns:
            Dictionary with conversation summary information
        """
        if not self.current_conversation:
            return {}

        return {
            "id": self.current_conversation.id,
            "title": self.current_conversation.title,
            "model": self.current_conversation.model,
            "message_count": self.current_conversation.get_message_count(),
            "created_at": self.current_conversation.created_at.isoformat(),
            "updated_at": self.current_conversation.updated_at.isoformat(),
            "last_message": (
                self.current_conversation.get_last_message().content
                if self.current_conversation.get_last_message()
                else None
            ),
        }

    def export_conversation(self, conversation_id: int = None) -> Dict[str, Any]:
        """
        Export a conversation to a dictionary format.

        Args:
            conversation_id: ID of conversation to export, or None for current

        Returns:
            Dictionary representation of the conversation
        """
        if conversation_id is None:
            if not self.current_conversation:
                raise RuntimeError("No active conversation")
            conversation = self.current_conversation
        else:
            conversation = self.load_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

        return conversation.to_dict()

    def close_conversation(self):
        """Close the current conversation."""
        if self.current_conversation:
            conversation_logger.info(
                "Closing conversation %s", self.current_conversation.id
            )
            self.current_conversation = None

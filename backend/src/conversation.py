"""
Conversation management module.
Handles conversation state, history, metadata, and persistence.
"""

import json
import logging

from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace

from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models import Conversation, ChatMessage, Role
from src.database.db import DatabaseManager


# Initialize tracer
tracer = trace.get_tracer(__name__)

# Initialize logging
conversation_logger = logging.getLogger("conversations_logger")

NO_ACTIVE_CONVERSATION_MESSAGE = (
    "No active conversation. Call start_new_conversation() first."
)


class ConversationManager:
    """
    Manages conversation lifecycle, state, and persistence.
    Provides high-level operations for conversation management.
    """

    def __init__(self, conversation: Conversation):
        """
        Private constructor. Use create_new or load_existing instead.
        """
        self.current_conversation = conversation
        self.conversation_history: List[Conversation] = [conversation]
        conversation_logger.info(
            f"Conversation manager initialized for conversation {conversation.id}"
        )

    @classmethod
    def create_new(cls, model: str = None, title: str = None, system_prompt: str = None, 
                   temperature: float = 0.7, max_tokens: int = None, **config):
        """
        Creates a new conversation and returns a ConversationManager instance.
        """
        # Create conversation with enhanced configuration
        conversation = Conversation(
            title=title,
            model=model,
            model_name=model,  # Ensure both fields are set
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=config.get('metadata', {}),
        )
        
        with DatabaseManager() as db:
            conversation_id = db.create_conversation(
                title=title,
                model_name=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                metadata=json.dumps(conversation.metadata) if conversation.metadata else "",
                uuid=conversation.uuid
            )
        
        now = datetime.now()
        conversation.id = conversation_id
        conversation.created_at = now
        conversation.updated_at = now
        
        return cls(conversation)

    @classmethod
    def load_existing(cls, conversation_id: int):
        """
        Loads an existing conversation and returns a ConversationManager instance.
        """
        with DatabaseManager() as db:
            conversation_data = db.get_conversation(conversation_id)
        if not conversation_data:
            conversation_logger.warning("Conversation %s not found", conversation_id)
            return None

        conversation = Conversation(
            id=conversation_id,
            created_at=conversation_data.get("timestamp"),
            updated_at=conversation_data.get("timestamp"),
            title=conversation_data.get("title"),
            model_name=conversation_data.get("model_name"),
            system_prompt=conversation_data.get("system_prompt"),
            temperature=conversation_data.get("temperature", 0.7),
            max_tokens=conversation_data.get("max_tokens"),
            metadata=json.loads(conversation_data.get("metadata", "{}")) if conversation_data.get("metadata") else {},
            uuid=conversation_data.get("uuid"),
        )

        with DatabaseManager() as db:
            messages_data = db.get_messages(conversation_id)
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
                # New Phase 1 fields
                confidence_score=msg_data.get("confidence_score"),
                token_count=msg_data.get("token_count"),
                processing_time_ms=msg_data.get("processing_time_ms"),
                metadata=json.loads(msg_data.get("metadata", "{}")) if msg_data.get("metadata") else None,
                parent_message_id=msg_data.get("parent_message_id"),
                uuid=msg_data.get("uuid"),
            )
            conversation.messages.append(message)

        return cls(conversation)

    @tracer.start_as_current_span(
        name="ConversationManager__add_user_message",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def add_user_message(self, content: str, model: str = None, **kwargs) -> ChatMessage:
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
            role=Role.USER, 
            content=content, 
            timestamp=datetime.now(), 
            model=model,
            **kwargs  # Support new fields like confidence_score, token_count, etc.
        )

        # Add to current conversation
        self.current_conversation.add_message(message)

        # Store in database
        step = self.current_conversation.get_message_count()
        print("step", step)
        conversation_id = (self.current_conversation.id,)
        print("conversation_id", conversation_id)
        with DatabaseManager() as db:
            db.insert_message(
                conversation_id=self.current_conversation.id,
                step=step,
                role=Role.USER.value,
                content=content,
                model=model,
                # Pass new fields to database
                confidence_score=message.confidence_score,
                token_count=message.token_count,
                processing_time_ms=message.processing_time_ms,
                metadata=json.dumps(message.metadata) if message.metadata else "",
                parent_message_id=message.parent_message_id,
                uuid=message.uuid,
            )

        conversation_logger.debug(
            "Added user message: %s",
            content[:50] + "..." if len(content) > 50 else content,
        )
        return message

    @tracer.start_as_current_span(
        name="ConversationManager__add_assistant_message",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def add_assistant_message(
        self,
        content: str,
        thinking: str = None,
        model: str = None,
        tool_calls: List[Dict] = None,
        **kwargs
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
            **kwargs  # Support new fields
        )

        # Add to current conversation
        self.current_conversation.add_message(message)

        # Store in database
        step = self.current_conversation.get_message_count()
        with DatabaseManager() as db:
            db.insert_message(
                conversation_id=self.current_conversation.id,
                step=step,
                role=Role.ASSISTANT.value,
                content=content,
                thinking=thinking,
                tool_calls=json.dumps(tool_calls) if tool_calls else "",
                model=model,
                # Pass new fields to database
                confidence_score=message.confidence_score,
                token_count=message.token_count,
                processing_time_ms=message.processing_time_ms,
                metadata=json.dumps(message.metadata) if message.metadata else "",
                parent_message_id=message.parent_message_id,
                uuid=message.uuid,
            )

        conversation_logger.debug(
            "Added assistant message: %s",
            content[:50] + "..." if len(content) > 50 else content,
        )
        return message

    @tracer.start_as_current_span(
        name="ConversationManager__add_user_message",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def add_tool_message(
        self, content: str, tool_name: str, model: str = None, **kwargs
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
            **kwargs  # Support new fields
        )

        # Add to current conversation
        self.current_conversation.add_message(message)

        # Store in database
        step = self.current_conversation.get_message_count()
        with DatabaseManager() as db:
            db.insert_message(
                conversation_id=self.current_conversation.id,
                step=step,
                role=Role.TOOL.value,
                content=content,
                tool_name=tool_name,
                model=model,
                # Pass new fields to database
                confidence_score=message.confidence_score,
                token_count=message.token_count,
                processing_time_ms=message.processing_time_ms,
                metadata=json.dumps(message.metadata) if message.metadata else "",
                parent_message_id=message.parent_message_id,
                uuid=message.uuid,
            )

        conversation_logger.debug(
            "Added tool message from %s: %s",
            tool_name,
            content[:50] + "..." if len(content) > 50 else content,
        )
        return message

    @tracer.start_as_current_span(
        name="ConversationManager__get_current_conversation",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def get_current_conversation(self) -> Optional[Conversation]:
        """Get the current active conversation."""
        return self.current_conversation

    @tracer.start_as_current_span(
        name="ConversationManager__get_conversation_history",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
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

    @tracer.start_as_current_span(
        name="ConversationManager__load_conversation",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def load_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """
        Load a specific conversation by ID.

        Args:
            conversation_id: The ID of the conversation to load

        Returns:
            The loaded conversation or None if not found
        """
        # Load from database
        with DatabaseManager() as db:
            conversation_data = db.get_conversation(conversation_id)
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
            model_name=conversation_data.get("model_name"),
            system_prompt=conversation_data.get("system_prompt"),
            temperature=conversation_data.get("temperature", 0.7),
            max_tokens=conversation_data.get("max_tokens"),
            metadata=json.loads(conversation_data.get("metadata", "{}")) if conversation_data.get("metadata") else {},
            uuid=conversation_data.get("uuid"),
        )

        # Load messages
        with DatabaseManager() as db:
            messages_data = db.get_messages(conversation_id)
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
                # New Phase 1 fields
                confidence_score=msg_data.get("confidence_score"),
                token_count=msg_data.get("token_count"),
                processing_time_ms=msg_data.get("processing_time_ms"),
                metadata=json.loads(msg_data.get("metadata", "{}")) if msg_data.get("metadata") else None,
                parent_message_id=msg_data.get("parent_message_id"),
                uuid=msg_data.get("uuid"),
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

    @tracer.start_as_current_span(
        name="ConversationManager__update_conversation_title",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
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
        # Optional: implement update_conversation_title in DatabaseManager
        # and call it here when available.

        conversation_logger.info("Updated conversation title to: %s", title)

    @tracer.start_as_current_span(
        name="ConversationManager__get_conversation_summary",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
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

    @tracer.start_as_current_span(
        name="ConversationManager__export_conversation",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
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

    @tracer.start_as_current_span(
        name="ConversationManager__close_conversation",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def close_conversation(self):
        """Close the current conversation."""
        if self.current_conversation:
            conversation_logger.info(
                "Closing conversation %s", self.current_conversation.id
            )
            self.current_conversation = None

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid


# Define the Enum first
class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """Represents a single message in a conversation."""

    role: Role
    content: str
    id: Optional[Union[int, str]] = None
    timestamp: Optional[datetime] = None
    thinking: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_name: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # New Phase 1 fields
    confidence_score: Optional[float] = None
    token_count: Optional[int] = None
    processing_time_ms: Optional[int] = None
    parent_message_id: Optional[Union[int, str]] = None
    uuid: Optional[str] = None

    def __post_init__(self):
        """Initialize UUID if not provided."""
        if self.uuid is None:
            self.uuid = str(uuid.uuid4())

        # Validate confidence score
        if self.confidence_score is not None:
            if not 0.0 <= self.confidence_score <= 1.0:
                raise ValueError("confidence_score must be between 0.0 and 1.0")

    def validate(self) -> bool:
        """Validate the message data."""
        print("Validating message...", self.to_dict())
        if not self.content and not self.tool_calls and not self.thinking:
            raise ValueError(
                "Message must have either content or tool_calls or thinking"
            )

        if self.token_count is not None and self.token_count < 0:
            raise ValueError("token_count cannot be negative")

        if self.processing_time_ms is not None and self.processing_time_ms < 0:
            raise ValueError("processing_time_ms cannot be negative")

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        data = asdict(self)
        if isinstance(data.get("role"), Enum):
            data["role"] = data["role"].value

        # Serialize datetime if present
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()

        # Filter out None values for cleaner API payloads
        return {k: v for k, v in data.items() if v is not None}

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """Get a specific metadata value."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)

    def set_metadata_value(self, key: str, value: Any) -> None:
        """Set a specific metadata value."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value


@dataclass
class Conversation:
    """Represents a conversation session."""

    id: Optional[Union[int, str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    title: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    messages: List[ChatMessage] = field(default_factory=list)
    # New Phase 1 fields
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    uuid: Optional[str] = None

    def __post_init__(self):
        """Initialize UUID if not provided and set defaults."""
        if self.uuid is None:
            self.uuid = str(uuid.uuid4())

        # Sync model fields for backward compatibility
        if self.model_name is None and self.model is not None:
            self.model_name = self.model
        elif self.model is None and self.model_name is not None:
            self.model = self.model_name

        # Validate temperature
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")

    def validate(self) -> bool:
        """Validate the conversation data."""
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        return True

    def add_message(self, message: ChatMessage):
        """Add a message to the conversation."""
        # Validate message before adding
        message.validate()
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_last_message(self) -> Optional[ChatMessage]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None

    def get_message_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return len(self.messages)

    def get_messages_by_role(self, role: Role) -> List[ChatMessage]:
        """Get all messages of a specific role."""
        return [msg for msg in self.messages if msg.role == role]

    def get_total_tokens(self) -> int:
        """Get total token count for all messages."""
        return sum(msg.token_count or 0 for msg in self.messages)

    def get_conversation_config(self) -> Dict[str, Any]:
        """Get conversation configuration as dictionary."""
        return {
            "model_name": self.model_name,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def update_config(self, **config: Any) -> None:
        """Update conversation configuration."""
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary format."""
        conv_dict = asdict(self)

        # Serialize datetime fields
        if self.created_at:
            conv_dict["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            conv_dict["updated_at"] = self.updated_at.isoformat()

        if self.messages:
            conv_dict["messages"] = [m.to_dict() for m in self.messages]

        return conv_dict

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """Get a specific metadata value."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)

    def set_metadata_value(self, key: str, value: Any) -> None:
        """Set a specific metadata value."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
        self.updated_at = datetime.now()

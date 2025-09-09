from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum


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
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    thinking: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_name: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        data = asdict(self)
        if isinstance(data.get("role"), Enum):
            data["role"] = data["role"].value

        # if isinstance(data.get("timestamp"), datetime):
        #     # here seriallize datetime
        #     data["timestamp"] = data["timestamp"].timestamp
        # Filter out None values for cleaner API payloads
        res = {k: v for k, v in data.items() if v is not None}
        print("res", res)
        return res


@dataclass
class Conversation:
    """Represents a conversation session."""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    title: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    messages: List[ChatMessage] = field(default_factory=list)

    def add_message(self, message: ChatMessage):
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_last_message(self) -> Optional[ChatMessage]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None

    def get_message_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return len(self.messages)

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary format."""
        conv_dict = asdict(self)
        if self.messages:
            conv_dict["messages"] = [m.to_dict() for m in self.messages]
        return conv_dict

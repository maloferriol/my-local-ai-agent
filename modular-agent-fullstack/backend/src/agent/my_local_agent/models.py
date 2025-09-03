
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Define the Enum first
class Role(Enum):
    USER = 'user'
    ASSISTANT = 'asssitant'
    SYSTEM = 'system'
    TOOL = 'tool'


@dataclass
class ChatMessage:
    """Represents a single message in a conversation."""
    id: str
    role: Role
    content: str
    timestamp: Optional[datetime] = None
    thinking: Optional[str] = None
    tool_name: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return asdict(self)

@dataclass
class Conversation:
    """Represents a conversation session."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    title: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    messages: List[ChatMessage] = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []

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
        return asdict(self)
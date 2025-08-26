from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from models.message import Message

@dataclass
class Conversation:
    """Represents a conversation session."""
    id: int
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    messages: List[Message] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
    
    def add_message(self, message: Message):
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_last_message(self) -> Optional[Message]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None
    
    def get_message_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return len(self.messages)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary format."""
        return asdict(self)
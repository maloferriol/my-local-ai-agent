from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ChatMessage:
    """Represents a single message in a conversation."""

    role: str
    content: str
    timestamp: datetime
    thinking: Optional[str] = None
    tool_name: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return asdict(self)

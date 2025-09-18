"""
Model package initialization.
Export all models for easy importing.
"""

# Import existing models from models.py in the parent src directory
# Using importlib to avoid circular import issues
import importlib.util
from pathlib import Path

# Import new Phase 2 models
from .planning import AgentPlan, PlanStep, PlanStatus
from .tracing import ExecutionTrace, ExecutionSpan, SpanStatus

# Get path to models.py in parent directory
models_file = Path(__file__).parent.parent / "models.py"
spec = importlib.util.spec_from_file_location("src_models", models_file)
models_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models_module)

# Extract the classes we need
Role = models_module.Role
ChatMessage = models_module.ChatMessage
Conversation = models_module.Conversation


__all__ = [
    # Core models
    "Role",
    "ChatMessage",
    "Conversation",
    # Planning models
    "AgentPlan",
    "PlanStep",
    "PlanStatus",
    # Tracing models
    "ExecutionTrace",
    "ExecutionSpan",
    "SpanStatus",
]

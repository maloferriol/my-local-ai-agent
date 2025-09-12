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
from src.models.planning import AgentPlan, PlanStep, PlanStatus
from src.models.tracing import ExecutionTrace, ExecutionSpan, SpanStatus
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

        # Phase 2 enhancements - Planning and Tracing
        self.current_plan: Optional[AgentPlan] = None
        self.current_trace: Optional[ExecutionTrace] = None
        self.execution_history: List[ExecutionTrace] = []
        self.plan_history: List[AgentPlan] = []

        conversation_logger.info(
            f"Conversation manager initialized for conversation {conversation.id}"
        )

    @classmethod
    def create_new(
        cls,
        model: str = None,
        title: str = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        **config,
    ):
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
            metadata=config.get("metadata", {}),
        )

        with DatabaseManager() as db:
            conversation_id = db.create_conversation(
                title=title,
                model_name=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                metadata=(
                    json.dumps(conversation.metadata) if conversation.metadata else ""
                ),
                uuid=conversation.uuid,
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
            metadata=(
                json.loads(conversation_data.get("metadata", "{}"))
                if conversation_data.get("metadata")
                else {}
            ),
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
                metadata=(
                    json.loads(msg_data.get("metadata", "{}"))
                    if msg_data.get("metadata")
                    else None
                ),
                parent_message_id=msg_data.get("parent_message_id"),
                uuid=msg_data.get("uuid"),
            )
            conversation.messages.append(message)

        return cls(conversation)

    @tracer.start_as_current_span(
        name="ConversationManager__add_user_message",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def add_user_message(
        self, content: str, model: str = None, **kwargs
    ) -> ChatMessage:
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
            **kwargs,  # Support new fields like confidence_score, token_count, etc.
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
        **kwargs,
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
            **kwargs,  # Support new fields
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
            **kwargs,  # Support new fields
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
            metadata=(
                json.loads(conversation_data.get("metadata", "{}"))
                if conversation_data.get("metadata")
                else {}
            ),
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
                metadata=(
                    json.loads(msg_data.get("metadata", "{}"))
                    if msg_data.get("metadata")
                    else None
                ),
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

    # Phase 2 Methods - Planning Integration

    @tracer.start_as_current_span(
        name="ConversationManager__create_plan",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def create_plan(
        self, title: str, description: str, steps: List[Dict[str, Any]] = None
    ) -> AgentPlan:
        """
        Create a new execution plan for the conversation.

        Args:
            title: Plan title
            description: Plan description
            steps: Optional list of step dictionaries

        Returns:
            Created AgentPlan instance
        """
        plan = AgentPlan(
            id="",  # Will be auto-generated
            title=title,
            description=description,
            conversation_id=(
                self.current_conversation.uuid if self.current_conversation else None
            ),
        )

        # Add steps if provided
        if steps:
            for step_data in steps:
                step = PlanStep(
                    id="",  # Will be auto-generated
                    title=step_data.get("title", ""),
                    description=step_data.get("description", ""),
                    dependencies=set(step_data.get("dependencies", [])),
                    priority=step_data.get("priority", 0),
                    estimated_duration_ms=step_data.get("estimated_duration_ms"),
                )
                plan.add_step(step)

        self.current_plan = plan
        self.plan_history.append(plan)

        conversation_logger.info(f"Created plan '{title}' with {len(plan.steps)} steps")
        return plan

    @tracer.start_as_current_span(
        name="ConversationManager__execute_plan",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def execute_plan(self, plan: AgentPlan = None) -> AgentPlan:
        """
        Execute a plan by running its steps in dependency order.

        Args:
            plan: Plan to execute, or current plan if None

        Returns:
            Updated plan with execution results
        """
        if plan is None:
            plan = self.current_plan

        if not plan:
            raise ValueError("No plan provided and no current plan available")

        plan.start_execution()
        conversation_logger.info(f"Starting execution of plan '{plan.title}'")

        # Simple execution loop - in a real implementation this would
        # integrate with the agent's execution engine
        while True:
            next_steps = plan.get_next_steps()
            if not next_steps:
                # Check if we have failed steps that can be retried
                retry_steps = plan.get_retry_candidates()
                if retry_steps and plan.auto_retry_failed_steps:
                    for step in retry_steps:
                        step.reset_for_retry()
                        conversation_logger.info(f"Retrying step '{step.title}'")
                    continue
                else:
                    break

            for step in next_steps:
                step.start_execution()
                conversation_logger.info(f"Executing step '{step.title}'")

                try:
                    # In a real implementation, this would call the actual
                    # execution logic based on step configuration
                    # For now, we'll mark steps as completed
                    step.complete_execution(f"Step '{step.title}' completed")
                except Exception as e:
                    step.fail_execution(str(e))
                    conversation_logger.error(f"Step '{step.title}' failed: {e}")

        if plan.is_complete():
            plan.complete_execution("Plan completed successfully")
        elif plan.has_failed_steps():
            plan.fail_execution()

        conversation_logger.info(
            f"Plan execution finished. Success rate: {plan.success_rate}"
        )
        return plan

    def get_current_plan(self) -> Optional[AgentPlan]:
        """Get the current execution plan."""
        return self.current_plan

    def get_plan_history(self) -> List[AgentPlan]:
        """Get history of all plans created in this conversation."""
        return self.plan_history.copy()

    # Phase 2 Methods - Tracing Integration

    @tracer.start_as_current_span(
        name="ConversationManager__start_trace",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def start_trace(self, name: str, description: str = "") -> ExecutionTrace:
        """
        Start a new execution trace for detailed monitoring.

        Args:
            name: Trace name
            description: Trace description

        Returns:
            Created ExecutionTrace instance
        """
        trace = ExecutionTrace(
            trace_id="",  # Will be auto-generated
            name=name,
            description=description,
            conversation_id=(
                self.current_conversation.uuid if self.current_conversation else None
            ),
            plan_id=self.current_plan.id if self.current_plan else None,
        )

        trace.start()
        self.current_trace = trace

        conversation_logger.info(f"Started execution trace '{name}'")
        return trace

    def create_span(
        self, operation_name: str, parent_span_id: str = None
    ) -> ExecutionSpan:
        """
        Create a new execution span within the current trace.

        Args:
            operation_name: Name of the operation being traced
            parent_span_id: ID of parent span, or None for root span

        Returns:
            Created ExecutionSpan instance
        """
        if not self.current_trace:
            raise ValueError("No active trace. Call start_trace() first.")

        if parent_span_id:
            span = self.current_trace.create_child_span(parent_span_id, operation_name)
        else:
            span = self.current_trace.create_root_span(operation_name)

        return span

    def end_trace(self) -> ExecutionTrace:
        """
        End the current execution trace and add it to history.

        Returns:
            Completed ExecutionTrace instance
        """
        if not self.current_trace:
            raise ValueError("No active trace to end")

        self.current_trace.end()
        self.execution_history.append(self.current_trace)

        conversation_logger.info(
            f"Ended trace '{self.current_trace.name}'. "
            f"Duration: {self.current_trace.total_duration_ms}ms, "
            f"Success: {self.current_trace.success}"
        )

        completed_trace = self.current_trace
        self.current_trace = None
        return completed_trace

    def get_current_trace(self) -> Optional[ExecutionTrace]:
        """Get the current execution trace."""
        return self.current_trace

    def get_execution_history(self) -> List[ExecutionTrace]:
        """Get history of all execution traces."""
        return self.execution_history.copy()

    # Enhanced Summary Methods

    @tracer.start_as_current_span(
        name="ConversationManager__get_enhanced_summary",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    )
    def get_enhanced_summary(self) -> Dict[str, Any]:
        """
        Get an enhanced summary including planning and tracing information.

        Returns:
            Comprehensive conversation summary
        """
        base_summary = self.get_conversation_summary()

        # Add planning information
        planning_summary = {
            "current_plan": (
                self.current_plan.get_execution_summary() if self.current_plan else None
            ),
            "total_plans": len(self.plan_history),
            "completed_plans": sum(
                1 for plan in self.plan_history if plan.status == PlanStatus.COMPLETED
            ),
        }

        # Add tracing information
        tracing_summary = {
            "current_trace": (
                self.current_trace.get_trace_summary() if self.current_trace else None
            ),
            "total_traces": len(self.execution_history),
            "successful_traces": sum(
                1 for trace in self.execution_history if trace.success
            ),
            "total_execution_time_ms": sum(
                trace.total_duration_ms or 0 for trace in self.execution_history
            ),
        }

        # Add performance metrics
        performance_summary = {
            "average_message_tokens": (
                self.current_conversation.get_total_tokens()
                / max(self.current_conversation.get_message_count(), 1)
                if self.current_conversation
                else 0
            ),
            "total_tokens": (
                self.current_conversation.get_total_tokens()
                if self.current_conversation
                else 0
            ),
        }

        return {
            **base_summary,
            "planning": planning_summary,
            "tracing": tracing_summary,
            "performance": performance_summary,
        }

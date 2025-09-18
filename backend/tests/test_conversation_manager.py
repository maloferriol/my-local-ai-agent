"""
Unit tests for the ConversationManager class.
"""

import pytest
import json

from src.conversation import ConversationManager
from src.models import Role

# Import the function from conftest
from .conftest import managed_db_connection


@pytest.fixture(scope="function")
def db_manager_fixture(clean_db_manager):
    """
    Pytest fixture to set up an in-memory SQLite database for a single test function.
    Uses the global clean_db_manager fixture for proper resource management.
    """
    return clean_db_manager


@pytest.fixture(scope="function")
def conversation_manager_fixture(db_manager_fixture):
    """
    Pytest fixture that provides a ConversationManager instance initialized
    with a clean, in-memory database.
    """
    # Ensure the fixture database has tables
    db_manager_fixture.create_init_tables()

    # Create a new conversation using the class method
    return ConversationManager.create_new(title="Test Conversation", model="test-model")


def test_create_new_conversation(conversation_manager_fixture, db_manager_fixture):
    """
    Test that ConversationManager.create_new creates a conversation in the object
    and the database.
    """
    # The fixture already creates a conversation, so we test that it worked
    current_convo = conversation_manager_fixture.get_current_conversation()
    assert current_convo is not None
    assert isinstance(current_convo.id, int)
    assert current_convo.title == "Test Conversation"
    assert current_convo.model == "test-model"

    # Test creating another conversation
    new_manager = ConversationManager.create_new(
        title="Another Test", model="another-model"
    )
    new_convo = new_manager.get_current_conversation()
    assert new_convo.title == "Another Test"
    assert new_convo.model == "another-model"


def test_add_user_message(conversation_manager_fixture, db_manager_fixture):
    """
    Test that add_user_message adds a message to the current conversation
    and persists it to the database.
    """
    # Arrange: The fixture already provides a conversation
    conversation_id = conversation_manager_fixture.get_current_conversation().id
    message_content = "Hello, this is a test."
    message_model = "test-model"

    # Act
    added_message = conversation_manager_fixture.add_user_message(
        content=message_content, model=message_model
    )

    # Assert on the returned object
    assert added_message is not None
    assert added_message.role == Role.USER
    assert added_message.content == message_content

    # Assert on the internal state of the conversation object
    current_convo = conversation_manager_fixture.get_current_conversation()
    assert current_convo.get_message_count() == 1
    last_message = current_convo.get_last_message()
    assert last_message.role == Role.USER
    assert last_message.content == message_content

    # Assert that it was persisted correctly in the database
    db_messages = db_manager_fixture.get_messages(conversation_id)
    assert len(db_messages) == 1
    db_message = db_messages[0]
    assert db_message["role"] == "user"
    assert db_message["content"] == message_content
    assert db_message["step"] == 1


def test_add_assistant_message(conversation_manager_fixture, db_manager_fixture):
    """
    Test that add_assistant_message adds a message with thinking and tool_calls
    and persists it correctly.
    """
    # Arrange
    conversation_id = conversation_manager_fixture.get_current_conversation().id
    # Add a user message first to make the conversation realistic
    conversation_manager_fixture.add_user_message("User message", "test-model")

    content = "Assistant response."
    thinking = "I am thinking about the response."
    tool_calls = [
        {"function": {"name": "get_weather", "arguments": {"city": "London"}}}
    ]
    model = "test-model-assistant"

    # Act
    added_message = conversation_manager_fixture.add_assistant_message(
        content=content, thinking=thinking, model=model, tool_calls=tool_calls
    )

    # Assert on returned object
    assert added_message.role == Role.ASSISTANT
    assert added_message.content == content
    assert added_message.thinking == thinking
    assert added_message.tool_calls == tool_calls

    # Assert on internal state
    current_convo = conversation_manager_fixture.get_current_conversation()
    assert current_convo.get_message_count() == 2

    # Assert on database persistence
    db_messages = db_manager_fixture.get_messages(conversation_id)
    assert len(db_messages) == 2
    db_message = db_messages[1]  # The assistant message is the second one
    assert db_message["role"] == "assistant"
    assert db_message["content"] == content
    assert db_message["thinking"] == thinking
    assert db_message["tool_calls"] == json.dumps(tool_calls)
    assert db_message["step"] == 2


def test_add_tool_message(conversation_manager_fixture, db_manager_fixture):
    """
    Test that add_tool_message adds a message and persists it correctly.
    """
    # Arrange
    conversation_id = conversation_manager_fixture.get_current_conversation().id
    tool_name = "get_weather"
    content = "The weather is sunny."

    # Act
    added_message = conversation_manager_fixture.add_tool_message(
        content=content, tool_name=tool_name
    )

    # Assert on returned object
    assert added_message.role == Role.TOOL
    assert added_message.content == content
    assert added_message.tool_name == tool_name

    # Assert on database persistence
    db_messages = db_manager_fixture.get_messages(conversation_id)
    assert len(db_messages) == 1
    db_message = db_messages[0]
    assert db_message["role"] == "tool"
    assert db_message["content"] == content
    assert db_message["tool_name"] == tool_name
    assert db_message["step"] == 1


def test_load_conversation():
    """
    Test that load_conversation correctly reconstructs a conversation
    from the database, including all its messages.
    """
    # Arrange: Manually populate the database to simulate a past conversation
    with managed_db_connection() as db:
        conv_id = db.create_conversation(title="Old Conversation")
        db.insert_message(conv_id, 1, "user", "Hello")
        db.insert_message(
            conv_id,
            2,
            "assistant",
            "Hi there",
            tool_calls=json.dumps([{"name": "test"}]),
        )

    # Act
    loaded_manager = ConversationManager.load_existing(conv_id)
    loaded_convo = loaded_manager.get_current_conversation()
    messages = loaded_convo.messages

    # Assert
    assert loaded_convo is not None
    assert loaded_convo.id == conv_id
    assert loaded_convo.title == "Old Conversation"
    assert loaded_convo.get_message_count() == 2
    assert messages[0].role == Role.USER
    assert messages[1].role == Role.ASSISTANT
    assert messages[1].tool_calls == [{"name": "test"}]


def test_load_non_existent_conversation():
    """
    Test that load_existing returns None for a non-existent ID.
    """
    loaded_manager = ConversationManager.load_existing(999)
    assert loaded_manager is None


def test_update_conversation_title(conversation_manager_fixture, db_manager_fixture):
    """
    Test that update_conversation_title updates the title on the in-memory object
    but does not persist to DB if the DB method is missing.
    """
    # Arrange
    conversation_id = conversation_manager_fixture.get_current_conversation().id
    new_title = "Updated Title"

    # Act
    conversation_manager_fixture.update_conversation_title(new_title)

    # Assert on the in-memory object
    current_convo = conversation_manager_fixture.get_current_conversation()
    assert current_convo.title == new_title

    # Assert that the database was NOT updated
    db_convo = db_manager_fixture.get_conversation(conversation_id)
    assert db_convo["title"] == "Test Conversation"  # Original title from fixture


@pytest.mark.parametrize(
    "add_message_method, args",
    [
        ("add_user_message", {"content": "test"}),
        ("add_assistant_message", {"content": "test"}),
        ("add_tool_message", {"content": "test", "tool_name": "test_tool"}),
    ],
)
def test_add_message_without_active_conversation(add_message_method, args):
    """
    Test that trying to add any message without an active conversation
    raises a RuntimeError.
    """
    # Arrange: Create a manager with no active conversation
    manager = ConversationManager.create_new(title="Test", model="test")
    # Set current conversation to None to simulate no active conversation
    manager.current_conversation = None

    method_to_call = getattr(manager, add_message_method)
    expected_error = "No active conversation"

    # Act & Assert
    with pytest.raises(RuntimeError, match=expected_error):
        method_to_call(**args)


def test_json_decode_error_in_load_existing():
    """
    Test that load_existing handles JSON decode errors in tool_calls gracefully.
    """
    # Arrange: Create conversation with malformed JSON tool_calls
    with managed_db_connection() as db:
        conv_id = db.create_conversation(title="JSON Error Test")
        db.insert_message(
            conv_id, 1, "assistant", "Response", tool_calls="invalid json"
        )

    # Act
    loaded_manager = ConversationManager.load_existing(conv_id)

    # Assert - should load successfully with tool_calls as None
    assert loaded_manager is not None
    loaded_convo = loaded_manager.get_current_conversation()
    assert loaded_convo.get_message_count() == 1
    assert loaded_convo.messages[0].tool_calls is None


def test_get_conversation_history_with_limit(conversation_manager_fixture):
    """
    Test get_conversation_history with limit parameter.
    """
    # Arrange - create additional conversations for history
    manager2 = ConversationManager.create_new(title="Second", model="test")
    manager3 = ConversationManager.create_new(title="Third", model="test")

    # Add all to first manager's history manually for testing
    conversation_manager_fixture.conversation_history.extend(
        [manager2.current_conversation, manager3.current_conversation]
    )

    # Act & Assert - no limit returns all
    all_history = conversation_manager_fixture.get_conversation_history()
    assert len(all_history) == 3

    # Act & Assert - with limit
    limited_history = conversation_manager_fixture.get_conversation_history(limit=2)
    assert len(limited_history) == 2
    assert limited_history == conversation_manager_fixture.conversation_history[-2:]


def test_load_conversation_method(conversation_manager_fixture, db_manager_fixture):
    """
    Test the load_conversation instance method.
    """
    # Arrange - create a second conversation in DB
    with managed_db_connection() as db:
        conv_id = db.create_conversation(title="Second Conversation")
        db.insert_message(conv_id, 1, "user", "Hello second")

    # Act
    loaded_convo = conversation_manager_fixture.load_conversation(conv_id)

    # Assert
    assert loaded_convo is not None
    assert loaded_convo.id == conv_id
    assert loaded_convo.title == "Second Conversation"
    assert conversation_manager_fixture.current_conversation == loaded_convo
    assert loaded_convo.get_message_count() == 1


def test_load_conversation_not_found(conversation_manager_fixture):
    """
    Test load_conversation with non-existent ID returns None.
    """
    result = conversation_manager_fixture.load_conversation(999)
    assert result is None


def test_update_conversation_title_no_active_conversation():
    """
    Test update_conversation_title raises error when no active conversation.
    """
    manager = ConversationManager.create_new(title="Test", model="test")
    manager.current_conversation = None

    with pytest.raises(RuntimeError, match="No active conversation"):
        manager.update_conversation_title("New Title")


def test_get_conversation_summary_no_active_conversation():
    """
    Test get_conversation_summary returns empty dict when no active conversation.
    """
    manager = ConversationManager.create_new(title="Test", model="test")
    manager.current_conversation = None

    summary = manager.get_conversation_summary()
    assert summary == {}


def test_get_conversation_summary_with_messages(conversation_manager_fixture):
    """
    Test get_conversation_summary with messages.
    """
    # Arrange - add messages
    conversation_manager_fixture.add_user_message("First message", "test")
    conversation_manager_fixture.add_assistant_message("Response", model="test")

    # Act
    summary = conversation_manager_fixture.get_conversation_summary()

    # Assert
    assert summary["message_count"] == 2
    assert summary["last_message"] == "Response"
    assert "id" in summary
    assert "title" in summary
    assert "model" in summary
    assert "created_at" in summary
    assert "updated_at" in summary


def test_export_conversation_current(conversation_manager_fixture):
    """
    Test export_conversation for current conversation.
    """
    # Arrange - add a message
    conversation_manager_fixture.add_user_message("Test export", "test")

    # Act
    exported = conversation_manager_fixture.export_conversation()

    # Assert
    assert "id" in exported
    assert exported["title"] == "Test Conversation"
    assert "messages" in exported
    assert len(exported["messages"]) == 1


def test_export_conversation_not_found():
    """
    Test export_conversation with non-existent ID raises error.
    """
    manager = ConversationManager.create_new(title="Test", model="test")

    with pytest.raises(ValueError, match="Conversation 999 not found"):
        manager.export_conversation(999)


def test_export_conversation_no_active():
    """
    Test export_conversation without active conversation raises error.
    """
    manager = ConversationManager.create_new(title="Test", model="test")
    manager.current_conversation = None

    with pytest.raises(RuntimeError, match="No active conversation"):
        manager.export_conversation()


def test_close_conversation(conversation_manager_fixture):
    """
    Test close_conversation method.
    """
    # Ensure we have an active conversation
    assert conversation_manager_fixture.current_conversation is not None

    # Act
    conversation_manager_fixture.close_conversation()

    # Assert
    assert conversation_manager_fixture.current_conversation is None


def test_close_conversation_already_none():
    """
    Test close_conversation when already None doesn't crash.
    """
    manager = ConversationManager.create_new(title="Test", model="test")
    manager.current_conversation = None

    # Should not raise error
    manager.close_conversation()
    assert manager.current_conversation is None


# Phase 2 Planning Tests


def test_create_plan(conversation_manager_fixture):
    """
    Test creating a new execution plan.
    """
    # Act
    plan = conversation_manager_fixture.create_plan(
        title="Test Plan",
        description="A test plan",
        steps=[
            {"title": "Step 1", "description": "First step", "priority": 1},
            {"title": "Step 2", "description": "Second step", "priority": 2},
        ],
    )

    # Assert
    assert plan is not None
    assert plan.title == "Test Plan"
    assert plan.description == "A test plan"
    assert len(plan.steps) == 2
    assert conversation_manager_fixture.current_plan == plan
    assert plan in conversation_manager_fixture.plan_history


def test_create_plan_no_steps(conversation_manager_fixture):
    """
    Test creating a plan without steps.
    """
    plan = conversation_manager_fixture.create_plan(
        title="Empty Plan", description="Plan with no steps"
    )

    assert len(plan.steps) == 0


def test_execute_plan(conversation_manager_fixture):
    """
    Test executing a plan.
    """
    # Arrange
    plan = conversation_manager_fixture.create_plan(
        title="Execute Test",
        description="Test execution",
        steps=[{"title": "Test Step", "description": "Step to execute"}],
    )

    # Act
    result = conversation_manager_fixture.execute_plan(plan)

    # Assert
    assert result == plan
    assert plan.is_complete() or plan.has_failed_steps()


def test_execute_plan_current(conversation_manager_fixture):
    """
    Test executing current plan.
    """
    # Arrange
    conversation_manager_fixture.create_plan(
        title="Current Plan",
        description="Test current plan execution",
        steps=[{"title": "Current Step", "description": "Step to execute"}],
    )

    # Act - execute without specifying plan
    result = conversation_manager_fixture.execute_plan()

    # Assert
    assert result is not None


def test_execute_plan_no_plan_available(conversation_manager_fixture):
    """
    Test executing plan when no plan is available.
    """
    with pytest.raises(
        ValueError, match="No plan provided and no current plan available"
    ):
        conversation_manager_fixture.execute_plan()


def test_get_current_plan(conversation_manager_fixture):
    """
    Test get_current_plan method.
    """
    # Initially None
    assert conversation_manager_fixture.get_current_plan() is None

    # Create plan
    plan = conversation_manager_fixture.create_plan("Test", "Description")
    assert conversation_manager_fixture.get_current_plan() == plan


def test_get_plan_history(conversation_manager_fixture):
    """
    Test get_plan_history method.
    """
    # Initially empty
    assert len(conversation_manager_fixture.get_plan_history()) == 0

    # Create plans
    plan1 = conversation_manager_fixture.create_plan("Plan 1", "First plan")
    plan2 = conversation_manager_fixture.create_plan("Plan 2", "Second plan")

    history = conversation_manager_fixture.get_plan_history()
    assert len(history) == 2
    assert plan1 in history
    assert plan2 in history


# Phase 2 Tracing Tests


def test_start_trace(conversation_manager_fixture):
    """
    Test starting an execution trace.
    """
    # Act
    trace = conversation_manager_fixture.start_trace(
        name="Test Trace", description="A test trace"
    )

    # Assert
    assert trace is not None
    assert trace.name == "Test Trace"
    assert trace.description == "A test trace"
    assert conversation_manager_fixture.current_trace == trace


def test_create_span(conversation_manager_fixture):
    """
    Test creating execution spans.
    """
    # Arrange
    conversation_manager_fixture.start_trace("Test Trace")

    # Act - create root span
    root_span = conversation_manager_fixture.create_span("root_operation")

    # Assert
    assert root_span is not None
    assert root_span.operation_name == "root_operation"


def test_create_span_with_parent(conversation_manager_fixture):
    """
    Test creating child spans.
    """
    # Arrange
    conversation_manager_fixture.start_trace("Test Trace")
    root_span = conversation_manager_fixture.create_span("root_operation")

    # Act - create child span
    child_span = conversation_manager_fixture.create_span(
        "child_operation", parent_span_id=root_span.span_id
    )

    # Assert
    assert child_span is not None
    assert child_span.operation_name == "child_operation"


def test_create_span_no_active_trace(conversation_manager_fixture):
    """
    Test creating span without active trace raises error.
    """
    with pytest.raises(ValueError, match="No active trace"):
        conversation_manager_fixture.create_span("test_operation")


def test_end_trace(conversation_manager_fixture):
    """
    Test ending an execution trace.
    """
    # Arrange
    trace = conversation_manager_fixture.start_trace("Test Trace")

    # Act
    ended_trace = conversation_manager_fixture.end_trace()

    # Assert
    assert ended_trace == trace
    assert conversation_manager_fixture.current_trace is None
    assert trace in conversation_manager_fixture.execution_history


def test_end_trace_no_active_trace(conversation_manager_fixture):
    """
    Test ending trace when no active trace raises error.
    """
    with pytest.raises(ValueError, match="No active trace to end"):
        conversation_manager_fixture.end_trace()


def test_get_current_trace(conversation_manager_fixture):
    """
    Test get_current_trace method.
    """
    # Initially None
    assert conversation_manager_fixture.get_current_trace() is None

    # Start trace
    trace = conversation_manager_fixture.start_trace("Test Trace")
    assert conversation_manager_fixture.get_current_trace() == trace


def test_get_execution_history(conversation_manager_fixture):
    """
    Test get_execution_history method.
    """
    # Initially empty
    assert len(conversation_manager_fixture.get_execution_history()) == 0

    # Create and end traces
    trace1 = conversation_manager_fixture.start_trace("Trace 1")
    conversation_manager_fixture.end_trace()

    trace2 = conversation_manager_fixture.start_trace("Trace 2")
    conversation_manager_fixture.end_trace()

    history = conversation_manager_fixture.get_execution_history()
    assert len(history) == 2
    assert trace1 in history
    assert trace2 in history


def test_get_enhanced_summary(conversation_manager_fixture):
    """
    Test get_enhanced_summary with planning and tracing info.
    """
    # Arrange - add messages, plans, and traces
    conversation_manager_fixture.add_user_message("Test message", "test")
    conversation_manager_fixture.create_plan("Test Plan", "Description")

    conversation_manager_fixture.start_trace("Test Trace")
    conversation_manager_fixture.end_trace()

    # Act
    summary = conversation_manager_fixture.get_enhanced_summary()

    # Assert
    assert "planning" in summary
    assert "tracing" in summary
    assert "performance" in summary
    assert summary["planning"]["total_plans"] == 1
    assert summary["tracing"]["total_traces"] == 1
    assert summary["performance"]["total_tokens"] >= 0

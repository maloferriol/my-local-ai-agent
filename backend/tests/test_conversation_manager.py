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

    # Assert that the database was NOT updated (since the method doesn't implement DB updates)
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

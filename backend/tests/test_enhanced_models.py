"""
Unit tests for Phase 1 enhanced models (ChatMessage and Conversation).
"""

import pytest
from datetime import datetime

from src.models import ChatMessage, Conversation, Role
from src.conversation import ConversationManager
from src.database.db import DatabaseManager


@pytest.fixture(scope="function")
def test_db_manager():
    """
    Pytest fixture to set up an in-memory SQLite database for a single test function.
    """
    db_manager = DatabaseManager(db_file=":memory:")
    db_manager.connect()
    db_manager.create_init_tables()
    yield db_manager
    db_manager.close()


class TestEnhancedChatMessage:
    """Test enhanced ChatMessage functionality."""

    def test_message_creation_with_new_fields(self):
        """Test creating a ChatMessage with enhanced Phase 1 fields."""
        message = ChatMessage(
            role=Role.USER,
            content="Test message",
            confidence_score=0.95,
            token_count=4,
            processing_time_ms=150,
            metadata={"key": "value"},
        )

        assert message.role == Role.USER
        assert message.content == "Test message"
        assert message.confidence_score == pytest.approx(0.95)
        assert message.token_count == 4
        assert message.processing_time_ms == 150
        assert message.metadata == {"key": "value"}
        assert message.uuid is not None
        assert len(message.uuid) == 36  # UUID4 format

    def test_message_uuid_auto_generation(self):
        """Test that UUID is automatically generated if not provided."""
        msg1 = ChatMessage(role=Role.USER, content="Test 1")
        msg2 = ChatMessage(role=Role.USER, content="Test 2")

        assert msg1.uuid is not None
        assert msg2.uuid is not None
        assert msg1.uuid != msg2.uuid

    def test_message_validation_success(self):
        """Test successful message validation."""
        message = ChatMessage(
            role=Role.USER,
            content="Valid message",
            confidence_score=0.5,
            token_count=10,
            processing_time_ms=100,
        )

        assert message.validate() is True

    def test_message_validation_confidence_score_bounds(self):
        """Test validation fails for invalid confidence scores."""
        with pytest.raises(
            ValueError, match="confidence_score must be between 0.0 and 1.0"
        ):
            ChatMessage(role=Role.USER, content="Test", confidence_score=1.5)

        with pytest.raises(
            ValueError, match="confidence_score must be between 0.0 and 1.0"
        ):
            ChatMessage(role=Role.USER, content="Test", confidence_score=-0.1)

    def test_message_validation_negative_counts(self):
        """Test validation fails for negative token counts and processing times."""
        message = ChatMessage(role=Role.USER, content="Test", token_count=-1)
        with pytest.raises(ValueError, match="token_count cannot be negative"):
            message.validate()

        message = ChatMessage(role=Role.USER, content="Test", processing_time_ms=-1)
        with pytest.raises(ValueError, match="processing_time_ms cannot be negative"):
            message.validate()

    def test_message_validation_empty_content_and_no_tools(self):
        """Test validation fails when both content and tool_calls are empty."""
        message = ChatMessage(role=Role.USER, content="", tool_calls=None)
        with pytest.raises(
            ValueError, match="Message must have either content or tool_calls"
        ):
            message.validate()

    def test_message_metadata_methods(self):
        """Test metadata getter and setter methods."""
        message = ChatMessage(role=Role.USER, content="Test")

        # Test setting metadata
        message.set_metadata_value("key1", "value1")
        message.set_metadata_value("key2", 42)

        # Test getting metadata
        assert message.get_metadata_value("key1") == "value1"
        assert message.get_metadata_value("key2") == 42
        assert message.get_metadata_value("nonexistent", "default") == "default"

    def test_message_to_dict_enhanced_serialization(self):
        """Test enhanced serialization includes new fields."""
        timestamp = datetime.now()
        message = ChatMessage(
            role=Role.ASSISTANT,
            content="Test response",
            timestamp=timestamp,
            confidence_score=0.8,
            token_count=5,
            processing_time_ms=200,
            metadata={"source": "test"},
        )

        result = message.to_dict()

        assert result["role"] == "assistant"
        assert result["content"] == "Test response"
        assert result["confidence_score"] == pytest.approx(0.8)
        assert result["token_count"] == 5
        assert result["processing_time_ms"] == 200
        assert result["metadata"] == {"source": "test"}
        assert result["uuid"] is not None
        assert result["timestamp"] == timestamp.isoformat()


class TestEnhancedConversation:
    """Test enhanced Conversation functionality."""

    def test_conversation_creation_with_new_fields(self):
        """Test creating a Conversation with enhanced Phase 1 fields."""
        conversation = Conversation(
            title="Test Conversation",
            model_name="gpt-4",
            system_prompt="You are a helpful assistant.",
            temperature=0.8,
            max_tokens=1000,
            metadata={"source": "test"},
        )

        assert conversation.title == "Test Conversation"
        assert conversation.model_name == "gpt-4"
        assert conversation.model == "gpt-4"  # Backward compatibility
        assert conversation.system_prompt == "You are a helpful assistant."
        assert conversation.temperature == pytest.approx(0.8)
        assert conversation.max_tokens == 1000
        assert conversation.metadata == {"source": "test"}
        assert conversation.uuid is not None

    def test_conversation_uuid_auto_generation(self):
        """Test that UUID is automatically generated."""
        conv1 = Conversation()
        conv2 = Conversation()

        assert conv1.uuid is not None
        assert conv2.uuid is not None
        assert conv1.uuid != conv2.uuid

    def test_conversation_model_field_sync(self):
        """Test that model and model_name fields are kept in sync."""
        # Test model_name -> model sync
        conv1 = Conversation(model_name="test-model")
        assert conv1.model == "test-model"

        # Test model -> model_name sync
        conv2 = Conversation(model="another-model")
        assert conv2.model_name == "another-model"

    def test_conversation_validation_temperature_bounds(self):
        """Test validation fails for invalid temperature values."""
        with pytest.raises(ValueError, match="temperature must be between 0.0 and 2.0"):
            Conversation(temperature=-0.1)

        with pytest.raises(ValueError, match="temperature must be between 0.0 and 2.0"):
            Conversation(temperature=2.1)

    def test_conversation_validation_max_tokens(self):
        """Test validation fails for invalid max_tokens."""
        conversation = Conversation(max_tokens=0)
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            conversation.validate()

        conversation = Conversation(max_tokens=-100)
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            conversation.validate()

    def test_conversation_add_message_with_validation(self):
        """Test that add_message validates messages before adding."""
        conversation = Conversation()

        # Valid message should be added
        valid_message = ChatMessage(role=Role.USER, content="Valid message")
        conversation.add_message(valid_message)
        assert conversation.get_message_count() == 1

        # Invalid message should raise an error
        invalid_message = ChatMessage(role=Role.USER, content="", tool_calls=None)
        with pytest.raises(ValueError):
            conversation.add_message(invalid_message)

    def test_conversation_utility_methods(self):
        """Test new utility methods."""
        conversation = Conversation()

        # Add messages with different roles and token counts
        conversation.add_message(
            ChatMessage(role=Role.USER, content="User 1", token_count=5)
        )
        conversation.add_message(
            ChatMessage(role=Role.ASSISTANT, content="Assistant 1", token_count=10)
        )
        conversation.add_message(
            ChatMessage(role=Role.USER, content="User 2", token_count=7)
        )
        conversation.add_message(
            ChatMessage(role=Role.TOOL, content="Tool result", token_count=3)
        )

        # Test get_messages_by_role
        user_messages = conversation.get_messages_by_role(Role.USER)
        assert len(user_messages) == 2
        assert all(msg.role == Role.USER for msg in user_messages)

        assistant_messages = conversation.get_messages_by_role(Role.ASSISTANT)
        assert len(assistant_messages) == 1

        # Test get_total_tokens
        total_tokens = conversation.get_total_tokens()
        assert total_tokens == 25  # 5 + 10 + 7 + 3

        # Test with messages that don't have token_count
        conversation.add_message(ChatMessage(role=Role.USER, content="No tokens"))
        assert conversation.get_total_tokens() == 25  # Should still be 25

    def test_conversation_config_methods(self):
        """Test conversation configuration methods."""
        conversation = Conversation(
            model_name="gpt-4",
            system_prompt="Test prompt",
            temperature=0.7,
            max_tokens=500,
        )

        # Test get_conversation_config
        config = conversation.get_conversation_config()
        expected_config = {
            "model_name": "gpt-4",
            "system_prompt": "Test prompt",
            "temperature": 0.7,
            "max_tokens": 500,
        }
        assert config == expected_config

        # Test update_config
        conversation.update_config(temperature=0.9, max_tokens=1000)
        assert conversation.temperature == pytest.approx(0.9)
        assert conversation.max_tokens == 1000

    def test_conversation_metadata_methods(self):
        """Test conversation metadata methods."""
        conversation = Conversation()

        # Test setting and getting metadata
        conversation.set_metadata_value("test_key", "test_value")
        conversation.set_metadata_value("number_key", 42)

        assert conversation.get_metadata_value("test_key") == "test_value"
        assert conversation.get_metadata_value("number_key") == 42
        assert conversation.get_metadata_value("nonexistent", "default") == "default"

    def test_conversation_to_dict_enhanced_serialization(self):
        """Test enhanced serialization includes new fields."""
        created_at = datetime.now()
        updated_at = datetime.now()

        conversation = Conversation(
            title="Test",
            model_name="gpt-4",
            system_prompt="Test prompt",
            temperature=0.8,
            max_tokens=1000,
            metadata={"source": "test"},
        )
        conversation.created_at = created_at
        conversation.updated_at = updated_at

        result = conversation.to_dict()

        assert result["title"] == "Test"
        assert result["model_name"] == "gpt-4"
        assert result["system_prompt"] == "Test prompt"
        assert result["temperature"] == pytest.approx(0.8)
        assert result["max_tokens"] == 1000
        assert result["metadata"] == {"source": "test"}
        assert result["uuid"] is not None
        assert result["created_at"] == created_at.isoformat()
        assert result["updated_at"] == updated_at.isoformat()


class TestEnhancedConversationManager:
    """Test ConversationManager with enhanced models."""

    def test_create_new_with_enhanced_fields(self, test_db_manager):
        """Test creating a conversation with enhanced configuration."""
        conv_manager = ConversationManager.create_new(
            model="gpt-4",
            title="Enhanced Test",
            system_prompt="You are a test assistant",
            temperature=0.9,
            max_tokens=500,
            metadata={"test": True},
        )

        conversation = conv_manager.get_current_conversation()
        assert conversation.model_name == "gpt-4"
        assert conversation.system_prompt == "You are a test assistant"
        assert conversation.temperature == pytest.approx(0.9)
        assert conversation.max_tokens == 500
        assert conversation.get_metadata_value("test") is True

    def test_add_messages_with_enhanced_fields(self, test_db_manager):
        """Test adding messages with enhanced fields."""
        conv_manager = ConversationManager.create_new(model="test-model")

        # Add user message with enhanced fields
        user_msg = conv_manager.add_user_message(
            content="Test user message",
            token_count=8,
            confidence_score=0.98,
            metadata={"source": "test"},
        )

        assert user_msg.token_count == 8
        assert user_msg.confidence_score == pytest.approx(0.98)
        assert user_msg.get_metadata_value("source") == "test"

        # Add assistant message with enhanced fields
        assistant_msg = conv_manager.add_assistant_message(
            content="Test response",
            thinking="Test thinking",
            token_count=12,
            processing_time_ms=200,
            confidence_score=0.92,
        )

        assert assistant_msg.token_count == 12
        assert assistant_msg.processing_time_ms == 200
        assert assistant_msg.confidence_score == pytest.approx(0.92)

    def test_load_existing_with_enhanced_fields(self, test_db_manager):
        """Test loading a conversation preserves enhanced fields."""
        # Create conversation with enhanced fields
        conv_manager = ConversationManager.create_new(
            model="test-model",
            title="Test Conversation",
            system_prompt="Test prompt",
            temperature=0.8,
            max_tokens=1000,
        )

        # Add messages with enhanced fields
        conv_manager.add_user_message(
            content="Test message", token_count=5, confidence_score=0.95
        )

        conv_id = conv_manager.get_current_conversation().id

        # Load the conversation
        loaded_manager = ConversationManager.load_existing(conv_id)
        loaded_conversation = loaded_manager.get_current_conversation()

        # Verify enhanced conversation fields are preserved
        assert loaded_conversation.system_prompt == "Test prompt"
        assert loaded_conversation.temperature == pytest.approx(0.8)
        assert loaded_conversation.max_tokens == 1000
        assert loaded_conversation.model_name == "test-model"

        # Verify enhanced message fields are preserved
        messages = loaded_conversation.messages
        assert len(messages) == 1
        user_msg = messages[0]
        assert user_msg.token_count == 5
        assert user_msg.confidence_score == pytest.approx(0.95)
        assert user_msg.uuid is not None

    def test_database_schema_compatibility(self, test_db_manager):
        """Test that enhanced models work with the updated database schema."""
        # This test verifies that the database migration worked correctly
        with DatabaseManager(db_file=":memory:") as db:
            db.connect()
            db.create_init_tables()

            # Create a conversation with all enhanced fields
            conv_id = db.create_conversation(
                title="Schema Test",
                model_name="test-model",
                system_prompt="Test prompt",
                temperature=0.9,
                max_tokens=500,
                metadata='{"test": true}',
                uuid="test-uuid-123",
            )

            # Insert a message with all enhanced fields
            message_id = db.insert_message(
                conversation_id=conv_id,
                step=1,
                role="user",
                content="Test message",
                confidence_score=0.95,
                token_count=10,
                processing_time_ms=150,
                metadata='{"source": "test"}',
                parent_message_id=None,
                uuid="msg-uuid-123",
            )

            assert conv_id is not None
            assert message_id is not None

            # Verify the data can be retrieved
            conv_data = db.get_conversation(conv_id)
            assert conv_data["model_name"] == "test-model"
            assert conv_data["system_prompt"] == "Test prompt"
            assert conv_data["temperature"] == pytest.approx(0.9)

            msg_data = db.get_messages(conv_id)[0]
            assert msg_data["confidence_score"] == pytest.approx(0.95)
            assert msg_data["token_count"] == 10
            assert msg_data["processing_time_ms"] == 150
            assert msg_data["uuid"] == "msg-uuid-123"

"""
Unit tests for Conversation Manager Service
"""
import pytest
from unittest.mock import Mock, patch
from app.services.conversation_manager import ConversationManager


class TestConversationManagerMemory:
    """Test suite for ConversationManager with in-memory fallback"""

    @pytest.fixture
    def manager(self):
        """Create a conversation manager with memory fallback (no Redis)"""
        with patch('redis.from_url') as mock_redis:
            # Simulate Redis connection failure
            mock_redis.side_effect = Exception("Redis not available")
            manager = ConversationManager(
                redis_url="redis://localhost:6379/0",
                history_length=10,
                session_ttl_hours=24
            )
            return manager

    def test_initialization_memory_fallback(self, manager):
        """Test manager initializes with memory fallback when Redis unavailable"""
        assert manager.use_redis is False
        assert hasattr(manager, '_memory_store')
        assert isinstance(manager._memory_store, dict)

    def test_add_user_message(self, manager):
        """Test adding a user message"""
        success = manager.add_message(
            session_id="test-session-1",
            role="user",
            content="Hello, what are your skills?"
        )
        assert success is True

        history = manager.get_history("test-session-1")
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello, what are your skills?"

    def test_add_assistant_message(self, manager):
        """Test adding an assistant message"""
        success = manager.add_message(
            session_id="test-session-2",
            role="assistant",
            content="I have expertise in Python, SQL, and PySpark."
        )
        assert success is True

        history = manager.get_history("test-session-2")
        assert len(history) == 1
        assert history[0]["role"] == "assistant"

    def test_add_message_with_metadata(self, manager):
        """Test adding a message with metadata"""
        metadata = {
            "intent": ["skills", "general"],
            "tokens": 150
        }
        success = manager.add_message(
            session_id="test-session-3",
            role="user",
            content="What skills do you have?",
            metadata=metadata
        )
        assert success is True

        history = manager.get_history("test-session-3")
        assert history[0]["metadata"]["intent"] == ["skills", "general"]
        assert history[0]["metadata"]["tokens"] == 150

    def test_add_invalid_role(self, manager):
        """Test adding a message with invalid role"""
        success = manager.add_message(
            session_id="test-session-4",
            role="invalid",
            content="Test message"
        )
        assert success is False

    def test_conversation_flow(self, manager):
        """Test a complete conversation flow"""
        session_id = "test-session-5"

        # User message
        manager.add_message(session_id, "user", "Hi, tell me about your projects")
        # Assistant message
        manager.add_message(session_id, "assistant", "I have built several projects...")
        # Follow-up user message
        manager.add_message(session_id, "user", "Tell me more about the LinkedIn project")
        # Follow-up assistant message
        manager.add_message(session_id, "assistant", "The LinkedIn Post Generator...")

        history = manager.get_history(session_id)
        assert len(history) == 4
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert history[2]["role"] == "user"
        assert history[3]["role"] == "assistant"

    def test_history_length_limit(self, manager):
        """Test that history is trimmed to configured length"""
        session_id = "test-session-6"

        # Add 15 messages (more than limit of 10)
        for i in range(15):
            role = "user" if i % 2 == 0 else "assistant"
            manager.add_message(session_id, role, f"Message {i}")

        history = manager.get_history(session_id)
        # Should only keep last 10 messages
        assert len(history) == 10
        # Should have messages 5-14
        assert history[0]["content"] == "Message 5"
        assert history[-1]["content"] == "Message 14"

    def test_get_history_with_limit(self, manager):
        """Test getting history with custom limit"""
        session_id = "test-session-7"

        # Add 5 messages
        for i in range(5):
            manager.add_message(session_id, "user", f"Message {i}")

        # Get only last 3
        history = manager.get_history(session_id, limit=3)
        assert len(history) == 3
        assert history[0]["content"] == "Message 2"
        assert history[-1]["content"] == "Message 4"

    def test_format_history_for_llm(self, manager):
        """Test formatting history for LLM API"""
        session_id = "test-session-8"

        manager.add_message(session_id, "user", "Hello")
        manager.add_message(session_id, "assistant", "Hi there!")
        manager.add_message(session_id, "user", "What are your skills?")

        llm_history = manager.format_history_for_llm(session_id)

        assert len(llm_history) == 3
        # Should only have role and content
        assert llm_history[0] == {"role": "user", "content": "Hello"}
        assert llm_history[1] == {"role": "assistant", "content": "Hi there!"}
        assert "timestamp" not in llm_history[0]
        assert "metadata" not in llm_history[0]

    def test_get_context_summary(self, manager):
        """Test getting context summary"""
        session_id = "test-session-9"

        manager.add_message(
            session_id, "user", "Hello",
            metadata={"intent": ["greeting"]}
        )
        manager.add_message(session_id, "assistant", "Hi!")
        manager.add_message(
            session_id, "user", "What skills do you have?",
            metadata={"intent": ["skills", "general"]}
        )

        summary = manager.get_context_summary(session_id)

        assert summary["session_id"] == session_id
        assert summary["total_messages"] == 3
        assert summary["user_messages"] == 2
        assert summary["assistant_messages"] == 1
        assert "greeting" in summary["unique_intents"]
        assert "skills" in summary["unique_intents"]
        assert summary["last_updated"] is not None

    def test_clear_history(self, manager):
        """Test clearing conversation history"""
        session_id = "test-session-10"

        # Add messages
        manager.add_message(session_id, "user", "Hello")
        manager.add_message(session_id, "assistant", "Hi!")

        assert len(manager.get_history(session_id)) == 2

        # Clear history
        success = manager.clear_history(session_id)
        assert success is True
        assert len(manager.get_history(session_id)) == 0

    def test_session_exists(self, manager):
        """Test checking if session exists"""
        session_id = "test-session-11"

        # Session doesn't exist yet
        assert manager.session_exists(session_id) is False

        # Add a message
        manager.add_message(session_id, "user", "Hello")

        # Session exists now
        assert manager.session_exists(session_id) is True

    def test_get_session_stats(self, manager):
        """Test getting session statistics"""
        # Add messages to multiple sessions
        manager.add_message("session-1", "user", "Hello")
        manager.add_message("session-2", "user", "Hi")

        stats = manager.get_session_stats()

        assert stats["storage"] == "memory"
        assert stats["active_sessions"] == 2
        assert stats["redis_connected"] is False

    def test_empty_session(self, manager):
        """Test getting history for non-existent session"""
        history = manager.get_history("non-existent-session")
        assert history == []

    def test_multiple_sessions(self, manager):
        """Test managing multiple sessions independently"""
        # Session 1
        manager.add_message("session-a", "user", "Message A1")
        manager.add_message("session-a", "assistant", "Response A1")

        # Session 2
        manager.add_message("session-b", "user", "Message B1")
        manager.add_message("session-b", "assistant", "Response B1")

        # Verify independence
        history_a = manager.get_history("session-a")
        history_b = manager.get_history("session-b")

        assert len(history_a) == 2
        assert len(history_b) == 2
        assert history_a[0]["content"] == "Message A1"
        assert history_b[0]["content"] == "Message B1"


class TestConversationManagerRedis:
    """Test suite for ConversationManager with Redis (mocked)"""

    @pytest.fixture
    def manager(self):
        """Create a conversation manager with mocked Redis"""
        with patch('redis.from_url') as mock_redis_from_url:
            # Create a mock Redis client
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_client.rpush.return_value = 1
            mock_client.ltrim.return_value = True
            mock_client.expire.return_value = True
            mock_client.lrange.return_value = []
            mock_client.delete.return_value = 1
            mock_client.exists.return_value = 0
            mock_client.keys.return_value = []

            mock_redis_from_url.return_value = mock_client

            manager = ConversationManager(
                redis_url="redis://localhost:6379/0",
                history_length=10,
                session_ttl_hours=24
            )
            manager.redis_client = mock_client
            return manager

    def test_initialization_with_redis(self, manager):
        """Test manager initializes with Redis successfully"""
        assert manager.use_redis is True
        assert manager.redis_client is not None
        manager.redis_client.ping.assert_called_once()

    def test_add_message_redis(self, manager):
        """Test adding message to Redis"""
        success = manager.add_message(
            "test-session",
            "user",
            "Hello"
        )

        assert success is True
        # Verify Redis methods were called
        assert manager.redis_client.rpush.called
        assert manager.redis_client.ltrim.called
        assert manager.redis_client.expire.called

    def test_get_session_stats_redis(self, manager):
        """Test getting session stats with Redis"""
        manager.redis_client.keys.return_value = ["chat:session:1:history", "chat:session:2:history"]

        stats = manager.get_session_stats()

        assert stats["storage"] == "redis"
        assert stats["active_sessions"] == 2
        assert stats["redis_connected"] is True

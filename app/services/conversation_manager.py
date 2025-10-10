"""
Conversation History Manager

Manages conversation history for chatbot sessions using Redis for caching.
Provides context-aware conversations by maintaining message history.
"""
from typing import List, Dict, Optional
import json
import redis
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConversationManager:
    """
    Manages conversation history for chatbot sessions.

    Features:
    - Stores conversation history in Redis with TTL
    - Maintains configurable history length (last N messages)
    - Formats conversation for LLM context
    - Supports session management and cleanup
    - Graceful fallback when Redis is unavailable
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        history_length: int = 10,
        session_ttl_hours: int = 24
    ):
        """
        Initialize conversation manager.

        Args:
            redis_url: Redis connection URL (defaults to settings.redis_url)
            history_length: Number of recent messages to keep (default: 10)
            session_ttl_hours: Session expiration time in hours (default: 24)
        """
        self.redis_url = redis_url or settings.redis_url
        self.history_length = history_length
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = True

        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=10,  # Increased for Railway's internal DNS
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Conversation manager initialized with Redis: {self.redis_url}")
        except Exception as e:
            self.use_redis = False
            logger.warning(f"Redis not available, using in-memory fallback: {e}")
            # Fallback to in-memory storage
            self._memory_store: Dict[str, List[Dict]] = {}

    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for a session."""
        return f"chat:session:{session_id}:history"

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add a message to conversation history.

        Args:
            session_id: Unique session identifier
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Optional metadata (intent, tokens, etc.)

        Returns:
            True if successful, False otherwise
        """
        if role not in ["user", "assistant"]:
            logger.error(f"Invalid role: {role}. Must be 'user' or 'assistant'")
            return False

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }

        try:
            if self.use_redis and self.redis_client:
                return self._add_message_redis(session_id, message)
            else:
                return self._add_message_memory(session_id, message)
        except Exception as e:
            logger.error(f"Failed to add message to session {session_id}: {e}")
            return False

    def _add_message_redis(self, session_id: str, message: Dict) -> bool:
        """Add message to Redis."""
        key = self._get_session_key(session_id)

        # Add message to list
        self.redis_client.rpush(key, json.dumps(message))

        # Trim to keep only recent messages
        self.redis_client.ltrim(key, -self.history_length, -1)

        # Set expiration
        self.redis_client.expire(key, int(self.session_ttl.total_seconds()))

        logger.info(f"Added {message['role']} message to session {session_id} (Redis)")
        return True

    def _add_message_memory(self, session_id: str, message: Dict) -> bool:
        """Add message to in-memory store."""
        if session_id not in self._memory_store:
            self._memory_store[session_id] = []

        self._memory_store[session_id].append(message)

        # Keep only recent messages
        self._memory_store[session_id] = self._memory_store[session_id][-self.history_length:]

        logger.info(f"Added {message['role']} message to session {session_id} (Memory)")
        return True

    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: Unique session identifier
            limit: Optional limit on number of messages (defaults to history_length)

        Returns:
            List of messages in chronological order
        """
        try:
            if self.use_redis and self.redis_client:
                return self._get_history_redis(session_id, limit)
            else:
                return self._get_history_memory(session_id, limit)
        except Exception as e:
            logger.error(f"Failed to get history for session {session_id}: {e}")
            return []

    def _get_history_redis(self, session_id: str, limit: Optional[int]) -> List[Dict]:
        """Get history from Redis."""
        key = self._get_session_key(session_id)

        # Get messages
        messages_json = self.redis_client.lrange(key, 0, -1)

        if not messages_json:
            return []

        messages = [json.loads(msg) for msg in messages_json]

        # Apply limit if specified
        if limit:
            messages = messages[-limit:]

        logger.info(f"Retrieved {len(messages)} messages from session {session_id} (Redis)")
        return messages

    def _get_history_memory(self, session_id: str, limit: Optional[int]) -> List[Dict]:
        """Get history from in-memory store."""
        messages = self._memory_store.get(session_id, [])

        if limit:
            messages = messages[-limit:]

        logger.info(f"Retrieved {len(messages)} messages from session {session_id} (Memory)")
        return messages

    def format_history_for_llm(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Format conversation history for LLM API.

        Returns messages in the format expected by Anthropic API:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Args:
            session_id: Unique session identifier
            limit: Optional limit on number of messages

        Returns:
            List of messages formatted for LLM
        """
        history = self.get_history(session_id, limit)

        # Convert to LLM format (only role and content)
        llm_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]

        logger.info(f"Formatted {len(llm_messages)} messages for LLM (session {session_id})")
        return llm_messages

    def get_context_summary(self, session_id: str) -> Dict:
        """
        Get a summary of the conversation context.

        Args:
            session_id: Unique session identifier

        Returns:
            Dictionary with context summary
        """
        history = self.get_history(session_id)

        user_messages = [msg for msg in history if msg["role"] == "user"]
        assistant_messages = [msg for msg in history if msg["role"] == "assistant"]

        # Extract intents from metadata
        intents = []
        for msg in history:
            if "metadata" in msg and "intent" in msg["metadata"]:
                intent = msg["metadata"]["intent"]
                if isinstance(intent, list):
                    intents.extend(intent)
                else:
                    intents.append(intent)

        return {
            "session_id": session_id,
            "total_messages": len(history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "unique_intents": list(set(intents)),
            "last_updated": history[-1]["timestamp"] if history else None
        }

    def clear_history(self, session_id: str) -> bool:
        """
        Clear conversation history for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            True if successful
        """
        try:
            if self.use_redis and self.redis_client:
                key = self._get_session_key(session_id)
                self.redis_client.delete(key)
                logger.info(f"Cleared history for session {session_id} (Redis)")
            else:
                if session_id in self._memory_store:
                    del self._memory_store[session_id]
                logger.info(f"Cleared history for session {session_id} (Memory)")
            return True
        except Exception as e:
            logger.error(f"Failed to clear history for session {session_id}: {e}")
            return False

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session has conversation history.

        Args:
            session_id: Unique session identifier

        Returns:
            True if session exists with messages
        """
        try:
            if self.use_redis and self.redis_client:
                key = self._get_session_key(session_id)
                return self.redis_client.exists(key) > 0
            else:
                return session_id in self._memory_store and len(self._memory_store[session_id]) > 0
        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {e}")
            return False

    def get_session_stats(self) -> Dict:
        """
        Get statistics about conversation storage.

        Returns:
            Dictionary with storage stats
        """
        try:
            if self.use_redis and self.redis_client:
                # Count sessions in Redis
                keys = self.redis_client.keys("chat:session:*:history")
                return {
                    "storage": "redis",
                    "active_sessions": len(keys),
                    "redis_connected": True
                }
            else:
                return {
                    "storage": "memory",
                    "active_sessions": len(self._memory_store),
                    "redis_connected": False
                }
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {
                "storage": "unknown",
                "active_sessions": 0,
                "redis_connected": False,
                "error": str(e)
            }


# Global conversation manager instance
conversation_manager = ConversationManager(
    history_length=settings.conversation_history_length,
    session_ttl_hours=settings.session_ttl_hours
)

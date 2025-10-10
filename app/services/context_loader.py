"""
Context Loader Service

Loads portfolio context files based on detected intents.
Manages context file reading, caching, and formatting for LLM prompts.
"""
from typing import List, Dict, Optional
from pathlib import Path
import time
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ContextLoader:
    """
    Loads and manages portfolio context files for LLM prompts.

    Features:
    - Loads .txt files from context/ directory
    - Caches frequently accessed context (15-minute TTL)
    - Maps intents to relevant context files
    - Formats context for LLM consumption
    """

    def __init__(self, context_dir: str = "context"):
        """
        Initialize context loader.

        Args:
            context_dir: Directory containing context files (default: "context")
        """
        self.context_dir = Path(context_dir)
        self.cache: Dict[str, Dict[str, any]] = {}
        self.cache_ttl = 900  # 15 minutes in seconds

        # Verify context directory exists
        if not self.context_dir.exists():
            raise FileNotFoundError(f"Context directory not found: {self.context_dir}")

        logger.info(f"Context loader initialized with directory: {self.context_dir}")

    def _get_cache_key(self, filename: str) -> str:
        """Generate cache key for a context file."""
        return f"context_{filename}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cached context is still valid.

        Args:
            cache_key: Cache key to check

        Returns:
            True if cache exists and is not expired
        """
        if cache_key not in self.cache:
            return False

        cached_time = self.cache[cache_key].get("timestamp", 0)
        current_time = time.time()

        return (current_time - cached_time) < self.cache_ttl

    def _read_context_file(self, filename: str) -> Optional[str]:
        """
        Read a context file from disk.

        Args:
            filename: Name of the context file (without .txt extension)

        Returns:
            Content of the file or None if not found
        """
        file_path = self.context_dir / f"{filename}.txt"

        if not file_path.exists():
            logger.warning(f"Context file not found: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            logger.info(f"Successfully read context file: {filename}.txt ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Error reading context file {filename}.txt: {e}")
            return None

    def load_context(self, filename: str, use_cache: bool = True) -> Optional[str]:
        """
        Load a single context file with optional caching.

        Args:
            filename: Name of the context file (without .txt extension)
            use_cache: Whether to use cache (default: True)

        Returns:
            Content of the file or None if not found
        """
        cache_key = self._get_cache_key(filename)

        # Check cache first
        if use_cache and self._is_cache_valid(cache_key):
            logger.info(f"Using cached context for: {filename}.txt")
            return self.cache[cache_key]["content"]

        # Read from disk
        content = self._read_context_file(filename)

        # Cache the result
        if content and use_cache:
            self.cache[cache_key] = {
                "content": content,
                "timestamp": time.time()
            }
            logger.info(f"Cached context for: {filename}.txt")

        return content

    def load_multiple_contexts(
        self,
        filenames: List[str],
        use_cache: bool = True
    ) -> Dict[str, str]:
        """
        Load multiple context files at once.

        Args:
            filenames: List of context file names (without .txt extension)
            use_cache: Whether to use cache (default: True)

        Returns:
            Dictionary mapping filename to content
        """
        contexts = {}

        for filename in filenames:
            content = self.load_context(filename, use_cache=use_cache)
            if content:
                contexts[filename] = content

        logger.info(f"Loaded {len(contexts)} context files: {list(contexts.keys())}")
        return contexts

    def format_context_for_llm(
        self,
        contexts: Dict[str, str],
        include_headers: bool = True
    ) -> str:
        """
        Format loaded contexts into a single string for LLM consumption.

        Args:
            contexts: Dictionary mapping filename to content
            include_headers: Whether to include section headers (default: True)

        Returns:
            Formatted context string
        """
        if not contexts:
            return ""

        formatted_sections = []

        for filename, content in contexts.items():
            if include_headers:
                # Create a clear section header
                header = f"=== {filename.upper().replace('_', ' ')} ==="
                formatted_sections.append(f"{header}\n{content}")
            else:
                formatted_sections.append(content)

        # Join with double newlines for clear separation
        formatted_context = "\n\n".join(formatted_sections)

        logger.info(f"Formatted context: {len(formatted_context)} chars from {len(contexts)} files")
        return formatted_context

    def get_context_for_intents(
        self,
        intents: List[str],
        use_cache: bool = True,
        include_headers: bool = True
    ) -> str:
        """
        Get formatted context based on detected intents.

        This is the main method to use in the chatbot flow.

        Args:
            intents: List of detected intents from intent_classifier
            use_cache: Whether to use cache (default: True)
            include_headers: Whether to include section headers (default: True)

        Returns:
            Formatted context string ready for LLM prompt
        """
        from app.services.intent_classifier import intent_classifier

        # Map intents to context files
        context_files = intent_classifier.map_intent_to_context_files(intents)

        # Load all relevant contexts
        contexts = self.load_multiple_contexts(context_files, use_cache=use_cache)

        # Format for LLM
        formatted_context = self.format_context_for_llm(contexts, include_headers=include_headers)

        logger.info(f"Generated context for intents {intents}: {len(formatted_context)} chars")
        return formatted_context

    def clear_cache(self, filename: Optional[str] = None):
        """
        Clear cached context.

        Args:
            filename: Specific file to clear, or None to clear all cache
        """
        if filename:
            cache_key = self._get_cache_key(filename)
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.info(f"Cleared cache for: {filename}.txt")
        else:
            self.cache.clear()
            logger.info("Cleared all context cache")

    def get_cache_stats(self) -> Dict[str, any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        current_time = time.time()
        valid_entries = sum(
            1 for entry in self.cache.values()
            if (current_time - entry["timestamp"]) < self.cache_ttl
        )

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_ttl_seconds": self.cache_ttl
        }


# Global context loader instance
context_loader = ContextLoader()

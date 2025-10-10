"""
Unit tests for Context Loader Service
"""
import pytest
from pathlib import Path
from app.services.context_loader import ContextLoader


class TestContextLoader:
    """Test suite for ContextLoader"""

    @pytest.fixture
    def loader(self):
        """Create a context loader instance"""
        return ContextLoader(context_dir="context")

    def test_initialization(self, loader):
        """Test context loader initializes correctly"""
        assert loader.context_dir == Path("context")
        assert loader.cache_ttl == 900
        assert isinstance(loader.cache, dict)
        assert len(loader.cache) == 0

    def test_load_general_context(self, loader):
        """Test loading general.txt"""
        content = loader.load_context("general", use_cache=False)
        assert content is not None
        assert "Anirudh Nuti" in content
        assert "Email:" in content or "nvkanirudh124@gmail.com" in content

    def test_load_skills_context(self, loader):
        """Test loading skills.txt"""
        content = loader.load_context("skills", use_cache=False)
        assert content is not None
        assert "Python" in content or "python" in content.lower()

    def test_load_experience_context(self, loader):
        """Test loading experience.txt"""
        content = loader.load_context("experience", use_cache=False)
        assert content is not None
        assert "Nidhi AI" in content or "experience" in content.lower()

    def test_load_projects_context(self, loader):
        """Test loading projects.txt"""
        content = loader.load_context("projects", use_cache=False)
        assert content is not None
        assert "project" in content.lower()

    def test_load_education_context(self, loader):
        """Test loading education.txt"""
        content = loader.load_context("education", use_cache=False)
        assert content is not None
        assert "Boston University" in content or "education" in content.lower()

    def test_load_contact_context(self, loader):
        """Test loading contact.txt"""
        content = loader.load_context("contact", use_cache=False)
        assert content is not None
        assert "nvkanirudh124@gmail.com" in content or "contact" in content.lower()

    def test_load_nonexistent_context(self, loader):
        """Test loading a file that doesn't exist"""
        content = loader.load_context("nonexistent", use_cache=False)
        assert content is None

    def test_cache_functionality(self, loader):
        """Test that caching works"""
        # First load (from disk)
        content1 = loader.load_context("general", use_cache=True)
        cache_key = loader._get_cache_key("general")
        assert cache_key in loader.cache

        # Second load (from cache)
        content2 = loader.load_context("general", use_cache=True)
        assert content1 == content2
        assert loader._is_cache_valid(cache_key)

    def test_cache_disabled(self, loader):
        """Test loading without cache"""
        content = loader.load_context("general", use_cache=False)
        cache_key = loader._get_cache_key("general")
        assert cache_key not in loader.cache
        assert content is not None

    def test_load_multiple_contexts(self, loader):
        """Test loading multiple context files"""
        contexts = loader.load_multiple_contexts(
            ["general", "skills", "experience"],
            use_cache=False
        )
        assert len(contexts) == 3
        assert "general" in contexts
        assert "skills" in contexts
        assert "experience" in contexts

    def test_load_multiple_with_nonexistent(self, loader):
        """Test loading multiple contexts with some nonexistent files"""
        contexts = loader.load_multiple_contexts(
            ["general", "nonexistent", "skills"],
            use_cache=False
        )
        # Should only load existing files
        assert len(contexts) == 2
        assert "general" in contexts
        assert "skills" in contexts
        assert "nonexistent" not in contexts

    def test_format_context_for_llm_with_headers(self, loader):
        """Test formatting context with headers"""
        contexts = {
            "general": "General info about Anirudh",
            "skills": "Python, SQL, PySpark"
        }
        formatted = loader.format_context_for_llm(contexts, include_headers=True)

        assert "=== GENERAL ===" in formatted
        assert "=== SKILLS ===" in formatted
        assert "General info about Anirudh" in formatted
        assert "Python, SQL, PySpark" in formatted

    def test_format_context_for_llm_without_headers(self, loader):
        """Test formatting context without headers"""
        contexts = {
            "general": "General info",
            "skills": "Tech skills"
        }
        formatted = loader.format_context_for_llm(contexts, include_headers=False)

        assert "===" not in formatted
        assert "General info" in formatted
        assert "Tech skills" in formatted

    def test_format_empty_context(self, loader):
        """Test formatting with no contexts"""
        formatted = loader.format_context_for_llm({})
        assert formatted == ""

    def test_get_context_for_greeting_intent(self, loader):
        """Test getting context for greeting intent"""
        context = loader.get_context_for_intents(["greeting"], use_cache=False)
        assert context is not None
        assert len(context) > 0
        # Greeting should load general context
        assert "GENERAL" in context or "Anirudh" in context

    def test_get_context_for_skills_intent(self, loader):
        """Test getting context for skills intent"""
        context = loader.get_context_for_intents(["skills"], use_cache=False)
        assert context is not None
        assert "SKILLS" in context or "Python" in context

    def test_get_context_for_contact_intent(self, loader):
        """Test getting context for contact intent"""
        context = loader.get_context_for_intents(["contact"], use_cache=False)
        assert context is not None
        # Should include contact or general info
        assert len(context) > 0

    def test_get_context_for_multiple_intents(self, loader):
        """Test getting context for multiple intents"""
        context = loader.get_context_for_intents(
            ["skills", "experience"],
            use_cache=False
        )
        assert context is not None
        assert len(context) > 0
        # Should include both contexts
        assert "SKILLS" in context or "EXPERIENCE" in context

    def test_clear_specific_cache(self, loader):
        """Test clearing cache for specific file"""
        # Load and cache
        loader.load_context("general", use_cache=True)
        cache_key = loader._get_cache_key("general")
        assert cache_key in loader.cache

        # Clear specific cache
        loader.clear_cache("general")
        assert cache_key not in loader.cache

    def test_clear_all_cache(self, loader):
        """Test clearing all cache"""
        # Load and cache multiple files
        loader.load_context("general", use_cache=True)
        loader.load_context("skills", use_cache=True)
        assert len(loader.cache) > 0

        # Clear all
        loader.clear_cache()
        assert len(loader.cache) == 0

    def test_get_cache_stats(self, loader):
        """Test getting cache statistics"""
        # Load some contexts
        loader.load_context("general", use_cache=True)
        loader.load_context("skills", use_cache=True)

        stats = loader.get_cache_stats()
        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 2
        assert stats["expired_entries"] == 0
        assert stats["cache_ttl_seconds"] == 900

    def test_cache_key_generation(self, loader):
        """Test cache key generation"""
        key1 = loader._get_cache_key("general")
        key2 = loader._get_cache_key("skills")

        assert key1 == "context_general"
        assert key2 == "context_skills"
        assert key1 != key2

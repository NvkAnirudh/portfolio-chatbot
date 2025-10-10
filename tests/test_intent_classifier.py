"""
Unit tests for Intent Classification Service
"""
import pytest
from app.services.intent_classifier import IntentClassifier


@pytest.fixture
def classifier():
    """Create a classifier instance"""
    return IntentClassifier()


class TestIntentClassifier:
    """Test suite for IntentClassifier"""

    def test_greeting_intent(self, classifier):
        """Test greeting detection"""
        messages = [
            "Hello",
            "Hi there",
            "Hey!",
            "Good morning",
            "Greetings"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "greeting" in intents

    def test_skills_intent(self, classifier):
        """Test skills intent detection"""
        messages = [
            "What are your skills?",
            "Tell me about your technical expertise",
            "What programming languages do you know?",
            "What technologies do you work with?",
            "Do you know Python and SQL?"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "skills" in intents

    def test_experience_intent(self, classifier):
        """Test experience intent detection"""
        messages = [
            "What is your work experience?",
            "Tell me about your jobs",
            "Where have you worked?",
            "What companies did you work for?",
            "What are your professional achievements?"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "experience" in intents

    def test_projects_intent(self, classifier):
        """Test projects intent detection"""
        messages = [
            "Show me your projects",
            "What have you built?",
            "Tell me about your portfolio",
            "Do you have any GitHub repositories?",
            "What applications have you developed?"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "projects" in intents

    def test_education_intent(self, classifier):
        """Test education intent detection"""
        messages = [
            "What is your education?",
            "Tell me about your degree",
            "Where did you study?",
            "What university did you go to?",
            "What courses did you take?"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "education" in intents

    def test_contact_intent(self, classifier):
        """Test contact intent detection"""
        messages = [
            "How can I contact you?",
            "What's your email?",
            "Are you available for hire?",
            "I want to reach out to you",
            "Can we discuss an opportunity?"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "contact" in intents

    def test_general_intent(self, classifier):
        """Test general intent as fallback"""
        messages = [
            "Tell me about yourself",
            "Who are you?",
            "What do you do?",
            "Give me an overview"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "general" in intents

    def test_multiple_intents(self, classifier):
        """Test detection of multiple intents"""
        # Skills + Experience
        intents = classifier.classify("What skills do you have from your work experience?")
        assert "skills" in intents
        assert "experience" in intents

        # Projects + Skills
        intents = classifier.classify("What technologies did you use in your projects?")
        assert "projects" in intents or "skills" in intents

    def test_primary_intent(self, classifier):
        """Test getting primary intent"""
        msg = "What are your Python skills?"
        primary = classifier.get_primary_intent(msg)
        assert primary == "skills"

    def test_should_load_context(self, classifier):
        """Test context loading decision"""
        # Greetings don't need context
        assert classifier.should_load_context("greeting") is False

        # Other intents need context
        assert classifier.should_load_context("skills") is True
        assert classifier.should_load_context("experience") is True
        assert classifier.should_load_context("projects") is True

    def test_context_file_mapping(self, classifier):
        """Test mapping intents to context files"""
        # Skills intent
        files = classifier.map_intent_to_context_files(["skills"])
        assert "skills" in files
        assert "general" in files

        # Experience intent
        files = classifier.map_intent_to_context_files(["experience"])
        assert "experience" in files
        assert "general" in files

        # Projects intent
        files = classifier.map_intent_to_context_files(["projects"])
        assert "projects" in files
        assert "general" in files

        # Education intent
        files = classifier.map_intent_to_context_files(["education"])
        assert "education" in files
        assert "general" in files

        # Contact intent
        files = classifier.map_intent_to_context_files(["contact"])
        assert "general" in files

        # Greeting intent
        files = classifier.map_intent_to_context_files(["greeting"])
        assert "general" in files

    def test_empty_message(self, classifier):
        """Test handling of empty messages"""
        intents = classifier.classify("")
        assert intents == ["general"]

        intents = classifier.classify("   ")
        assert intents == ["general"]

    def test_case_insensitivity(self, classifier):
        """Test that classification is case-insensitive"""
        messages = [
            "WHAT ARE YOUR SKILLS?",
            "what are your skills?",
            "What Are Your Skills?"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "skills" in intents

    def test_specific_technology_mentions(self, classifier):
        """Test detection of specific technologies"""
        messages = [
            "Do you know PySpark?",
            "Have you worked with Kafka?",
            "Can you use Airflow?",
            "What about AWS experience?"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "skills" in intents

    def test_company_mentions(self, classifier):
        """Test detection of company names"""
        messages = [
            "Tell me about your work at Nidhi AI",
            "What did you do at Econtenti?",
            "Your experience at ATC?"
        ]
        for msg in messages:
            intents = classifier.classify(msg)
            assert "experience" in intents

    def test_combined_greeting_and_question(self, classifier):
        """Test messages that start with greeting but have questions"""
        msg = "Hi! What are your skills?"
        intents = classifier.classify(msg)
        assert "greeting" in intents
        assert "skills" in intents

"""
Intent Classification Service

Classifies user messages into intents to determine which context to load.
Uses LLM (Claude Haiku) for accurate classification (~$0.00001 per call).
Falls back to keyword matching if LLM is unavailable.
"""
from typing import List, Optional
import anthropic
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class IntentClassifier:
    """
    Classifies user queries into intents using keyword matching.

    Intent Categories:
    - normal: Casual conversation, small talk, "how are you", chitchat
    - greeting: Hello, hi, hey
    - skills: Technical skills, tech stack, languages, tools
    - experience: Work history, jobs, roles, companies
    - projects: Portfolio projects, demos, GitHub
    - education: Degrees, university, courses, academic background
    - contact: How to reach, email, hire, availability
    - general: General questions about Anirudh
    """

    def __init__(self):
        """Initialize intent patterns and LLM client"""
        # Initialize Anthropic client
        try:
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.use_llm = True
            logger.info("Intent classifier initialized with LLM support")
        except Exception as e:
            self.client = None
            self.use_llm = False
            logger.warning(f"LLM not available, using keyword fallback: {e}")

        # Keyword patterns for fallback
        self.intent_patterns = {
            "normal": [
                "how are you", "how are you doing", "how's it going", "hows it going",
                "how have you been", "what's up", "whats up", "sup", "wassup",
                "how do you feel", "are you okay", "doing well", "doing good",
                "nice to meet you", "pleasure to meet", "thank you", "thanks",
                "appreciate it", "cool", "awesome", "great", "nice", "interesting",
                "that's great", "thats great", "good to know", "i see", "okay",
                "alright", "sounds good", "makes sense", "got it", "understood"
            ],
            "greeting": [
                "hello", "hi", "hey", "greetings", "good morning", "good afternoon",
                "good evening", "howdy"
            ],
            "skills": [
                "skill", "skills", "technology", "technologies", "tech stack",
                "programming", "language", "languages", "framework", "frameworks",
                "tool", "tools", "python", "sql", "pyspark", "kafka", "airflow",
                "aws", "cloud", "database", "databases", "fastapi", "react",
                "know", "proficient", "expertise", "capabilities", "competencies",
                "data engineering", "machine learning", "ai", "ml", "llm"
            ],
            "experience": [
                "experience", "work", "job", "jobs", "role", "roles", "position",
                "positions", "company", "companies", "worked", "employer",
                "career", "professional", "working", "worked at", "currently",
                "responsibility", "responsibilities", "achievement", "achievements",
                "nidhi", "determined", "econtenti", "atc", "intain"
            ],
            "projects": [
                "project", "projects", "portfolio", "built", "build", "created",
                "developed", "github", "demo", "code", "application", "applications",
                "linkedin post generator", "e-commerce", "analytics", "mcp",
                "show me", "examples", "work samples", "repositories"
            ],
            "education": [
                "education", "degree", "degrees", "university", "college",
                "study", "studied", "academic", "school", "bachelor", "master",
                "masters", "bachelors", "boston university", "gitam", "course",
                "courses", "learning", "teaching assistant", "ta", "coursework"
            ],
            "contact": [
                "contact", "email", "reach", "reach out", "get in touch", "hire", "hiring",
                "recruit", "recruiting", "available", "availability", "phone",
                "connect", "connection", "message", "talk", "discuss", "opportunity",
                "opportunities", "work with", "collaborate", "collaboration", "touch base"
            ],
            "general": [
                "who", "what", "where", "about", "tell me", "information",
                "know more", "describe", "background", "overview", "summary"
            ]
        }

    def classify_with_llm(self, message: str) -> List[str]:
        """
        Classify message using LLM for accurate intent detection.

        Args:
            message: User's message

        Returns:
            List of detected intents
        """
        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=50,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"""Classify this user message into one or more of these intents:
- normal: Casual conversation, small talk (e.g., "how are you?", "what's up?", "nice!", "thanks", "cool")
- greeting: Initial greetings only (e.g., "hello", "hi", "hey")
- skills: Questions about technical skills, technologies, programming languages, expertise
- experience: Questions about work history, jobs, companies, professional experience
- projects: Questions about portfolio projects, what was built, GitHub, demos
- education: Questions about degrees, university, academic background, courses
- contact: Questions about how to reach out, email, hiring, availability, collaboration
- general: General questions about the person, or unclear queries

User message: "{message}"

Return ONLY the intent names as a comma-separated list (e.g., "skills,general" or "contact" or "normal").
IMPORTANT: If the message is casual conversation like "how are you?" or small talk, classify it as "normal".
If the message is asking how to contact/reach out/get in touch/email, classify it as "contact".
Return maximum 2 intents, ordered by relevance."""
                }]
            )

            # Parse response
            intents_str = response.content[0].text.strip().lower()
            intents = [intent.strip() for intent in intents_str.split(",")]

            # Validate intents
            valid_intents = ["normal", "greeting", "skills", "experience", "projects", "education", "contact", "general"]
            filtered_intents = [i for i in intents if i in valid_intents]

            if not filtered_intents:
                filtered_intents = ["general"]

            logger.info(f"LLM classified message into intents: {filtered_intents}")
            return filtered_intents[:3]  # Max 3

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self.classify_with_keywords(message)

    def classify_with_keywords(self, message: str) -> List[str]:
        """
        Fallback keyword-based classification.

        Args:
            message: User's message

        Returns:
            List of detected intents
        """
        if not message or not message.strip():
            return ["general"]

        message_lower = message.lower().strip()
        detected_intents = []
        intent_scores = {}

        # Check for greeting at the start
        if any(message_lower.startswith(pattern) for pattern in self.intent_patterns["greeting"]):
            detected_intents.append("greeting")

        # Score each intent based on keyword matches
        for intent, keywords in self.intent_patterns.items():
            if intent == "greeting" and "greeting" in detected_intents:
                continue  # Already detected

            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    # Longer keywords get higher scores
                    score += len(keyword.split())

            if score > 0:
                intent_scores[intent] = score

        # Sort intents by score (highest first)
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)

        # Add top intents to the list
        for intent, score in sorted_intents[:3]:  # Maximum 3 intents
            if intent not in detected_intents:
                detected_intents.append(intent)

        # Default to general if no specific intent found (and not a greeting)
        if not detected_intents:
            detected_intents.append("general")

        logger.info(f"Keyword-based classification: {detected_intents}")
        return detected_intents

    def classify(self, message: str) -> List[str]:
        """
        Classify a message into one or more intents.
        Uses LLM if available, falls back to keywords.

        Args:
            message: User's message

        Returns:
            List of detected intents, ordered by relevance
        """
        if not message or not message.strip():
            return ["general"]

        if self.use_llm and self.client:
            return self.classify_with_llm(message)
        else:
            return self.classify_with_keywords(message)

    def get_primary_intent(self, message: str) -> str:
        """
        Get the primary (most relevant) intent for a message.

        Args:
            message: User's message

        Returns:
            Primary intent string
        """
        intents = self.classify(message)
        return intents[0] if intents else "general"

    def should_load_context(self, intent: str) -> bool:
        """
        Determine if context files should be loaded for this intent.

        Normal conversations and greetings don't need full context.

        Args:
            intent: Detected intent

        Returns:
            True if context should be loaded
        """
        # Normal conversations and greetings don't need context files
        return intent not in ["normal", "greeting"]

    def map_intent_to_context_files(self, intents: List[str]) -> List[str]:
        """
        Map intents to the context files that should be loaded.

        Args:
            intents: List of detected intents

        Returns:
            List of context file names (without .txt extension)
        """
        context_files = set()

        for intent in intents:
            if intent == "normal":
                # No context needed for casual conversation
                pass
            elif intent == "greeting":
                # No context for greetings either
                pass
            elif intent == "skills":
                context_files.add("skills")
                context_files.add("general")
            elif intent == "experience":
                context_files.add("experience")
                context_files.add("general")
            elif intent == "projects":
                context_files.add("projects")
                context_files.add("general")
            elif intent == "education":
                context_files.add("education")
                context_files.add("general")
            elif intent == "contact":
                context_files.add("contact")
                context_files.add("general")
            elif intent == "general":
                # Load general for now, more specific context if needed
                context_files.add("general")

        logger.info(f"Mapped intents {intents} to context files: {list(context_files)}")
        return list(context_files)


# Global classifier instance
intent_classifier = IntentClassifier()

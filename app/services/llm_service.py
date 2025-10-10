"""
LLM Service

Integrates with Anthropic Claude API for generating chatbot responses.
Includes prompt caching, cost tracking, and error handling.
"""
from typing import List, Dict, Optional, Tuple
import anthropic
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMService:
    """
    Service for interacting with Anthropic Claude API.

    Features:
    - Claude 3.5 Haiku integration
    - Prompt caching for portfolio context (reduces costs by 90%)
    - Automatic cost calculation from usage stats
    - Error handling and retries
    - Configurable temperature and max tokens
    """

    # Anthropic pricing for Claude 3.5 Haiku (as of Oct 2024)
    # Source: https://www.anthropic.com/pricing
    PRICING = {
        "input_tokens": 0.80 / 1_000_000,      # $0.80 per million tokens
        "output_tokens": 4.00 / 1_000_000,      # $4.00 per million tokens
        "cache_creation": 1.00 / 1_000_000,     # $1.00 per million tokens (write)
        "cache_read": 0.08 / 1_000_000,         # $0.08 per million tokens (90% discount)
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        """
        Initialize LLM service.

        Args:
            api_key: Anthropic API key (defaults to settings.anthropic_api_key)
            model: Model name (defaults to settings.llm_model)
            max_tokens: Maximum tokens in response (defaults to settings.max_tokens)
            temperature: Sampling temperature (defaults to settings.temperature)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.llm_model
        self.max_tokens = max_tokens or settings.max_tokens
        self.temperature = temperature or settings.temperature

        # Initialize Anthropic client
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"LLM service initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise

    def _build_system_prompt(self, portfolio_context: str) -> str:
        """
        Build the system prompt with portfolio context.

        Args:
            portfolio_context: Formatted portfolio context from context_loader

        Returns:
            System prompt string
        """
        system_prompt = f"""You are an AI assistant for Anirudh Nuti's portfolio website. Your role is to help visitors learn about Anirudh's professional background, skills, experience, projects, and how to contact him.

PORTFOLIO INFORMATION:
{portfolio_context}

GUIDELINES:
1. Answer questions accurately based on the portfolio information provided above
2. Be professional, friendly, and concise
3. If asked about something not in the portfolio context, politely say you don't have that information
4. For contact inquiries, provide the email and LinkedIn information
5. Highlight relevant achievements and measurable impact when appropriate
6. If the user asks a technical question about Anirudh's skills, provide specific examples from the context
7. Keep responses focused and under 200 words unless more detail is explicitly requested
8. Use a conversational but professional tone

Remember: You represent Anirudh's professional brand. Be helpful, accurate, and enthusiastic about his work!"""

        return system_prompt

    def generate_response(
        self,
        user_message: str,
        portfolio_context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_cache: bool = True
    ) -> Tuple[str, Dict]:
        """
        Generate a response using Claude API.

        Args:
            user_message: User's message
            portfolio_context: Formatted portfolio context
            conversation_history: Previous messages (optional)
            use_cache: Whether to use prompt caching (default: True)

        Returns:
            Tuple of (response_text, usage_stats)
            usage_stats contains: {
                "input_tokens": int,
                "output_tokens": int,
                "cache_creation_tokens": int,
                "cache_read_tokens": int,
                "total_tokens": int,
                "cost_usd": float
            }
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(portfolio_context)

            # Build messages array
            messages = []

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Create API request parameters
            request_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": messages
            }

            # Add system prompt with caching if enabled
            if use_cache:
                # Use prompt caching for system context
                # This caches the portfolio context, saving ~90% on repeated queries
                request_params["system"] = [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            else:
                request_params["system"] = system_prompt

            logger.info(f"Sending request to Claude API (cache: {use_cache})")

            # Make API call
            response = self.client.messages.create(**request_params)

            # Extract response text
            response_text = response.content[0].text

            # Extract usage statistics
            usage = response.usage
            usage_stats = self._calculate_usage_stats(usage)

            logger.info(
                f"Response generated: {usage_stats['total_tokens']} tokens, "
                f"${usage_stats['cost_usd']:.6f}"
            )

            return response_text, usage_stats

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def _calculate_usage_stats(self, usage: anthropic.types.Usage) -> Dict:
        """
        Calculate cost and aggregate usage statistics.

        Args:
            usage: Usage object from Anthropic API response

        Returns:
            Dictionary with usage stats and cost
        """
        # Extract token counts
        input_tokens = getattr(usage, 'input_tokens', 0)
        output_tokens = getattr(usage, 'output_tokens', 0)
        cache_creation_tokens = getattr(usage, 'cache_creation_input_tokens', 0)
        cache_read_tokens = getattr(usage, 'cache_read_input_tokens', 0)

        # Calculate costs
        input_cost = input_tokens * self.PRICING["input_tokens"]
        output_cost = output_tokens * self.PRICING["output_tokens"]
        cache_creation_cost = cache_creation_tokens * self.PRICING["cache_creation"]
        cache_read_cost = cache_read_tokens * self.PRICING["cache_read"]

        total_cost = input_cost + output_cost + cache_creation_cost + cache_read_cost
        total_tokens = input_tokens + output_tokens + cache_creation_tokens + cache_read_tokens

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_creation_tokens": cache_creation_tokens,
            "cache_read_tokens": cache_read_tokens,
            "total_tokens": total_tokens,
            "cost_usd": total_cost
        }

    def generate_greeting_response(self, user_name: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Generate a simple greeting response without full context.

        Args:
            user_name: Optional user name for personalization

        Returns:
            Tuple of (response_text, usage_stats)
        """
        greeting_message = (
            f"Hello{' ' + user_name if user_name else ''}! "
            "I'm Anirudh's AI assistant. I can help you learn about his professional background, "
            "skills, experience, projects, and how to get in touch with him. "
            "What would you like to know?"
        )

        # For greetings, we return a canned response with minimal cost
        usage_stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_tokens": 0,
            "cache_read_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0
        }

        logger.info("Generated greeting response (no API call)")
        return greeting_message, usage_stats

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        use_cache: bool = False,
        cache_hit: bool = False
    ) -> float:
        """
        Estimate cost for a request.

        Args:
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens
            use_cache: Whether caching is used
            cache_hit: Whether cache will be hit (vs. cache write)

        Returns:
            Estimated cost in USD
        """
        if use_cache and cache_hit:
            # Cache read is 90% cheaper
            input_cost = input_tokens * self.PRICING["cache_read"]
        elif use_cache:
            # Cache creation (first time)
            input_cost = input_tokens * self.PRICING["cache_creation"]
        else:
            # Normal input
            input_cost = input_tokens * self.PRICING["input_tokens"]

        output_cost = output_tokens * self.PRICING["output_tokens"]

        return input_cost + output_cost


# Global LLM service instance
llm_service = LLMService()

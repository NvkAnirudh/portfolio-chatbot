"""
Unit tests for LLM Service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.llm_service import LLMService
import anthropic


class TestLLMService:
    """Test suite for LLMService"""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mocked Anthropic client"""
        with patch('anthropic.Anthropic') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def service(self, mock_anthropic_client):
        """Create LLM service with mocked client"""
        return LLMService(
            api_key="test-api-key",
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            temperature=0.7
        )

    def test_initialization(self, service):
        """Test service initializes correctly"""
        assert service.model == "claude-3-5-haiku-20241022"
        assert service.max_tokens == 1000
        assert service.temperature == 0.7
        assert service.client is not None

    def test_pricing_constants(self):
        """Test pricing constants are defined"""
        assert LLMService.PRICING["input_tokens"] > 0
        assert LLMService.PRICING["output_tokens"] > 0
        assert LLMService.PRICING["cache_creation"] > 0
        assert LLMService.PRICING["cache_read"] > 0
        # Cache read should be cheaper than normal input
        assert LLMService.PRICING["cache_read"] < LLMService.PRICING["input_tokens"]

    def test_build_system_prompt(self, service):
        """Test system prompt construction"""
        context = "Anirudh Nuti is a data engineer with expertise in Python and SQL."
        prompt = service._build_system_prompt(context)

        assert "Anirudh Nuti" in prompt
        assert "portfolio" in prompt.lower()
        assert context in prompt
        assert "GUIDELINES" in prompt

    def test_generate_greeting_response(self, service):
        """Test greeting response generation"""
        response, usage = service.generate_greeting_response()

        assert "Anirudh" in response
        assert "assistant" in response.lower()
        assert usage["cost_usd"] == 0.0
        assert usage["total_tokens"] == 0

    def test_generate_greeting_response_with_name(self, service):
        """Test greeting response with user name"""
        response, usage = service.generate_greeting_response(user_name="John")

        assert "John" in response
        assert "Anirudh" in response

    def test_calculate_usage_stats_basic(self, service):
        """Test basic usage statistics calculation"""
        mock_usage = Mock()
        mock_usage.input_tokens = 1000
        mock_usage.output_tokens = 200
        mock_usage.cache_creation_input_tokens = 0
        mock_usage.cache_read_input_tokens = 0

        stats = service._calculate_usage_stats(mock_usage)

        assert stats["input_tokens"] == 1000
        assert stats["output_tokens"] == 200
        assert stats["total_tokens"] == 1200
        assert stats["cost_usd"] > 0

    def test_calculate_usage_stats_with_cache(self, service):
        """Test usage statistics with cache"""
        mock_usage = Mock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 200
        mock_usage.cache_creation_input_tokens = 500
        mock_usage.cache_read_input_tokens = 1000

        stats = service._calculate_usage_stats(mock_usage)

        assert stats["cache_creation_tokens"] == 500
        assert stats["cache_read_tokens"] == 1000
        assert stats["total_tokens"] == 1800
        # Cost should include cache costs
        assert stats["cost_usd"] > 0

    def test_estimate_cost_no_cache(self, service):
        """Test cost estimation without cache"""
        cost = service.estimate_cost(
            input_tokens=1000,
            output_tokens=200,
            use_cache=False
        )
        assert cost > 0
        # Should be roughly: 1000 * 0.80/1M + 200 * 4.00/1M
        expected = (1000 * 0.80 / 1_000_000) + (200 * 4.00 / 1_000_000)
        assert abs(cost - expected) < 0.000001

    def test_estimate_cost_with_cache_miss(self, service):
        """Test cost estimation with cache creation"""
        cost = service.estimate_cost(
            input_tokens=1000,
            output_tokens=200,
            use_cache=True,
            cache_hit=False
        )
        # Cache creation costs $1.00 per million tokens
        expected = (1000 * 1.00 / 1_000_000) + (200 * 4.00 / 1_000_000)
        assert abs(cost - expected) < 0.000001

    def test_estimate_cost_with_cache_hit(self, service):
        """Test cost estimation with cache hit"""
        cost = service.estimate_cost(
            input_tokens=1000,
            output_tokens=200,
            use_cache=True,
            cache_hit=True
        )
        # Cache read costs $0.08 per million tokens (90% discount)
        expected = (1000 * 0.08 / 1_000_000) + (200 * 4.00 / 1_000_000)
        assert abs(cost - expected) < 0.000001

    def test_cache_read_cheaper_than_normal(self, service):
        """Test that cache reads are significantly cheaper"""
        normal_cost = service.estimate_cost(1000, 200, use_cache=False)
        cache_hit_cost = service.estimate_cost(1000, 200, use_cache=True, cache_hit=True)

        # Cache hit should be much cheaper
        assert cache_hit_cost < normal_cost
        # Cache read input should be 90% cheaper (0.08 vs 0.80 per million)
        # But output cost is the same, so overall discount is less than 50%
        assert cache_hit_cost < normal_cost * 0.8  # At least 20% cheaper overall

    def test_generate_response_basic(self, service, mock_anthropic_client):
        """Test basic response generation"""
        # Mock API response
        mock_response = Mock()
        mock_response.content = [Mock(text="I have expertise in Python, SQL, and PySpark.")]
        mock_response.usage = Mock(
            input_tokens=500,
            output_tokens=100,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0
        )
        mock_anthropic_client.messages.create.return_value = mock_response

        # Generate response
        response_text, usage_stats = service.generate_response(
            user_message="What are your skills?",
            portfolio_context="Anirudh has skills in Python, SQL, PySpark",
            use_cache=False
        )

        assert "Python" in response_text
        assert usage_stats["input_tokens"] == 500
        assert usage_stats["output_tokens"] == 100
        assert usage_stats["cost_usd"] > 0

    def test_generate_response_with_history(self, service, mock_anthropic_client):
        """Test response generation with conversation history"""
        mock_response = Mock()
        mock_response.content = [Mock(text="I worked at Nidhi AI as a Founding Engineer.")]
        mock_response.usage = Mock(
            input_tokens=600,
            output_tokens=120,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0
        )
        mock_anthropic_client.messages.create.return_value = mock_response

        conversation_history = [
            {"role": "user", "content": "Tell me about yourself"},
            {"role": "assistant", "content": "I'm a data engineer..."}
        ]

        response_text, usage_stats = service.generate_response(
            user_message="Where do you work?",
            portfolio_context="Anirudh works at Nidhi AI",
            conversation_history=conversation_history,
            use_cache=False
        )

        # Verify messages were passed correctly
        call_args = mock_anthropic_client.messages.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 3  # 2 history + 1 new
        assert messages[0]["content"] == "Tell me about yourself"
        assert messages[2]["content"] == "Where do you work?"

    def test_generate_response_with_cache(self, service, mock_anthropic_client):
        """Test response generation with caching enabled"""
        mock_response = Mock()
        mock_response.content = [Mock(text="Response text")]
        mock_response.usage = Mock(
            input_tokens=100,
            output_tokens=50,
            cache_creation_input_tokens=500,
            cache_read_input_tokens=0
        )
        mock_anthropic_client.messages.create.return_value = mock_response

        response_text, usage_stats = service.generate_response(
            user_message="Test question",
            portfolio_context="Test context",
            use_cache=True
        )

        # Verify cache was enabled in request
        call_args = mock_anthropic_client.messages.create.call_args
        system_param = call_args.kwargs["system"]
        assert isinstance(system_param, list)
        assert system_param[0]["cache_control"]["type"] == "ephemeral"

        # Verify cache creation tokens tracked
        assert usage_stats["cache_creation_tokens"] == 500

    def test_generate_response_api_error(self, service, mock_anthropic_client):
        """Test error handling for API errors"""
        # Create a proper APIError with required arguments
        mock_request = Mock()
        mock_anthropic_client.messages.create.side_effect = anthropic.APIError(
            "API Error",
            request=mock_request,
            body=None
        )

        with pytest.raises(anthropic.APIError):
            service.generate_response(
                user_message="Test",
                portfolio_context="Context"
            )

    def test_generate_response_generic_error(self, service, mock_anthropic_client):
        """Test error handling for generic errors"""
        mock_anthropic_client.messages.create.side_effect = Exception("Unknown error")

        with pytest.raises(Exception):
            service.generate_response(
                user_message="Test",
                portfolio_context="Context"
            )

    def test_model_parameters_passed_correctly(self, service, mock_anthropic_client):
        """Test that model parameters are passed to API"""
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(
            input_tokens=100,
            output_tokens=50,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0
        )
        mock_anthropic_client.messages.create.return_value = mock_response

        service.generate_response(
            user_message="Test",
            portfolio_context="Context",
            use_cache=False
        )

        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-3-5-haiku-20241022"
        assert call_args.kwargs["max_tokens"] == 1000
        assert call_args.kwargs["temperature"] == 0.7

"""
Chat API Routes

Main chatbot endpoint that orchestrates all services:
- Intent classification
- Context loading
- Conversation history management
- LLM response generation
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
import uuid
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import ChatRequest, ChatResponse, MessageCreate
from app.services.intent_classifier import intent_classifier
from app.services.context_loader import context_loader
from app.services.conversation_manager import conversation_manager
from app.services.llm_service import llm_service
from app.db.session import get_db
from app.db.repository import SessionRepository, MessageRepository, CostTrackingRepository
from app.utils.logger import setup_logger
from app.middleware.rate_limiter import limiter
from app.middleware.security import sanitize_input, validate_session_id
from app.middleware.cost_control import check_cost_budget

logger = setup_logger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    http_request: Request,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Process a chat message and return AI response.

    Orchestrates the complete chatbot flow:
    1. Classify user message intent
    2. Load relevant portfolio context
    3. Retrieve conversation history
    4. Generate AI response with Claude
    5. Save conversation to history
    6. Return response with metadata

    Args:
        request: Chat request with message and session_id
        http_request: FastAPI request object for IP/user agent

    Returns:
        ChatResponse with AI response and metadata
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Validate session ID format if provided
        if request.session_id and not validate_session_id(request.session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Sanitize and validate user message
        user_message = sanitize_input(request.message, max_length=1000)

        logger.info(f"Processing chat request for session: {session_id}")

        # Create or get session in database
        client_ip = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent", "")

        db_session = await SessionRepository.get_or_create_session(
            db=db,
            session_id=session_id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        logger.info(f"Using session: {session_id}")

        # Step 1: Classify intent
        intents = intent_classifier.classify(user_message)
        primary_intent = intents[0] if intents else "general"

        logger.info(f"Classified intents: {intents}, primary: {primary_intent}")

        # Step 2: Handle greetings separately (no LLM call needed)
        if primary_intent == "greeting":
            response_text, usage_stats = llm_service.generate_greeting_response()

            # Save to conversation history (Redis)
            conversation_manager.add_message(
                session_id=session_id,
                role="user",
                content=user_message,
                metadata={"intent": intents}
            )
            conversation_manager.add_message(
                session_id=session_id,
                role="assistant",
                content=response_text,
                metadata={"intent": intents, "cost_usd": 0.0}
            )

            # Save to database (PostgreSQL)
            await MessageRepository.create_message(
                db=db,
                message_data=MessageCreate(
                    session_id=session_id,
                    role="user",
                    content=user_message,
                    intent=",".join(intents),
                    tokens_used=0,
                    cost_usd=0.0
                )
            )
            await MessageRepository.create_message(
                db=db,
                message_data=MessageCreate(
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    intent=primary_intent,
                    tokens_used=0,
                    cost_usd=0.0
                )
            )
            await db.commit()

            return ChatResponse(
                session_id=session_id,
                message=response_text,
                intent=primary_intent,
                tokens_used=0,
                cost_usd=0.0,
                cached=False
            )

        # Step 3: Load portfolio context based on intents
        # For "normal" casual conversations, this will return empty string
        portfolio_context = context_loader.get_context_for_intents(
            intents=intents,
            use_cache=True,
            include_headers=True
        )

        # If context is empty (e.g., for "normal" intent), pass None to LLM
        if not portfolio_context or portfolio_context.strip() == "":
            portfolio_context = None
            logger.info("No context loaded (casual conversation mode)")
        else:
            logger.info(f"Loaded context: {len(portfolio_context)} characters")

        # Step 4: Get conversation history
        conversation_history = conversation_manager.format_history_for_llm(
            session_id=session_id,
            limit=10  # Last 10 messages
        )

        logger.info(f"Retrieved {len(conversation_history)} messages from history")

        # Step 5: Generate AI response
        response_text, usage_stats = llm_service.generate_response(
            user_message=user_message,
            portfolio_context=portfolio_context,
            conversation_history=conversation_history,
            use_cache=True
        )

        logger.info(
            f"Generated response: {usage_stats['total_tokens']} tokens, "
            f"${usage_stats['cost_usd']:.6f}"
        )

        # Step 6: Save to conversation history (Redis)
        conversation_manager.add_message(
            session_id=session_id,
            role="user",
            content=user_message,
            metadata={
                "intent": intents,
                "tokens": usage_stats.get("input_tokens", 0)
            }
        )

        conversation_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=response_text,
            metadata={
                "intent": intents,
                "tokens": usage_stats.get("output_tokens", 0),
                "cost_usd": usage_stats.get("cost_usd", 0.0)
            }
        )

        # Save to database (PostgreSQL)
        await MessageRepository.create_message(
            db=db,
            message_data=MessageCreate(
                session_id=session_id,
                role="user",
                content=user_message,
                intent=",".join(intents),
                tokens_used=usage_stats.get("input_tokens", 0),
                cost_usd=0.0  # Cost is on assistant message
            )
        )
        await MessageRepository.create_message(
            db=db,
            message_data=MessageCreate(
                session_id=session_id,
                role="assistant",
                content=response_text,
                intent=primary_intent,
                tokens_used=usage_stats.get("total_tokens", 0),
                cost_usd=usage_stats.get("cost_usd", 0.0)
            )
        )

        # Update daily cost tracking
        cache_hit = usage_stats.get("cache_read_tokens", 0) > 0
        await CostTrackingRepository.update_daily_cost(
            db=db,
            date=datetime.now(),
            tokens=usage_stats.get("total_tokens", 0),
            cost=usage_stats.get("cost_usd", 0.0),
            is_cache_read=cache_hit
        )
        await db.commit()

        # Determine if cache was used
        cached = usage_stats.get("cache_read_tokens", 0) > 0

        # Step 7: Return response
        return ChatResponse(
            session_id=session_id,
            message=response_text,
            intent=primary_intent,
            tokens_used=usage_stats.get("total_tokens", 0),
            cost_usd=usage_stats.get("cost_usd", 0.0),
            cached=cached
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your message. Please try again."
        )


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """
    Get conversation history for a session.

    Args:
        session_id: Session identifier

    Returns:
        Conversation history and summary
    """
    try:
        if not conversation_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        history = conversation_manager.get_history(session_id)
        summary = conversation_manager.get_context_summary(session_id)

        return {
            "session_id": session_id,
            "history": history,
            "summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session history")


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear conversation history for a session.

    Args:
        session_id: Session identifier

    Returns:
        Success message
    """
    try:
        success = conversation_manager.clear_history(session_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear session")

        return {
            "session_id": session_id,
            "message": "Session cleared successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear session")


@router.get("/sessions/stats")
async def get_sessions_stats():
    """
    Get statistics about active sessions.

    Returns:
        Session statistics
    """
    try:
        stats = conversation_manager.get_session_stats()
        return stats

    except Exception as e:
        logger.error(f"Error retrieving session stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session stats")


@router.get("/budget/status")
async def get_budget_status(db: AsyncSession = Depends(get_db)):
    """
    Get current cost budget status.

    Returns:
        Budget utilization and remaining capacity
    """
    try:
        budget_status = await check_cost_budget(db)
        return budget_status

    except Exception as e:
        logger.error(f"Error retrieving budget status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve budget status")

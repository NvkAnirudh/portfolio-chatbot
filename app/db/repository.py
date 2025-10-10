"""
Database Repository Layer for CRUD Operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.db_models import Session, Message, Feedback, CostTracking
from app.models.schemas import MessageCreate, SessionCreate, FeedbackCreate
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionRepository:
    """Repository for Session operations"""

    @staticmethod
    async def create_session(db: AsyncSession, session_data: SessionCreate) -> Session:
        """Create a new session"""
        session = Session(
            id=session_data.id,
            ip_address=session_data.ip_address,
            user_agent=session_data.user_agent,
        )
        db.add(session)
        await db.flush()
        logger.info(f"Created session: {session.id}")
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_session(
        db: AsyncSession, session_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None
    ) -> Session:
        """Get existing session or create new one"""
        session = await SessionRepository.get_session(db, session_id)
        if not session:
            session_data = SessionCreate(
                id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session = await SessionRepository.create_session(db, session_data)
        return session

    @staticmethod
    async def get_session_count(db: AsyncSession) -> int:
        """Get total session count"""
        result = await db.execute(select(func.count(Session.id)))
        return result.scalar() or 0


class MessageRepository:
    """Repository for Message operations"""

    @staticmethod
    async def create_message(db: AsyncSession, message_data: MessageCreate) -> Message:
        """Create a new message"""
        message = Message(
            session_id=message_data.session_id,
            role=message_data.role,
            content=message_data.content,
            intent=message_data.intent,
            tokens_used=message_data.tokens_used,
            cost_usd=message_data.cost_usd,
        )
        db.add(message)
        await db.flush()
        logger.info(f"Created message: {message.id} for session: {message.session_id}")
        return message

    @staticmethod
    async def get_session_messages(
        db: AsyncSession, session_id: str, limit: int = 10
    ) -> List[Message]:
        """Get recent messages for a session"""
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        messages = result.scalars().all()
        return list(reversed(messages))  # Return in chronological order

    @staticmethod
    async def get_message_count(db: AsyncSession) -> int:
        """Get total message count"""
        result = await db.execute(select(func.count(Message.id)))
        return result.scalar() or 0

    @staticmethod
    async def get_session_message_count(db: AsyncSession, session_id: str) -> int:
        """Get message count for a specific session"""
        result = await db.execute(
            select(func.count(Message.id)).where(Message.session_id == session_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_total_cost(db: AsyncSession) -> float:
        """Get total cost across all messages"""
        result = await db.execute(select(func.sum(Message.cost_usd)))
        return result.scalar() or 0.0

    @staticmethod
    async def get_total_tokens(db: AsyncSession) -> int:
        """Get total tokens used across all messages"""
        result = await db.execute(select(func.sum(Message.tokens_used)))
        return result.scalar() or 0


class FeedbackRepository:
    """Repository for Feedback operations"""

    @staticmethod
    async def create_feedback(db: AsyncSession, feedback_data: FeedbackCreate) -> Feedback:
        """Create new feedback"""
        feedback = Feedback(
            session_id=feedback_data.session_id,
            message_id=feedback_data.message_id,
            rating=feedback_data.rating,
            comment=feedback_data.comment,
        )
        db.add(feedback)
        await db.flush()
        logger.info(f"Created feedback: {feedback.id} for session: {feedback.session_id}")
        return feedback


class CostTrackingRepository:
    """Repository for Cost Tracking operations"""

    @staticmethod
    async def get_or_create_daily_cost(db: AsyncSession, date: datetime) -> CostTracking:
        """Get or create cost tracking for a specific date"""
        # Normalize to start of day
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)

        result = await db.execute(
            select(CostTracking).where(CostTracking.date == day_start)
        )
        cost_tracking = result.scalar_one_or_none()

        if not cost_tracking:
            cost_tracking = CostTracking(date=day_start)
            db.add(cost_tracking)
            await db.flush()

        return cost_tracking

    @staticmethod
    async def update_daily_cost(
        db: AsyncSession,
        date: datetime,
        tokens: int,
        cost: float,
        is_cache_read: bool = False,
    ):
        """Update daily cost tracking"""
        cost_tracking = await CostTrackingRepository.get_or_create_daily_cost(db, date)

        cost_tracking.total_requests += 1
        cost_tracking.total_tokens += tokens
        cost_tracking.total_cost_usd += cost

        if is_cache_read:
            cost_tracking.cache_reads += 1
        else:
            cost_tracking.cache_writes += 1

        await db.flush()
        logger.info(f"Updated daily cost for {date.date()}: ${cost_tracking.total_cost_usd:.4f}")

    @staticmethod
    async def get_today_cost(db: AsyncSession) -> float:
        """Get today's total cost"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(CostTracking.total_cost_usd).where(CostTracking.date == today)
        )
        cost = result.scalar_one_or_none()
        return cost or 0.0

    @staticmethod
    async def get_today_requests(db: AsyncSession) -> int:
        """Get today's total requests"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(CostTracking.total_requests).where(CostTracking.date == today)
        )
        requests = result.scalar_one_or_none()
        return requests or 0

    @staticmethod
    async def get_today_tracking(db: AsyncSession) -> Optional[dict]:
        """Get today's complete cost tracking data"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(CostTracking).where(CostTracking.date == today)
        )
        tracking = result.scalar_one_or_none()

        if not tracking:
            return None

        return {
            "total_tokens": tracking.total_tokens,
            "cache_read_tokens": tracking.cache_reads,  # Approximate - not exact token count
            "requests": tracking.total_requests,
            "total_cost_usd": tracking.total_cost_usd,
            "cache_writes": tracking.cache_writes
        }

    @staticmethod
    async def get_recent_daily_costs(db: AsyncSession, days: int = 7) -> List[CostTracking]:
        """Get recent daily cost tracking records"""
        start_date = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(CostTracking)
            .where(CostTracking.date >= start_date)
            .order_by(desc(CostTracking.date))
        )
        return list(result.scalars().all())

"""
Pydantic Schemas for Request/Response Validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Chat Schemas
class ChatRequest(BaseModel):
    """Chat request from frontend"""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Chat response to frontend"""
    response: str = Field(..., description="Bot response")
    session_id: str = Field(..., description="Session ID")
    intent: Optional[str] = Field(None, description="Detected intent")


# Message Schemas
class MessageCreate(BaseModel):
    """Schema for creating a message"""
    session_id: str
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    intent: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: int
    session_id: str
    role: str
    content: str
    intent: Optional[str]
    tokens_used: Optional[int]
    cost_usd: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# Session Schemas
class SessionCreate(BaseModel):
    """Schema for creating a session"""
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SessionResponse(BaseModel):
    """Schema for session response"""
    id: str
    created_at: datetime
    updated_at: datetime
    ip_address: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# Feedback Schemas
class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    session_id: str
    message_id: Optional[int] = None
    rating: Optional[int] = Field(None, ge=0, le=5)
    comment: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: int
    session_id: str
    message_id: Optional[int]
    rating: Optional[int]
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics Schemas
class ConversationStats(BaseModel):
    """Conversation statistics"""
    total_sessions: int
    total_messages: int
    avg_messages_per_session: float
    total_cost_usd: float
    total_tokens: int


class DailyCostStats(BaseModel):
    """Daily cost statistics"""
    date: str
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    cache_reads: int
    cache_writes: int


class AnalyticsResponse(BaseModel):
    """Analytics response"""
    conversation_stats: ConversationStats
    recent_daily_costs: List[DailyCostStats]
    top_intents: List[dict]

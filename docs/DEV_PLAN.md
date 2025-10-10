# Portfolio Chatbot - Development Plan

## Project Overview
Build an intelligent chatbot for Anirudh's portfolio using Python FastAPI backend with Claude LLM, smart context loading, conversation memory, and prompt caching for cost optimization.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + Vite)                        │
│                     Portfolio Website on Vercel                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTP/REST
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI on Railway)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐          ┌──────────────────┐                      │
│  │  Chat Router    │          │  Health Check    │                      │
│  │  /api/chat      │          │  /health         │                      │
│  └────────┬────────┘          └──────────────────┘                      │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────────────────────────────────────────────┐            │
│  │              Request Processing Pipeline                 │            │
│  │                                                           │            │
│  │  1. Validate Request (Pydantic)                          │            │
│  │           ↓                                               │            │
│  │  2. Intent Classifier                                    │            │
│  │     - Keyword matching                                   │            │
│  │     - Detect: skills/projects/experience/etc.            │            │
│  │           ↓                                               │            │
│  │  3. Context Loader                                       │            │
│  │     - Load relevant .txt files                           │            │
│  │     - Map intent → context                               │            │
│  │           ↓                                               │            │
│  │  4. History Manager (Redis)                              │            │
│  │     - Retrieve session history                           │            │
│  │     - Format for LLM                                     │            │
│  │           ↓                                               │            │
│  │  5. LLM Service (Claude API)                             │            │
│  │     - Build prompt with cached context                   │            │
│  │     - Send to Anthropic Claude                           │            │
│  │     - Get response                                       │            │
│  │           ↓                                               │            │
│  │  6. Update History                                       │            │
│  │     - Store Q&A in Redis                                 │            │
│  │     - Set TTL (30 min)                                   │            │
│  │           ↓                                               │            │
│  │  7. Return Response                                      │            │
│  └─────────────────────────────────────────────────────────┘            │
│                                                                           │
└───────────────────┬───────────────────────────────────┬─────────────────┘
                    │                                   │
                    ▼                                   ▼
        ┌───────────────────────┐         ┌──────────────────────────┐
        │   Redis (Railway)     │         │  Anthropic Claude API    │
        │                       │         │                          │
        │  - Session cache      │         │  - Claude 3.5 Haiku      │
        │  - Rate limiting      │         │  - Prompt caching        │
        │  - Cost tracking      │         │  - Response generation   │
        │  - TTL: 30 min        │         │                          │
        └───────────────────────┘         └──────────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────────────────┐
        │   PostgreSQL Database (Railway)             │
        │                                             │
        │  Tables:                                    │
        │  - sessions (conversation metadata)         │
        │  - messages (all Q&A, persistent)           │
        │  - feedback (user ratings - optional)       │
        │                                             │
        │  Benefits:                                  │
        │  ✓ Long-term message storage                │
        │  ✓ Analytics & insights                     │
        │  ✓ Audit trail                              │
        │  ✓ User behavior analysis                   │
        └─────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
User Types Message
       │
       ▼
┌──────────────────┐
│  Frontend sends  │
│  POST /api/chat  │
│  {               │
│   sessionId,     │
│   message        │
│  }               │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Intent Classifier                  │
│  "What are your skills?" → "skills" │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Context Loader                     │
│  Load: context/skills_context.txt   │
│  (~300 tokens)                      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Redis: Get History                 │
│  GET session:abc123                 │
│  Returns: [prev messages...]        │
└────────┬────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│  Build Prompt                                     │
│                                                   │
│  System (CACHED):                                 │
│  "You are Anirudh's assistant.                    │
│   Context: [skills_context.txt content]"         │
│                                                   │
│  Messages:                                        │
│  - Previous Q&A pairs from history               │
│  - New user message                               │
└────────┬─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Anthropic Claude API               │
│  - First call: Cache WRITE          │
│  - Subsequent: Cache READ (90% off) │
│  Returns: AI response               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Redis: Update History              │
│  APPEND to session:abc123           │
│  SET TTL 1800 seconds               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Return Response                    │
│  {                                  │
│   sessionId,                        │
│   response,                         │
│   tokensUsed                        │
│  }                                  │
└────────┬────────────────────────────┘
         │
         ▼
   Display to User
```

---

## Technology Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Server:** Uvicorn (ASGI)
- **Validation:** Pydantic v2
- **Cache/Sessions:** Redis (Railway add-on)
- **Database:** PostgreSQL 15+ (Railway add-on)
- **ORM:** SQLAlchemy 2.0 with async support
- **LLM:** Anthropic Claude 3.5 Haiku with prompt caching

### Key Libraries
```
fastapi==0.109.0            # Web framework
uvicorn[standard]==0.27.0   # ASGI server
anthropic==0.18.0           # Claude SDK
redis==5.0.1                # Redis client (cache/sessions)
sqlalchemy==2.0.25          # ORM for PostgreSQL
asyncpg==0.29.0             # Async PostgreSQL driver
alembic==1.13.1             # Database migrations
python-dotenv==1.0.0        # Environment variables
pydantic==2.5.0             # Data validation
pydantic-settings==2.1.0    # Settings management
slowapi==0.1.9              # Rate limiting
```

### Deployment
- **Platform:** Railway
- **Cache:** Redis (managed Railway add-on)
- **Database:** PostgreSQL (managed Railway add-on)
- **CI/CD:** GitHub integration (auto-deploy)
- **Frontend:** Vercel (existing)

### Data Architecture
```
PostgreSQL: Long-term persistent storage
  - Conversations (all messages, sessions)
  - User analytics
  - Feedback & ratings
  - Cost tracking history

Redis: Fast temporary storage
  - Active session cache (30 min TTL)
  - Rate limiting counters
  - Real-time cost tracking
```

---

## Directory Structure

```
chatbot-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app + CORS setup
│   ├── config.py                    # Settings (Pydantic BaseSettings)
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py                  # Chat endpoints
│   │   └── analytics.py             # Analytics endpoints (optional)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── intent_classifier.py     # Intent detection logic
│   │   ├── context_loader.py        # Load context files
│   │   ├── llm_service.py           # Claude API integration
│   │   ├── history_manager.py       # Redis session cache
│   │   ├── rate_limiter.py          # Rate limiting services
│   │   └── cost_monitor.py          # Cost tracking
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py               # Pydantic request/response models
│   │   └── db_models.py             # SQLAlchemy database models
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py               # Database session management
│   │   └── repository.py            # Database operations
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py                # Logging configuration
│
├── alembic/
│   ├── versions/                    # Database migration scripts
│   ├── env.py
│   └── script.py.mako
│
├── context/
│   ├── skills_context.txt           # Skills & technologies (~300 tokens)
│   ├── projects_context.txt         # Projects & implementations (~400 tokens)
│   ├── experience_context.txt       # Work experience (~300 tokens)
│   ├── education_context.txt        # Education & background (~200 tokens)
│   └── general_context.txt          # About, contact, availability (~250 tokens)
│
├── tests/
│   ├── __init__.py
│   ├── test_intent.py               # Intent classifier tests
│   ├── test_context.py              # Context loader tests
│   └── test_api.py                  # API endpoint tests
│
├── docs/
│   └── DEV_PLAN.md                  # This file
│
├── .env.example                     # Environment variables template
├── .gitignore
├── requirements.txt                 # Python dependencies
├── Procfile                         # Railway deployment config
├── runtime.txt                      # Python version specification
└── README.md                        # Project documentation
```

---

## Implementation Plan

### Phase 1: Setup & Foundation (30 minutes)
**Tasks:**
1. Initialize Python virtual environment
2. Create `requirements.txt` with dependencies
3. Set up FastAPI project structure (app/, routes/, services/, models/)
4. Create `.env.example` and `.gitignore`
5. Build basic FastAPI app with health check endpoint
6. Configure CORS for frontend

**Deliverables:**
- Working FastAPI server running locally
- Project structure in place
- Dependencies installed

**Files Created:**
- `app/main.py`
- `app/config.py`
- `requirements.txt`
- `.env.example`
- `Procfile`
- `runtime.txt`

---

### Phase 2: Database Setup & Models (1 hour)
**Tasks:**

1. **Install Database Dependencies:**
   ```bash
   pip install sqlalchemy==2.0.25 asyncpg==0.29.0 alembic==1.13.1
   ```

2. **Create Database Models** (`app/models/db_models.py`):
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
   from sqlalchemy.ext.declarative import declarative_base
   from sqlalchemy.orm import relationship
   from datetime import datetime

   Base = declarative_base()

   class Session(Base):
       """Conversation sessions"""
       __tablename__ = "sessions"

       id = Column(String(100), primary_key=True)  # session_id
       created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       ip_address = Column(String(45), nullable=True)  # Store for analytics
       user_agent = Column(String(500), nullable=True)

       # Relationships
       messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

   class Message(Base):
       """Individual chat messages"""
       __tablename__ = "messages"

       id = Column(Integer, primary_key=True, autoincrement=True)
       session_id = Column(String(100), ForeignKey("sessions.id"), nullable=False)
       role = Column(String(20), nullable=False)  # 'user' or 'assistant'
       content = Column(Text, nullable=False)
       intent = Column(String(100), nullable=True)  # Detected intent
       tokens_used = Column(Integer, nullable=True)
       cost_usd = Column(Float, nullable=True)
       created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

       # Relationships
       session = relationship("Session", back_populates="messages")

   class Feedback(Base):
       """User feedback on responses (optional)"""
       __tablename__ = "feedback"

       id = Column(Integer, primary_key=True, autoincrement=True)
       message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
       rating = Column(Integer, nullable=True)  # 1-5 stars or thumbs up/down
       comment = Column(Text, nullable=True)
       created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
   ```

3. **Create Database Session Manager** (`app/db/session.py`):
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
   from sqlalchemy.orm import sessionmaker
   from app.config import settings

   # Create async engine
   engine = create_async_engine(
       settings.DATABASE_URL,
       echo=True if settings.LOG_LEVEL == "DEBUG" else False,
       future=True
   )

   # Create async session factory
   AsyncSessionLocal = sessionmaker(
       engine,
       class_=AsyncSession,
       expire_on_commit=False
   )

   async def get_db():
       """Dependency for FastAPI routes"""
       async with AsyncSessionLocal() as session:
           yield session
   ```

4. **Create Repository Layer** (`app/db/repository.py`):
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, func
   from app.models.db_models import Session, Message, Feedback
   from datetime import datetime, timedelta

   class ChatRepository:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def create_session(self, session_id: str, ip: str = None, user_agent: str = None):
           """Create new conversation session"""
           session = Session(id=session_id, ip_address=ip, user_agent=user_agent)
           self.db.add(session)
           await self.db.commit()
           return session

       async def add_message(
           self,
           session_id: str,
           role: str,
           content: str,
           intent: str = None,
           tokens: int = None,
           cost: float = None
       ):
           """Add message to database"""
           message = Message(
               session_id=session_id,
               role=role,
               content=content,
               intent=intent,
               tokens_used=tokens,
               cost_usd=cost
           )
           self.db.add(message)
           await self.db.commit()
           return message

       async def get_session_messages(self, session_id: str, limit: int = 50):
           """Get messages for a session"""
           result = await self.db.execute(
               select(Message)
               .where(Message.session_id == session_id)
               .order_by(Message.created_at.desc())
               .limit(limit)
           )
           return result.scalars().all()

       async def get_daily_stats(self, date: datetime = None):
           """Get analytics for a specific day"""
           if date is None:
               date = datetime.utcnow()

           start = date.replace(hour=0, minute=0, second=0, microsecond=0)
           end = start + timedelta(days=1)

           # Total messages
           total_messages = await self.db.execute(
               select(func.count(Message.id))
               .where(Message.created_at >= start, Message.created_at < end)
           )

           # Total cost
           total_cost = await self.db.execute(
               select(func.sum(Message.cost_usd))
               .where(Message.created_at >= start, Message.created_at < end)
           )

           return {
               "total_messages": total_messages.scalar() or 0,
               "total_cost": total_cost.scalar() or 0.0
           }
   ```

5. **Initialize Alembic** (Database Migrations):
   ```bash
   alembic init alembic
   ```

   Update `alembic/env.py`:
   ```python
   from app.models.db_models import Base
   from app.config import settings

   target_metadata = Base.metadata
   config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
   ```

6. **Create Initial Migration:**
   ```bash
   alembic revision --autogenerate -m "Initial tables"
   alembic upgrade head
   ```

**Deliverables:**
- SQLAlchemy models (Session, Message, Feedback)
- Database session management
- Repository layer for CRUD operations
- Alembic migrations setup
- Initial database schema created

**Benefits:**
- ✅ Persistent storage of all conversations
- ✅ Analytics & insights capability
- ✅ Audit trail for debugging
- ✅ User behavior analysis
- ✅ Cost tracking over time

---

### Phase 3: Context Files Creation (1 hour)
**Tasks:**
1. Research and compile portfolio information
2. Create 5 context files in `/context`:
   - `skills_context.txt` - Programming languages, frameworks, tools
   - `projects_context.txt` - Project descriptions, tech stacks, achievements
   - `experience_context.txt` - Work history, roles, responsibilities
   - `education_context.txt` - Academic background, certifications
   - `general_context.txt` - Bio, contact info, availability, interests

**Guidelines:**
- Keep each file 200-400 tokens (~150-300 words)
- Use clear, concise language
- Format for LLM consumption (bullet points, sections)
- Include specific, relevant details

**Deliverables:**
- 5 well-structured context files
- Total context size: ~1200-1500 tokens

**Example Format:**
```
SKILLS & TECHNOLOGIES

Programming Languages:
- Python: Advanced (5+ years) - AI/ML, backend development
- JavaScript/TypeScript: Advanced - React, Node.js, full-stack
- Java: Intermediate - Enterprise applications
- C++: Intermediate - Systems programming

Frontend Development:
- React.js, Next.js - Modern web applications
- Tailwind CSS, Material-UI - Responsive design
...
```

---

### Phase 4: Intent Classification (1 hour)
**Tasks:**
1. Build `intent_classifier.py`:
   - Keyword-based classification function
   - Categories: skills, projects, experience, education, contact, general
   - Multi-intent support (e.g., skills + projects)
   - Fallback to "general" for unclear queries

**Logic:**
```python
def classify_intent(message: str) -> list[str]:
    """
    Classify user message into intent categories.
    Returns list of intents (can be multiple).
    """
    message_lower = message.lower()
    intents = []

    # Skills
    if any(word in message_lower for word in
           ['skill', 'technology', 'tech stack', 'programming', 'language']):
        intents.append('skills')

    # Projects
    if any(word in message_lower for word in
           ['project', 'built', 'developed', 'created']):
        intents.append('projects')

    # ... more logic

    return intents if intents else ['general']
```

**Deliverables:**
- Intent classification function
- Unit tests (optional)
- Support for 6 intent categories

---

### Phase 5: Context Loader (30 minutes)
**Tasks:**
1. Build `context_loader.py`:
   - Read context files from `/context` directory
   - Cache loaded contexts in memory
   - Map intent → context file(s)
   - Combine multiple contexts when needed
   - Handle file read errors gracefully

**Features:**
```python
class ContextLoader:
    def __init__(self):
        self._cache = {}  # In-memory cache

    def load_context(self, intents: list[str]) -> str:
        """Load and combine contexts based on intents."""
        # Load relevant context files
        # Combine if multiple intents
        # Return as single string
        pass
```

**Deliverables:**
- Context loading service with caching
- Error handling for missing files
- Efficient file reading

---

### Phase 6: Conversation History Manager (1 hour)
**Tasks:**
1. Build `history_manager.py`:
   - Redis client setup
   - Store conversation history per session ID
   - Retrieve history for session
   - Limit to last 10 messages (token optimization)
   - Auto-expire sessions after 30 minutes (TTL)
   - Handle Redis connection errors

**Data Structure in Redis:**
```python
Key: f"session:{session_id}"
Value: JSON string of messages list
TTL: 1800 seconds (30 minutes)

Example:
{
    "messages": [
        {"role": "user", "content": "What are your skills?"},
        {"role": "assistant", "content": "I have expertise in..."}
    ],
    "created_at": "2025-10-09T10:30:00Z"
}
```

**Methods:**
```python
class HistoryManager:
    async def get_history(self, session_id: str) -> list[dict]
    async def add_message(self, session_id: str, role: str, content: str)
    async def clear_session(self, session_id: str)
```

**Deliverables:**
- Redis-based session management
- TTL for auto-cleanup
- Error handling for Redis failures

---

### Phase 7: LLM Service Integration (2 hours)
**Tasks:**
1. Build `llm_service.py`:
   - Set up Anthropic async client
   - Implement prompt caching
   - Build system prompt template
   - Format conversation history
   - Handle API errors and retries
   - Track token usage

**Prompt Structure:**
```python
system_prompt = [
    {
        "type": "text",
        "text": f"""You are a helpful assistant for Anirudh Nuti's portfolio website.

Your role:
- Answer questions based ONLY on the context provided
- Be concise, friendly, and professional
- If information is not in the context, politely say you don't have that information
- Encourage visitors to check other sections or contact Anirudh directly

Context:
{context}
""",
        "cache_control": {"type": "ephemeral"}  # Enable caching
    }
]
```

**API Call:**
```python
async def get_llm_response(
    context: str,
    history: list[dict],
    message: str
) -> tuple[str, int]:
    """
    Get response from Claude API.
    Returns (response_text, tokens_used)
    """
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    response = await client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=500,
        system=[...],  # System prompt with caching
        messages=history + [{"role": "user", "content": message}]
    )

    return response.content[0].text, response.usage.input_tokens
```

**Deliverables:**
- Claude API integration with async
- Prompt caching implementation
- Error handling and retries
- Token usage tracking

---

### Phase 8: API Endpoints with Database Integration (1.5 hours)
**Tasks:**
1. Build `schemas.py` - Pydantic models:
   ```python
   class ChatRequest(BaseModel):
       session_id: str = Field(..., min_length=1)
       message: str = Field(..., min_length=1, max_length=500)

   class ChatResponse(BaseModel):
       session_id: str
       response: str
       tokens_used: int | None = None
   ```

2. Build `chat.py` - Route handlers:
   - `POST /api/chat` - Main chat endpoint
   - `POST /api/chat/new-session` - Create new session ID
   - `DELETE /api/chat/session/{session_id}` - Clear session history
   - `GET /api/chat/health` - Health check

**Main Chat Endpoint Flow:**
```python
@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # 1. Classify intent
    intents = classify_intent(request.message)

    # 2. Load context
    context = context_loader.load_context(intents)

    # 3. Get history
    history = await history_manager.get_history(request.session_id)

    # 4. Get LLM response
    response, tokens = await get_llm_response(context, history, request.message)

    # 5. Update history
    await history_manager.add_message(request.session_id, "user", request.message)
    await history_manager.add_message(request.session_id, "assistant", response)

    # 6. Return
    return ChatResponse(
        session_id=request.session_id,
        response=response,
        tokens_used=tokens
    )
```

**Deliverables:**
- RESTful chat endpoints
- Pydantic validation
- Error handling with proper HTTP status codes

---

### Phase 9: Integration & Testing (1-2 hours)
**Tasks:**
1. Connect all services in main FastAPI app
2. Test end-to-end flow:
   - Send various questions across all topics
   - Verify intent classification accuracy
   - Check context loading correctness
   - Validate history persistence
   - Assess LLM response quality
3. Test edge cases:
   - Invalid/missing session IDs
   - Empty messages
   - Very long messages
   - API failures (mock)
   - Redis connection issues
4. Load testing (optional):
   - Use `locust` or `pytest-benchmark`
   - Test concurrent requests

**Test Scenarios:**
```python
# Test 1: Skills question
POST /api/chat
{
  "session_id": "test-001",
  "message": "What programming languages do you know?"
}
# Expected: Response with skills from context

# Test 2: Follow-up (conversation memory)
POST /api/chat
{
  "session_id": "test-001",
  "message": "Which one is your favorite?"
}
# Expected: Contextual response referencing previous answer

# Test 3: Multi-intent
POST /api/chat
{
  "session_id": "test-002",
  "message": "What skills did you use in your projects?"
}
# Expected: Combined context from skills + projects
```

**Deliverables:**
- Fully integrated system
- Test results documentation
- Bug fixes

---

### Phase 10: Security & Rate Limiting (1.5 hours) 🔒 **CRITICAL**
**Tasks:**

1. **Install Security Dependencies:**
   ```bash
   pip install slowapi==0.1.9
   ```

2. **Implement Rate Limiting Service** (`app/services/rate_limiter.py`):
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   from fastapi import Request, HTTPException
   import redis.asyncio as redis

   # IP-based rate limiting (slowapi)
   limiter = Limiter(key_func=get_remote_address)

   # Session-based rate limiting (Redis)
   class SessionRateLimiter:
       def __init__(self, redis_client):
           self.redis = redis_client

       async def check_limit(self, session_id: str,
                           max_requests: int = 20,
                           window: int = 3600) -> bool:
           """Check if session has exceeded rate limit"""
           key = f"rate_limit:session:{session_id}"
           count = await self.redis.get(key)

           if count and int(count) >= max_requests:
               return False

           await self.redis.incr(key)
           await self.redis.expire(key, window)
           return True

   # Daily global limit
   async def check_daily_limit(redis_client, max_daily: int = 1000):
       """Check total daily requests across all users"""
       from datetime import datetime
       today = datetime.now().strftime("%Y-%m-%d")
       key = f"daily_requests:{today}"
       count = await redis_client.get(key)

       if count and int(count) >= max_daily:
           raise HTTPException(429, "Daily limit reached. Try tomorrow.")

       await redis_client.incr(key)
       await redis_client.expire(key, 86400)  # 24 hours
   ```

3. **Enhanced Input Validation** (`app/models/schemas.py`):
   ```python
   from pydantic import BaseModel, Field, validator
   import re

   class ChatRequest(BaseModel):
       session_id: str = Field(..., min_length=1, max_length=100)
       message: str = Field(..., min_length=1, max_length=500)

       @validator('message')
       def validate_message(cls, v):
           # Block repeated character spam
           if any(v.count(char) > 20 for char in set(v)):
               raise ValueError("Invalid message format")

           # Require actual text content
           if not any(c.isalpha() for c in v):
               raise ValueError("Message must contain text")

           # Block URL spam
           url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
           if len(re.findall(url_pattern, v)) > 1:
               raise ValueError("Too many links")

           # Block common spam keywords
           spam_words = ['viagra', 'crypto', 'investment', 'casino']
           if any(word in v.lower() for word in spam_words):
               raise ValueError("Message contains prohibited content")

           return v.strip()
   ```

4. **Cost Monitoring Service** (`app/services/cost_monitor.py`):
   ```python
   from datetime import datetime
   import redis.asyncio as redis
   from fastapi import HTTPException

   class CostMonitor:
       def __init__(self, redis_client, daily_limit_usd: float = 5.0):
           self.redis = redis_client
           self.daily_limit = daily_limit_usd
           self.cost_per_1k_tokens = {
               'input': 0.0008,
               'output': 0.004,
               'cache_read': 0.00008,
               'cache_write': 0.001
           }

       async def log_usage(self, tokens: dict):
           """Log token usage and calculate cost"""
           today = datetime.now().strftime("%Y-%m-%d")

           # Calculate cost in micro-dollars (to avoid float precision)
           cost_micro = int(
               tokens.get('input', 0) * self.cost_per_1k_tokens['input'] / 1000 * 1_000_000 +
               tokens.get('output', 0) * self.cost_per_1k_tokens['output'] / 1000 * 1_000_000
           )

           # Increment daily cost
           key = f"daily_cost:{today}"
           await self.redis.hincrby(key, "total", cost_micro)
           await self.redis.expire(key, 86400 * 7)  # Keep for 7 days

           return cost_micro / 1_000_000  # Return actual dollars

       async def check_budget(self):
           """Check if daily budget exceeded"""
           today = datetime.now().strftime("%Y-%m-%d")
           key = f"daily_cost:{today}"
           cost_micro = await self.redis.hget(key, "total")

           if cost_micro:
               cost_usd = int(cost_micro) / 1_000_000
               if cost_usd >= self.daily_limit:
                   # Disable chatbot
                   await self.redis.set("chatbot_disabled", "1", ex=3600)
                   raise HTTPException(503, "Service temporarily unavailable")
   ```

5. **Update Chat Endpoint with All Protections** (`app/routes/chat.py`):
   ```python
   from fastapi import APIRouter, Request, HTTPException, Depends
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   from app.services.rate_limiter import limiter, SessionRateLimiter, check_daily_limit
   from app.services.cost_monitor import CostMonitor

   router = APIRouter()

   @router.post("/", response_model=ChatResponse)
   @limiter.limit("10/minute")   # Max 10 requests per minute per IP
   @limiter.limit("50/hour")     # Max 50 requests per hour per IP
   async def chat(
       request: Request,
       chat_request: ChatRequest,
       redis_client = Depends(get_redis),
       session_limiter = Depends(get_session_limiter),
       cost_monitor = Depends(get_cost_monitor)
   ):
       # 1. Check if chatbot is disabled (budget exceeded)
       if await redis_client.get("chatbot_disabled"):
           raise HTTPException(
               503,
               "Chatbot temporarily unavailable. Please try again later."
           )

       # 2. Check daily global limit
       await check_daily_limit(redis_client, max_daily=1000)

       # 3. Check session-based rate limit
       if not await session_limiter.check_limit(chat_request.session_id):
           raise HTTPException(
               429,
               "You've reached your message limit. Please wait or start a new session."
           )

       # 4. Check budget before API call
       await cost_monitor.check_budget()

       # 5. Process request (validation happens automatically via Pydantic)
       intents = classify_intent(chat_request.message)
       context = context_loader.load_context(intents)
       history = await history_manager.get_history(chat_request.session_id)

       # 6. Call LLM (protected by all above checks)
       response, token_usage = await get_llm_response(
           context, history, chat_request.message
       )

       # 7. Log usage and cost
       cost = await cost_monitor.log_usage(token_usage)

       # 8. Update history
       await history_manager.add_message(
           chat_request.session_id, "user", chat_request.message
       )
       await history_manager.add_message(
           chat_request.session_id, "assistant", response
       )

       return ChatResponse(
           session_id=chat_request.session_id,
           response=response,
           tokens_used=token_usage.get('total', 0),
           cost_usd=round(cost, 6)
       )
   ```

6. **Add Metrics Endpoint** (optional but recommended):
   ```python
   @router.get("/metrics")
   async def get_metrics(redis_client = Depends(get_redis)):
       """Get usage statistics"""
       from datetime import datetime
       today = datetime.now().strftime("%Y-%m-%d")

       daily_requests = await redis_client.get(f"daily_requests:{today}")
       daily_cost = await redis_client.hget(f"daily_cost:{today}", "total")

       return {
           "date": today,
           "total_requests": int(daily_requests) if daily_requests else 0,
           "total_cost_usd": int(daily_cost) / 1_000_000 if daily_cost else 0,
           "chatbot_status": "disabled" if await redis_client.get("chatbot_disabled") else "active"
       }
   ```

7. **Client-Side Rate Limiting** (frontend update):
   Update your React chatbot component:
   ```javascript
   const [messageCount, setMessageCount] = useState(0);
   const [cooldown, setCooldown] = useState(false);
   const MAX_MESSAGES = 20;

   const handleSend = async () => {
       // Check message count
       if (messageCount >= MAX_MESSAGES) {
           setMessages(prev => [...prev, {
               type: 'bot',
               text: "You've reached the message limit for this session. Please refresh to start a new conversation."
           }]);
           return;
       }

       // Check cooldown
       if (cooldown) {
           return; // Silently prevent spam
       }

       // Send message
       setCooldown(true);
       setMessageCount(prev => prev + 1);

       try {
           // ... send to API
       } catch (error) {
           if (error.response?.status === 429) {
               setMessages(prev => [...prev, {
                   type: 'bot',
                   text: "Please slow down! Wait a moment before sending another message."
               }]);
           }
       } finally {
           setTimeout(() => setCooldown(false), 3000); // 3 second cooldown
       }
   };
   ```

**Deliverables:**
- Multi-layer rate limiting (IP + session + global)
- Input validation and spam prevention
- Cost monitoring and budget protection
- Client-side rate limiting
- Metrics endpoint for monitoring

**Protection Summary:**
```
Layer 1: Client-side (3s cooldown, 20 msg limit)
Layer 2: IP-based (10/min, 50/hour)
Layer 3: Session-based (20 messages per session)
Layer 4: Daily global (1000 requests/day)
Layer 5: Cost budget ($5/day hard limit)
Layer 6: Input validation (spam detection)
```

---

### Phase 11: Deployment & Monitoring (1 hour)
**Tasks:**
1. **Railway Setup:**
   - Create Railway project
   - Connect GitHub repository
   - Add Redis add-on (one-click)
   - Configure environment variables

2. **Add PostgreSQL add-on** to Railway project

3. **Environment Variables:**
   ```
   # LLM API
   ANTHROPIC_API_KEY=sk-ant-...

   # Database
   DATABASE_URL=${DATABASE_URL}  # Auto-provided by Railway PostgreSQL
   REDIS_URL=${REDIS_URL}        # Auto-provided by Railway Redis

   # Security
   ALLOWED_ORIGINS=http://localhost:5173,https://your-portfolio.vercel.app

   # Rate Limiting
   MAX_DAILY_REQUESTS=1000
   MAX_DAILY_COST_USD=5.0
   MAX_SESSION_MESSAGES=20

   # Application
   PORT=8000
   LOG_LEVEL=INFO
   ```

3. **Deployment Files:**
   - `Procfile`: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - `runtime.txt`: `python-3.11`

4. **Update requirements.txt:**
   ```
   # Web Framework
   fastapi==0.109.0
   uvicorn[standard]==0.27.0

   # LLM
   anthropic==0.18.0

   # Databases
   redis==5.0.1                # Cache/sessions
   sqlalchemy==2.0.25          # ORM
   asyncpg==0.29.0             # Async PostgreSQL driver
   alembic==1.13.1             # Database migrations

   # Core
   python-dotenv==1.0.0
   pydantic==2.5.0
   pydantic-settings==2.1.0

   # Security
   slowapi==0.1.9              # Rate limiting
   ```

5. **Run Database Migrations on Railway:**
   Railway automatically runs migrations if you add this to `Procfile`:
   ```
   release: alembic upgrade head
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

5. **Logging:**
   - Add structured logging for:
     - Request/response times
     - Token usage per request
     - Cost per request
     - Rate limit violations
     - Intent classification results
     - Cache hit/miss (from Claude API response)
     - Errors and exceptions

6. **Set Up Anthropic Billing Alerts:**
   - Go to Anthropic Console
   - Set alert at $5 spent
   - Set hard limit at $10/month

**Deliverables:**
- Production deployment on Railway
- Environment configured
- Security layers enabled
- Logging in place
- Budget alerts configured
- API URL to connect frontend

---

## API Documentation

### Endpoints

#### 1. Chat Endpoint
```
POST /api/chat
Content-Type: application/json

Request:
{
  "session_id": "string (uuid recommended)",
  "message": "string (1-500 chars)"
}

Response (200):
{
  "session_id": "string",
  "response": "string",
  "tokens_used": 1250
}

Response (400): Validation error
Response (500): Server error
```

#### 2. New Session
```
POST /api/chat/new-session

Response (200):
{
  "session_id": "uuid-generated-id"
}
```

#### 3. Clear Session
```
DELETE /api/chat/session/{session_id}

Response (200):
{
  "message": "Session cleared"
}
```

#### 4. Health Check
```
GET /health

Response (200):
{
  "status": "healthy",
  "redis": "connected",
  "timestamp": "2025-10-09T10:30:00Z"
}
```

---

## Cost Estimates

### Anthropic Claude 3.5 Haiku Pricing:
- **Input:** $0.80 per 1M tokens
- **Output:** $4.00 per 1M tokens
- **Cache writes:** $1.00 per 1M tokens
- **Cache reads:** $0.08 per 1M tokens (90% savings!)

### Per Conversation (5 messages):
**First message:**
- Input (context + message): 400 tokens × $0.80/1M = $0.00032
- Cache write: 400 tokens × $1.00/1M = $0.00040
- Output: 150 tokens × $4.00/1M = $0.00060
- **Total: $0.00132**

**Subsequent messages (cache hit):**
- Cache read: 400 tokens × $0.08/1M = $0.00003
- Input (message): 20 tokens × $0.80/1M = $0.00002
- Output: 150 tokens × $4.00/1M = $0.00060
- **Total: $0.00065**

**5-message conversation: $0.00132 + (4 × $0.00065) = $0.00392**

### Railway Costs:
- Free tier: $5/month credit
- Typical usage (small app): $3-5/month
- Redis add-on: Included in free tier initially

### Monthly Estimate:
- 500 conversations (2,500 messages): ~$2.00
- Railway: ~$3-5 (after free credit)
- **Total: ~$5-7/month**

---

## Environment Variables

```env
# Required - LLM API
ANTHROPIC_API_KEY=sk-ant-api03-...

# Required - Databases
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
REDIS_URL=redis://default:password@redis-host:6379

# Application
PORT=8000
LOG_LEVEL=INFO

# Security & CORS
ALLOWED_ORIGINS=http://localhost:5173,https://your-portfolio.com

# Rate Limiting
MAX_DAILY_REQUESTS=1000
MAX_DAILY_COST_USD=5.0
MAX_SESSION_MESSAGES=20

# Session Management
MAX_HISTORY_LENGTH=10
SESSION_TIMEOUT=1800
```

---

## Risk Mitigation - UPDATED

### Potential Issues & Solutions:
1. **LLM API downtime**
   - ✅ Cache responses, show fallback message
   - ✅ Handle API errors gracefully

2. **Redis connection loss**
   - ✅ Degrade gracefully, use in-memory fallback
   - Add connection retry logic

3. **High costs / Abuse**
   - ✅ SOLVED: Multi-layer rate limiting
   - ✅ SOLVED: Cost monitoring with $5 daily limit
   - ✅ SOLVED: Auto-disable chatbot if budget exceeded
   - ✅ SOLVED: Input validation blocks spam

4. **Slow responses**
   - ✅ Add timeout to LLM calls
   - ✅ Optimize context size (smart loading)
   - Use faster Claude Haiku model

5. **Inaccurate answers**
   - Improve context files quality
   - Add disclaimers in system prompt
   - Monitor and iterate based on feedback

6. **Spam/Malicious Users**
   - ✅ SOLVED: 6-layer protection (client + IP + session + daily + budget + validation)
   - ✅ SOLVED: 3-second cooldown
   - ✅ SOLVED: Max 20 messages per session
   - Block repeat offenders (future: IP blacklist)

---

## Security Summary 🔒

**Your chatbot is now protected against:**
- ✅ Cost overruns (hard $5/day limit)
- ✅ Spam flooding (rate limiting)
- ✅ Malicious input (validation)
- ✅ API abuse (multi-layer limits)
- ✅ Budget exhaustion (auto-disable)

**Maximum possible cost per day:** $5 (enforced)
**Maximum possible cost per month:** ~$150 (but realistically ~$2-5)

With these protections, **it's completely safe to deploy publicly!**

---

## Future Enhancements

### Phase 11+ (Optional):
1. **Advanced Intent Classification**
   - Use small LLM for better accuracy
   - Handle complex multi-intent queries

2. **Enhanced Rate Limiting**
   - IP blacklist for repeat offenders
   - Whitelist for trusted IPs

3. **Analytics Dashboard**
   - Track popular questions
   - Monitor costs in real-time
   - User engagement metrics

4. **Streaming Responses**
   - Real-time token streaming for better UX
   - Use Server-Sent Events (SSE)

5. **Feedback System**
   - Thumbs up/down on responses
   - Store feedback for improvement

6. **Multi-language Support**
   - Detect input language
   - Respond in user's language

7. **Voice Integration**
   - Speech-to-text input
   - Text-to-speech output

8. **Context Updates**
   - Admin API to update contexts
   - Automatic cache invalidation

---

## Testing Strategy

### Unit Tests:
```python
# test_intent.py
def test_skills_intent():
    result = classify_intent("What are your skills?")
    assert "skills" in result

# test_context.py
def test_load_skills_context():
    context = context_loader.load_context(["skills"])
    assert "Python" in context
```

### Integration Tests:
```python
# test_api.py
async def test_chat_endpoint():
    response = await client.post("/api/chat", json={
        "session_id": "test-123",
        "message": "What programming languages do you know?"
    })
    assert response.status_code == 200
    assert "Python" in response.json()["response"]
```

### Manual Testing Checklist:
- [ ] Basic questions across all topics
- [ ] Conversation continuity (follow-up questions)
- [ ] Edge cases (empty messages, invalid session)
- [ ] Performance (response time < 3 seconds)
- [ ] Cost tracking (verify token counts)

---

## Success Metrics

1. **Response Quality:** Accurate, relevant answers based on context
2. **Response Time:** < 3 seconds per message (95th percentile)
3. **Cost Efficiency:** < $10/month for expected traffic
4. **Cache Hit Rate:** > 70% (after first message in conversation)
5. **User Engagement:** Average 3-5 messages per session
6. **Uptime:** > 99% availability

---

## Timeline Estimate

- **Phase 1 (Setup):** 30 minutes
- **Phase 2 (Database Setup):** 1 hour 🆕
- **Phase 3 (Context Files):** 1 hour
- **Phase 4 (Intent):** 1 hour
- **Phase 5 (Context Loader):** 30 minutes
- **Phase 6 (History):** 1 hour
- **Phase 7 (LLM):** 2 hours
- **Phase 8 (API + DB Integration):** 1.5 hours
- **Phase 9 (Testing):** 1-2 hours
- **Phase 10 (Security & Rate Limiting):** 1.5 hours 🔒
- **Phase 11 (Deployment):** 1 hour

**Total:** ~12-13 hours for full implementation (with PostgreSQL)

---

## Risk Mitigation

### Potential Issues:
1. **LLM API downtime** → Cache responses, show fallback message
2. **Redis connection loss** → Degrade gracefully, use in-memory fallback
3. **High costs** → Set up billing alerts, implement rate limiting
4. **Slow responses** → Add timeout, optimize context size
5. **Inaccurate answers** → Improve context files, add disclaimers

---

## Next Steps

1. ✅ Review and approve this plan
2. Choose LLM provider: **Anthropic Claude** (with caching)
3. Get API key from Anthropic
4. Create Railway account
5. Start Phase 1: FastAPI project setup

---

## Questions to Resolve Before Starting

1. ✅ **Tech stack confirmed:** Python + FastAPI + Claude + Redis + Railway
2. **Python version:** 3.11 or 3.12?
3. **Do you have portfolio info ready** for context files or should I help compile it?
4. **Any specific chatbot personality/tone** preferences?
5. **Rate limiting needed** from day 1 or add later?

---

---

## Production Readiness Checklist

Before deploying to production, ensure:

**Security & Protection:**
- [ ] Rate limiting implemented (IP + session + global)
- [ ] Input validation with spam detection
- [ ] Cost monitoring with budget limits
- [ ] Client-side rate limiting (3s cooldown)
- [ ] Environment variables properly set
- [ ] CORS configured for your domain only

**Monitoring:**
- [ ] Logging configured for all endpoints
- [ ] Anthropic billing alerts set ($5 warning)
- [ ] Metrics endpoint accessible
- [ ] Error tracking in place

**Testing:**
- [ ] All endpoints tested
- [ ] Rate limits verified
- [ ] Cost calculations accurate
- [ ] Spam detection working
- [ ] LLM responses quality checked

**Deployment:**
- [ ] Railway project created
- [ ] Redis add-on configured
- [ ] GitHub auto-deploy enabled
- [ ] Environment variables set
- [ ] Frontend updated with API URL

---

**Document Version:** 4.0 (Added PostgreSQL Database)
**Last Updated:** 2025-10-09
**Stack:** Python + FastAPI + PostgreSQL + Redis + Anthropic Claude + Railway
**Security:** ✅ Production-ready with 6-layer protection
**Database:** ✅ PostgreSQL for persistent storage + Redis for caching

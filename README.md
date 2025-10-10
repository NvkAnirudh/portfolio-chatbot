# Portfolio Chatbot Backend

AI-powered chatbot backend for Anirudh Nuti's portfolio website, built with FastAPI and Anthropic Claude.

## Features

- 🤖 AI-powered responses using Claude 3.5 Haiku
- 💾 PostgreSQL for persistent message storage
- ⚡ Redis for caching and session management
- 🔒 Multi-layer security and rate limiting
- 💰 Cost monitoring and budget controls
- 📊 Analytics and conversation tracking

## Tech Stack

- **Framework**: FastAPI 0.115.0
- **LLM**: Anthropic Claude 3.5 Haiku
- **Database**: PostgreSQL (via asyncpg)
- **Cache**: Redis
- **ORM**: SQLAlchemy 2.0
- **Deployment**: Railway

## Project Structure

```
chatbot-backend/
├── app/
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   ├── models/          # Pydantic schemas & DB models
│   ├── db/              # Database session & repository
│   ├── utils/           # Utilities (logger, etc.)
│   ├── main.py          # FastAPI app entry point
│   └── config.py        # Configuration management
├── context/             # Portfolio context files (.txt)
├── alembic/             # Database migrations
├── tests/               # Unit & integration tests
├── docs/                # Development documentation
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables

```

## Setup

### 1. Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Anthropic API Key

### 2. Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Update the following variables:
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

### 4. Database Setup

```bash
# Run migrations
alembic upgrade head
```

### 5. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`

## API Endpoints

### Chat Endpoints
- `POST /api/chat` - Send a chat message and get AI response
- `GET /api/session/{session_id}/history` - Get conversation history for a session
- `DELETE /api/session/{session_id}` - Clear conversation history
- `GET /api/sessions/stats` - Get statistics about active sessions

### Monitoring Endpoints
- `GET /` - Root endpoint with API info
- `GET /health` - Basic health check (for Railway)
- `GET /health/detailed` - Comprehensive health check (DB, Redis, LLM)
- `GET /metrics` - Application metrics (sessions, costs, tokens)
- `GET /api/budget/status` - Cost budget status and utilization

### Example Requests

**Chat with the AI:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your Python skills?"}'
```

**Check budget status:**
```bash
curl http://localhost:8000/api/budget/status
```

**Get detailed health:**
```bash
curl http://localhost:8000/health/detailed
```

## Development Phases

- [x] **Phase 1**: Setup & Foundation
- [x] **Phase 2**: Database Setup & Models
- [x] **Phase 3**: Portfolio Context Files
- [x] **Phase 4**: Intent Classification
- [x] **Phase 5**: Context Loader
- [x] **Phase 6**: Conversation History Manager
- [x] **Phase 7**: LLM Service Integration
- [x] **Phase 8**: API Endpoints
- [x] **Phase 9**: Integration & Testing
- [x] **Phase 10**: Security & Rate Limiting
- [x] **Phase 11**: Deployment & Monitoring

---

## Phase Implementation Details

### Phase 1: Setup & Foundation ✅
**Completed**: Basic FastAPI app, configuration, dependencies, project structure

**Files Created:**
- `app/main.py` - FastAPI application with CORS, health endpoints
- `app/config.py` - Pydantic settings for environment variables
- `app/utils/logger.py` - Logging configuration
- `requirements.txt` - All dependencies
- `.env.example`, `.gitignore`, `Procfile`, `runtime.txt`

**Key Features:**
- FastAPI 0.115.0 with uvicorn
- Environment-based configuration
- CORS middleware
- Health check endpoints

### Phase 2: Database Setup & Models ✅
**Completed**: PostgreSQL models, repositories, Alembic migrations

**Files Created:**
- `app/models/db_models.py` - SQLAlchemy models (Session, Message, Feedback, CostTracking)
- `app/models/schemas.py` - Pydantic request/response schemas
- `app/db/session.py` - Async database session management
- `app/db/repository.py` - Repository layer (SessionRepository, MessageRepository, FeedbackRepository, CostTrackingRepository)
- `alembic/versions/001_initial_migration.py` - Initial database schema

**Database Schema:**
```
sessions (id, created_at, updated_at, ip_address, user_agent, is_active)
  └─> messages (id, session_id, role, content, intent, tokens_used, cost_usd, created_at)
  └─> feedback (id, session_id, message_id, rating, comment, created_at)

cost_tracking (id, date, total_requests, total_tokens, total_cost_usd, cache_reads, cache_writes)
```

**Key Features:**
- Async SQLAlchemy with asyncpg
- Repository pattern for clean data access
- Foreign keys with cascade delete
- Indexes on session_id, created_at, date
- Daily cost tracking for budget monitoring
- Alembic migrations for schema versioning

**Database Setup:**
```bash
# Option 1: Docker
docker run -d --name chatbot-postgres \
  -e POSTGRES_USER=chatbot_user \
  -e POSTGRES_PASSWORD=chatbot_password \
  -e POSTGRES_DB=chatbot_db \
  -p 5432:5432 postgres:15-alpine

# Option 2: Local PostgreSQL
createdb chatbot_db

# Update .env
DATABASE_URL=postgresql+asyncpg://chatbot_user:chatbot_password@localhost:5432/chatbot_db

# Run migrations
alembic upgrade head
```

### Phase 3: Portfolio Context Files ✅
**Completed**: Created comprehensive context files with real portfolio information

**Files Created:**
- `context/general.txt` (27 lines) - Name, role, contact info, general description
- `context/skills.txt` (77 lines) - Technical skills across data engineering, AI/ML, cloud, and full-stack
- `context/experience.txt` (107 lines) - Complete work history from 6 companies with achievements
- `context/projects.txt` (94 lines) - 3 detailed projects with features and links
- `context/education.txt` (82 lines) - Master's and Bachelor's degrees with coursework

**Content Overview:**
```
Education: MS Applied Data Analytics (Boston University), BTech CS (GITAM)
Experience: 6 positions including Founding Engineer, Data Engineer, Data Scientist
Projects: LinkedIn Post Generator (MCP), Real-Time E-Commerce Analytics, DEtermined Platform
Skills: Python, R, SQL, PySpark, Kafka, Airflow, dbt, AWS, GenAI, LLMs, FastAPI, React
```

**Key Features:**
- Comprehensive coverage of all portfolio aspects
- Specific achievements with measurable impact ($250K+ savings, 5x performance improvements)
- Technologies organized by category (Data Engineering, Cloud, AI/ML, Full-Stack)
- Project details with links to GitHub, demos, and live platforms
- Graduate coursework and teaching experience highlighted
- Ready for LLM context injection (387 total lines, ~2500 tokens)

### Phase 4: Intent Classification ✅
**Completed**: Keyword-based intent classifier with comprehensive testing

**Files Created:**
- `app/services/intent_classifier.py` (181 lines) - Intent classification service
- `tests/test_intent_classifier.py` (189 lines) - Comprehensive unit tests
- `tests/__init__.py` - Test suite initialization
- `pytest.ini` - Pytest configuration

**Intent Categories:**
- **greeting**: Hello, hi, hey
- **skills**: Technical skills, tech stack, programming languages
- **experience**: Work history, jobs, companies, achievements
- **projects**: Portfolio projects, GitHub, demos
- **education**: Degrees, university, courses
- **contact**: How to reach, email, hiring, availability
- **general**: General questions (fallback)

**Key Features:**
- Zero API cost - pure keyword matching
- Multi-intent detection (up to 3 intents per message)
- Case-insensitive pattern matching
- Smart context file mapping based on intents
- Primary intent extraction for simple workflows
- Handles empty/whitespace-only messages gracefully

**Test Coverage:**
- 16 unit tests, all passing ✅
- 95% code coverage for intent_classifier.py
- Tests for all intent categories
- Edge cases (empty messages, case sensitivity, multiple intents)
- Context file mapping validation

**How It Works:**
```python
from app.services.intent_classifier import intent_classifier

# Classify a message
intents = intent_classifier.classify("What are your Python skills?")
# Returns: ["skills", "general"]

# Get context files to load
files = intent_classifier.map_intent_to_context_files(intents)
# Returns: ["skills", "general"]
```

**Dependencies Added:**
- pytest==8.3.4
- pytest-asyncio==0.24.0
- pytest-cov==6.0.0

### Phase 5: Context Loader ✅
**Completed**: Service for loading and formatting portfolio context files based on intents

**Files Created:**
- `app/services/context_loader.py` (242 lines) - Context loading service with caching
- `tests/test_context_loader.py` (230 lines) - Comprehensive unit tests
- `context/contact.txt` (98 lines) - Dedicated contact information file

**Key Features:**
- Loads `.txt` files from `context/` directory based on detected intents
- In-memory caching with 15-minute TTL for frequently accessed contexts
- Formats multiple context files for LLM consumption with clear section headers
- Main method: `get_context_for_intents(intents)` - one-stop solution for chatbot workflow
- Graceful handling of missing files and cache expiration
- Cache statistics and management utilities

**How It Works:**
```python
from app.services.context_loader import context_loader

# Load context based on intents
intents = ["skills", "experience"]
context = context_loader.get_context_for_intents(intents)

# Returns formatted string:
# === SKILLS ===
# [content from skills.txt]
#
# === EXPERIENCE ===
# [content from experience.txt]
#
# === GENERAL ===
# [content from general.txt]
```

**Intent to Context File Mapping:**
- `greeting` → general.txt
- `skills` → skills.txt + general.txt
- `experience` → experience.txt + general.txt
- `projects` → projects.txt + general.txt
- `education` → education.txt + general.txt
- `contact` → contact.txt + general.txt
- `general` → general.txt

**Test Coverage:**
- 23 unit tests, all passing ✅
- 95% code coverage for context_loader.py
- Tests for all context files (general, skills, experience, projects, education, contact)
- Cache functionality, expiration, and statistics
- Multiple intent handling and formatting
- Edge cases (nonexistent files, empty contexts)

**Context Files (6 total):**
1. `general.txt` (68 lines) - Overview, summary, measurable impact
2. `skills.txt` (77 lines) - Technical skills by category
3. `experience.txt` (107 lines) - 6 companies with achievements
4. `projects.txt` (94 lines) - 3 projects with demos
5. `education.txt` (82 lines) - MS + BTech degrees
6. `contact.txt` (98 lines) - Contact info, availability, preferences

**Performance:**
- First load: Reads from disk
- Subsequent loads (within 15 min): Served from cache
- Average context size: 2,000-5,000 characters depending on intent
- Supports loading multiple contexts in parallel

### Phase 6: Conversation History Manager ✅
**Completed**: Redis-backed conversation history management with in-memory fallback

**Files Created:**
- `app/services/conversation_manager.py` (314 lines) - Conversation history service
- `tests/test_conversation_manager.py` (254 lines) - Comprehensive unit tests

**Key Features:**
- Redis-based storage for conversation history (with automatic fallback to in-memory)
- Configurable history length (default: 10 recent messages)
- Session-based conversation tracking with TTL (default: 24 hours)
- Message metadata support (intents, tokens, timestamps)
- Automatic history trimming to maintain performance
- Format conversation for LLM API consumption
- Session management utilities (clear, exists, stats)

**How It Works:**
```python
from app.services.conversation_manager import conversation_manager

# Add messages to a session
conversation_manager.add_message(
    session_id="user-123",
    role="user",
    content="What are your Python skills?",
    metadata={"intent": ["skills", "general"], "tokens": 25}
)

conversation_manager.add_message(
    session_id="user-123",
    role="assistant",
    content="I have advanced Python expertise...",
    metadata={"tokens": 150}
)

# Get history for LLM context
llm_history = conversation_manager.format_history_for_llm("user-123")
# Returns: [
#   {"role": "user", "content": "What are your Python skills?"},
#   {"role": "assistant", "content": "I have advanced Python expertise..."}
# ]

# Get context summary
summary = conversation_manager.get_context_summary("user-123")
# Returns: {
#   "total_messages": 2,
#   "user_messages": 1,
#   "assistant_messages": 1,
#   "unique_intents": ["skills", "general"]
# }
```

**Storage Architecture:**
- **Primary**: Redis with session-based keys (`chat:session:{id}:history`)
- **Fallback**: In-memory dictionary when Redis unavailable
- **TTL**: 24 hours (configurable via `SESSION_TTL_HOURS`)
- **History Length**: Last 10 messages (configurable via `CONVERSATION_HISTORY_LENGTH`)

**Test Coverage:**
- 18 unit tests, all passing ✅
- 75% code coverage for conversation_manager.py
- Tests for both Redis and in-memory modes
- Message addition, retrieval, and formatting
- History limiting and trimming
- Session management (clear, exists, stats)
- Multiple concurrent sessions
- Edge cases (invalid roles, empty sessions)

**Data Structure:**
Each message stored with:
```json
{
  "role": "user" | "assistant",
  "content": "message text",
  "timestamp": "2025-10-10T12:34:56.789Z",
  "metadata": {
    "intent": ["skills"],
    "tokens": 25,
    "cost_usd": 0.0001
  }
}
```

**Session Management:**
- Auto-expiration after 24 hours of inactivity
- Automatic trimming to last N messages
- Support for clearing individual sessions
- Global session statistics

**Graceful Degradation:**
- If Redis unavailable → automatic fallback to in-memory storage
- Logs warnings but continues operation
- No service interruption

### Phase 7: LLM Service Integration ✅
**Completed**: Anthropic Claude API integration with prompt caching and cost tracking

### Phase 8: API Endpoints ✅
**Completed**: FastAPI endpoints for chat, session management, and monitoring

**Files Created:**
- `app/routes/chat.py` - Complete chat API with all endpoints
- `test_api.py` - API integration tests

**Endpoints:**
- `POST /api/chat` - Main chat endpoint
- `GET /api/session/{session_id}/history` - Get conversation history
- `DELETE /api/session/{session_id}` - Clear session
- `GET /api/sessions/stats` - Session statistics
- `GET /api/budget/status` - Budget monitoring

**Features:**
- Orchestrates all services (intent, context, conversation, LLM)
- PostgreSQL message persistence
- Redis session management
- Cost tracking and budget enforcement
- Session ID generation and validation

### Phase 9: Integration & Testing ✅
**Completed**: Full integration with PostgreSQL persistence and comprehensive testing

**Key Changes:**
- Added PostgreSQL persistence to chat endpoints
- Fixed repository method calls (static methods)
- Integrated database session management
- Tested end-to-end chat flow
- Verified dual storage (Redis + PostgreSQL)

**Testing:**
- Started PostgreSQL via Docker
- Ran Alembic migrations
- Verified message persistence
- Tested greeting responses (0 tokens)
- Tested complex queries (2,385 tokens)

### Phase 10: Security & Rate Limiting ✅
**Completed**: Multi-layer security, rate limiting, and cost controls

**Files Created:**
- `app/middleware/rate_limiter.py` - Rate limiting middleware (10 req/min)
- `app/middleware/security.py` - Security headers and input validation
- `app/middleware/cost_control.py` - Daily budget enforcement
- `test_security.py` - Security feature tests

**Security Features:**
- Security headers (X-Content-Type-Options, X-Frame-Options, CSP)
- Input sanitization (XSS protection, length validation)
- Session ID validation (UUID v4 format)
- Rate limiting (10 requests/minute per IP)
- Cost budget controls ($5/day, 1000 requests/day)
- CORS protection
- SQL injection protection (parameterized queries)

**Middleware Stack:**
1. Security Headers (all responses)
2. Rate Limiting (IP-based)
3. Cost Control (budget enforcement)
4. CORS (configurable origins)

### Phase 11: Deployment & Monitoring ✅
**Completed**: Railway deployment configuration and comprehensive monitoring

**Files Created:**
- `railway.json` - Railway deployment configuration
- `.env.production.example` - Production environment template
- `docs/DEPLOYMENT.md` - Complete deployment guide (550+ lines)
- Enhanced health check endpoints
- Application metrics endpoint

**Monitoring Endpoints:**
- `/health` - Basic health (for Railway load balancer)
- `/health/detailed` - Comprehensive health check
  - Database connectivity
  - Redis connectivity
  - LLM configuration
  - System information
- `/metrics` - Application metrics
  - Active sessions
  - Total messages
  - Cost tracking
  - Budget utilization
  - Token usage
  - Configuration details

**Deployment Features:**
- Railway.json with healthcheck configuration
- Automatic migration on deployment
- Environment variable templates
- Database backup instructions
- Troubleshooting guide
- Production security checklist
- Cost optimization guide

**Ready for Production:**
- ✅ All phases complete
- ✅ Comprehensive documentation
- ✅ Security hardened
- ✅ Monitoring enabled
- ✅ Cost controls active
- ✅ Railway deployment ready

---

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Deployment

### Railway Deployment

1. **Add Services:**
   - PostgreSQL (auto-configured)
   - Redis (auto-configured)

2. **Environment Variables:**
   ```
   ANTHROPIC_API_KEY=your_key_here
   # DATABASE_URL and REDIS_URL auto-set by Railway
   ```

3. **Deploy:**
   - Railway will run migrations via Procfile
   - Application starts on dynamic PORT

See `docs/DEV_PLAN.md` for complete deployment instructions.

## License

Private - Portfolio Project

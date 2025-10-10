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

- `GET /` - Root endpoint with API info
- `GET /health` - Health check endpoint
- `POST /api/chat` - Send chat message (Coming soon)
- `GET /api/analytics` - Get conversation analytics (Coming soon)

## Development Phases

- [x] **Phase 1**: Setup & Foundation
- [x] **Phase 2**: Database Setup & Models
- [ ] **Phase 3**: Portfolio Context Files
- [ ] **Phase 4**: Intent Classification
- [ ] **Phase 5**: Context Loader
- [ ] **Phase 6**: Conversation History Manager
- [ ] **Phase 7**: LLM Service Integration
- [ ] **Phase 8**: API Endpoints
- [ ] **Phase 9**: Integration & Testing
- [ ] **Phase 10**: Security & Rate Limiting
- [ ] **Phase 11**: Deployment & Monitoring

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

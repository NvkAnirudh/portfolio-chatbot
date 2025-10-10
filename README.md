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
- [ ] **Phase 2**: Database Setup & Models
- [ ] **Phase 3**: Portfolio Context Files
- [ ] **Phase 4**: Intent Classification
- [ ] **Phase 5**: Context Loader
- [ ] **Phase 6**: Conversation History Manager
- [ ] **Phase 7**: LLM Service Integration
- [ ] **Phase 8**: API Endpoints
- [ ] **Phase 9**: Integration & Testing
- [ ] **Phase 10**: Security & Rate Limiting
- [ ] **Phase 11**: Deployment & Monitoring

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Deployment

The application is configured for deployment on Railway. See `docs/DEV_PLAN.md` for detailed deployment instructions.

## License

Private - Portfolio Project

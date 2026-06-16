# Plum Claims Processing System

AI-powered health insurance claims adjudication platform. Processes OPD (Outpatient Department) claims through a multi-agent pipeline with full explainability.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.13, FastAPI, SQLAlchemy (async), Celery |
| **Frontend** | Next.js 15, React 19, TypeScript, TailwindCSS |
| **Database** | PostgreSQL 17 |
| **Cache** | Redis 7 |
| **LLM** | Google Gemini (default), OpenAI, Anthropic (configurable) |
| **Observability** | OpenTelemetry, Jaeger, Prometheus, Grafana |

## Architecture

```
┌──────────────┐     ┌──────────────────────────────────────────────────┐
│   Frontend   │────▶│  FastAPI Backend                                  │
│  (Next.js)   │     │  ┌─────────────────────────────────────────────┐ │
│  :3000       │     │  │  Orchestrator (5-step pipeline)             │ │
└──────────────┘     │  │  ┌───────────┐ ┌───────────┐ ┌──────────┐ │ │
                     │  │  │Verifier   │▶│Extractor  │▶│Policy    │ │ │
                     │  │  └───────────┘ └───────────┘ └──────────┘ │ │
                     │  │       ▲                            │       │ │
                     │  │       │            ┌──────────┐    ▼       │ │
                     │  │       └────────────│Fraud     │◀───┘       │ │
                     │  │                    └──────────┘             │ │
                     │  │                         │                   │ │
                     │  │                    ┌────▼─────┐             │ │
                     │  │                    │ Decision  │             │ │
                     │  │                    └──────────┘             │ │
                     │  └─────────────────────────────────────────────┘ │
                     │                                                  │
                     │  ┌──────┐ ┌───────┐ ┌────────┐ ┌─────────────┐ │
                     │  │ DB   │ │ Redis │ │ Celery │ │ LLM Provider│ │
                     │  └──────┘ └───────┘ └────────┘ └─────────────┘ │
                     └──────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL 17
- Redis 7
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### 1. Clone and Install

```bash
# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Set Up Environment

```bash
# Copy the example env file
cp backend/.env.example backend/.env

# Edit backend/.env with your settings:
# - Set LLM_PROVIDER (google/openai/anthropic/mock)
# - Add your API key (GEMINI_API_KEY, OPENAI_API_KEY, etc.)
# - Configure DATABASE_URL for your PostgreSQL instance
# - Configure REDIS_URL for your Redis instance
```

### 3. Set Up Database

```bash
# Start PostgreSQL and Redis (if running locally)
# Then run migrations:
uv run alembic -c backend/alembic.ini upgrade head

# Seed the database with test data:
uv run python scripts/seed_data.py
```

### 4. Start the Application

**Option A: Using Docker Compose (recommended)**

```bash
# Start all services (backend, frontend, db, redis, jaeger, prometheus, grafana)
docker compose up -d

# Seed the database after services are up
docker compose exec app uv run python scripts/seed_data.py
```

**Option B: Running locally**

```bash
# Terminal 1: Start the backend
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start the frontend
cd frontend && npm run dev

# Terminal 3: Start the Celery worker (optional, runs embedded in dev mode)
uv run celery -A backend.core.celery_app worker -Q claims -l info
```

### 5. Access the Application

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3052 | — |
| **Backend API** | http://localhost:3051 | — |
| **API Docs** | http://localhost:3051/docs | — |
| **Jaeger** (tracing) | http://localhost:3059 | — |
| **Prometheus** (metrics) | http://localhost:3062 | — |
| **Grafana** (dashboards) | http://localhost:3063 | admin / admin |

### Demo Credentials

| Role | Member ID | Password |
|------|-----------|----------|
| Member | EMP001 | pass001 |
| Member | EMP002 | pass002 |
| Admin | ADMIN001 | admin123 |

## Usage

### Submit a Claim

1. Log in at http://localhost:3052/login
2. Fill in claim details (member ID, category, amount, date)
3. Upload supporting documents (prescriptions, bills, reports)
4. Submit and wait for AI-powered adjudication
5. View the decision with full reasoning trace

### Claim Categories

| Category | Type | Definition |
|----------|------|------------|
| CONSULTATION | Doctor visits | General practitioner or specialist consultation |
| DIAGNOSTIC | Lab tests & imaging | Blood tests, X-rays, MRI, CT scans |
| PHARMACY | Medications | Prescription drugs and medicines |
| DENTAL | Dental procedures | Checkups, cleaning, basic procedures |
| VISION | Eye care | Eye exams, glasses, contact lenses |
| ALTERNATIVE_MEDICINE | AYUSH treatments | Ayurveda, Yoga, Unani, Siddha, Homeopathy |

### Claim Decisions

| Decision | Meaning |
|----------|---------|
| **APPROVED** | Full amount approved (minus co-pay) |
| **PARTIAL** | Partially approved (some items excluded) |
| **REJECTED** | Claim rejected (with specific reason) |
| **MANUAL_REVIEW** | Requires human review |

## Makefile Commands

```bash
make help              # Show all available commands
make install           # Install production dependencies
make dev-install       # Install dev dependencies
make run               # Start backend with hot reload
make frontend-dev      # Start frontend dev server
make test              # Run backend tests
make test-cov          # Run tests with coverage report
make lint              # Run linter (ruff)
make format            # Format code
make seed              # Seed database with test data
make eval              # Run evaluation against test cases
make clean             # Remove build artifacts
```

## Testing

### Backend Unit Tests

```bash
# Run all tests
uv run pytest backend/tests/ -v

# Run with coverage
uv run pytest backend/tests/ -v --cov=backend --cov-report=term

# Run a specific test file
uv run pytest backend/tests/test_policy_service.py -v

# Run a specific test
uv run pytest backend/tests/test_claim_pipeline.py::TestClaimPipeline::test_tc004_clean_consultation_approval -v
```

### E2E Evaluation

```bash
# Run all 12 test cases against the running API
uv run python scripts/run_eval.py
```

This generates `eval_report.md` with pass/fail results and full processing traces.

## Project Structure

```
├── backend/                    # Python backend (FastAPI)
│   ├── api/                    # HTTP layer
│   │   └── v1/                 # API v1 endpoints (claims, documents, admin, auth)
│   ├── core/                   # Shared infrastructure (config, DI, logging, telemetry)
│   ├── domain/                 # Business logic
│   │   ├── claims/             # Claim lifecycle management
│   │   ├── decision/           # Decision aggregation
│   │   ├── documents/          # Document verification & extraction
│   │   ├── fraud/              # Fraud detection
│   │   ├── member/             # Member management & auth
│   │   └── policy/             # Policy rule evaluation (30+ rules)
│   ├── orchestrator/           # Multi-agent pipeline engine
│   │   └── agents/             # AI agents (verification, extraction, policy, fraud, decision)
│   ├── providers/              # External service adapters
│   │   ├── cache/              # Redis / in-memory cache
│   │   ├── db/                 # PostgreSQL (async SQLAlchemy)
│   │   ├── doc_processing/     # OCR + Vision LLM
│   │   ├── llm/                # LLM providers (OpenAI, Anthropic, Gemini, Mock)
│   │   └── storage/            # File storage (local, MinIO, S3)
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Unit & integration tests
│   └── uploads/                # Runtime file uploads (gitignored)
├── frontend/                   # Next.js 15 frontend
│   └── src/
│       ├── app/                # Pages (home, login, claims, admin)
│       ├── components/         # React components
│       │   ├── claims/         # Claim-specific components
│       │   └── ui/             # Reusable UI components
│       ├── contexts/           # React contexts (auth)
│       ├── lib/                # Utilities (API client, auth helpers)
│       └── types/              # TypeScript type definitions
├── assignment/                 # Assignment specification & test data
├── scripts/                    # Utility scripts (seed, eval, document generator)
├── docs/                       # Documentation (Mintlify)
├── documents/                  # Test document fixtures
├── infra/                      # Observability configs (Prometheus, Grafana)
├── docker-compose.yml          # Multi-service Docker stack
├── Dockerfile                  # Container build
├── Makefile                    # Build/dev commands
└── pyproject.toml              # Python project config
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `LLM_PROVIDER` | `mock` | LLM provider: `google`, `openai`, `anthropic`, `mock` |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `STORAGE_PROVIDER` | `local` | File storage: `local`, `minio`, `s3` |
| `STORAGE_PATH` | `/workspace/backend/uploads` | Local storage path |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://jaeger:4317` | OpenTelemetry collector endpoint |
| `ENABLE_TRACING` | `true` | Enable distributed tracing |
| `ENABLE_METRICS` | `true` | Enable Prometheus metrics |
| `JWT_SECRET_KEY` | — | JWT signing key |
| `APP_ENV` | `development` | Environment: `development`, `production` |

### LLM Provider Setup

**Google Gemini (recommended for development):**
```bash
LLM_PROVIDER=google
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-3.1-flash-lite
```

**OpenAI:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
```

**Anthropic:**
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

**Mock (no API key needed, for testing):**
```bash
LLM_PROVIDER=mock
```

## API Reference

### Claims

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/claims` | Submit a claim (async, returns 202) |
| `POST` | `/api/v1/claims/upload` | Submit with file uploads |
| `GET` | `/api/v1/claims` | List claims (with filters) |
| `GET` | `/api/v1/claims/{id}` | Get claim details |
| `GET` | `/api/v1/claims/{id}/trace` | Get processing trace |
| `POST` | `/api/v1/claims/{id}/retry` | Retry failed claim |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | Login (returns JWT) |
| `POST` | `/api/v1/auth/register` | Register new member |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/admin/dashboard` | Dashboard statistics |
| `GET` | `/api/v1/admin/claims` | All claims with filters |
| `POST` | `/api/v1/admin/claims/{id}/override` | Override decision |
| `POST` | `/api/v1/admin/claims/{id}/rerun` | Re-run pipeline |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check |
| `GET` | `/metrics` | Prometheus metrics |

Full API documentation available at http://localhost:3051/docs (Swagger UI).

## Known Limitations

- **Document extraction accuracy depends on document quality** — The LLM-based extraction works well on clear scans but degrades on blurry photos, handwritten notes, or low-contrast documents. The Docling integration is a stub and not yet production-ready for OCR-based extraction.

- **Fraud detection is primarily rule-based** — The AI fraud signal is supplemental but currently returns hardcoded confidence. Sophisticated fraud patterns (collusion networks, staged accidents) cannot be detected with the current rule set.

- **No multi-page PDF support** — The system processes single-page documents. Multi-page PDFs (common for hospital bills) are not yet supported.

- **SHA-256 password hashing (not bcrypt/argon2)** — Password storage uses SHA-256 with a salt, which is faster but less resistant to GPU-based brute force than bcrypt or argon2. Acceptable for the assignment scope but not production-grade.

- **Rate limiting is in-memory only** — The Redis-backed rate limiter path has dead code; in-memory rate limiting means each uvicorn worker has its own window, giving an effective limit of N x configured_limit where N is the number of workers.

- **Embedded Celery worker pattern is dev-only** — The worker service is defined in docker-compose but the dev mode defaults to embedded/sequential processing. A separate worker process is needed for production.

- **Mock provider used for eval testing** — All test evaluations run with the Mock LLM provider. Real LLM results may differ in extraction quality, confidence scores, and edge case handling.

## License

This project is a technical assignment for Plum.

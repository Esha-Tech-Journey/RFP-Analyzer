# RFP Insight & Risk Analyzer

A full-stack internal tool for evaluating incoming Request for Proposal (RFP) documents. Upload a PDF, DOCX, or TXT file (or paste text directly) and the system automatically extracts content, runs rule-based analysis, and returns a structured risk assessment, effort estimate, and go/no-go recommendation.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Database Schema](#database-schema)
5. [Backend — Layer by Layer](#backend--layer-by-layer)
   - [Configuration](#configuration)
   - [Models](#models)
   - [Parsers](#parsers)
   - [Analysis Engine](#analysis-engine)
   - [Repositories](#repositories)
   - [Services](#services)
   - [Celery Task](#celery-task)
   - [API Routers](#api-routers)
   - [Schemas](#schemas)
6. [Frontend](#frontend)
7. [Infrastructure](#infrastructure)
8. [Environment Variables](#environment-variables)
9. [Running the Project](#running-the-project)
10. [API Reference](#api-reference)

---

## Architecture Overview

```
Browser (React + Vite)
        │
        │  HTTP via Vite proxy → /api/*
        ▼
  FastAPI (Uvicorn)          ← port 8001 (host) → 8000 (container)
        │
        ├── Validates & parses uploaded file
        ├── Creates DB rows (rfp_documents + rfp_document_content + rfp_jobs)
        └── Enqueues Celery task ID → Redis
                          │
                     Redis (broker)
                          │
                    Celery Worker
                          │
                          ├── Fetches extracted text from PostgreSQL
                          ├── Runs rule-based analysis engine
                          └── Writes results back to rfp_jobs table
                          │
                     PostgreSQL
```

The frontend polls `GET /api/v1/jobs/{id}` every 3 seconds until the job reaches a terminal state (`completed` or `failed`).

---

## Technology Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI + Uvicorn |
| Task queue | Celery 5 |
| Message broker | Redis 7 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2 (async + sync sessions) |
| Migrations | Alembic |
| Package manager | uv |
| PDF parsing | pdfplumber |
| DOCX parsing | python-docx |
| Frontend | React 18 + Vite 5 |
| Containerisation | Docker + Docker Compose |

---

## Project Structure

```
rfp-analyzer/
├── Dockerfile                  # Multi-stage: frontend (Node) + backend (Python)
├── .dockerignore               # Excludes .venv, node_modules, __pycache__
├── docker-compose.yml          # Orchestrates 5 services
│
├── backend/
│   ├── pyproject.toml          # Python dependencies (uv)
│   ├── alembic.ini             # Alembic config
│   ├── entrypoint.sh           # Runs migrations then Uvicorn (or Celery if args passed)
│   │
│   ├── alembic/
│   │   ├── env.py              # Alembic runtime environment
│   │   └── versions/
│   │       └── a1b2c3d4e5f6_create_normalized_schema.py
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI app factory
│       ├── config.py           # Pydantic settings (loaded from .env)
│       ├── constants.py        # ALLOWED_EXTENSIONS, MAX_FILE_SIZE, etc.
│       ├── database.py         # Async engine, session, Base, get_db dependency
│       ├── celery_app.py       # Celery instance with task registration
│       │
│       ├── models/
│       │   ├── __init__.py     # Imports all models (required for Alembic)
│       │   ├── rfp_document.py
│       │   ├── rfp_document_content.py
│       │   └── rfp_job.py
│       │
│       ├── parsers/
│       │   ├── base_parser.py
│       │   ├── pdf_parser.py
│       │   ├── docx_parser.py
│       │   ├── txt_parser.py
│       │   ├── parser_factory.py
│       │   └── __init__.py
│       │
│       ├── analysis/
│       │   ├── engine.py       # AnalysisResult dataclass + RuleBasedAnalysisEngine
│       │   ├── summariser.py
│       │   ├── risk_analyser.py
│       │   ├── effort_estimator.py
│       │   ├── recommender.py
│       │   └── __init__.py
│       │
│       ├── repositories/
│       │   ├── rfp_job_repository.py       # Async (FastAPI)
│       │   ├── sync_rfp_job_repository.py  # Sync (Celery worker)
│       │   └── __init__.py
│       │
│       ├── services/
│       │   ├── rfp_job_service.py
│       │   └── __init__.py
│       │
│       ├── tasks/
│       │   ├── analysis_task.py
│       │   └── __init__.py
│       │
│       ├── routers/
│       │   ├── rfp_jobs.py
│       │   └── __init__.py
│       │
│       └── schemas/
│           ├── rfp_job.py
│           └── __init__.py
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js          # Proxies /api/* → backend:8000
    └── src/
        ├── main.jsx
        ├── App.jsx             # View router: list | upload | detail
        ├── api/
        │   └── rfpClient.js    # All fetch calls centralised here
        ├── components/
        │   ├── FileUploadForm.jsx   # Two tabs: file upload + text paste
        │   ├── JobList.jsx          # Table of all jobs with sequential numbering
        │   └── JobDetail.jsx        # Polling detail view with results
        └── styles/
            └── main.css        # CSS custom properties, all styles
```

---

## Database Schema

Three tables — normalized to avoid loading large text blobs on every query.

### `rfp_documents`
Immutable metadata record created when a file is uploaded.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `title` | VARCHAR(255) | Derived from filename stem |
| `original_filename` | VARCHAR(512) | |
| `file_type` | VARCHAR(10) | `pdf`, `docx`, or `txt` |
| `created_at` | TIMESTAMPTZ | |

### `rfp_document_content`
Holds the extracted text — separated so list queries never load it.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `document_id` | UUID FK → `rfp_documents` | CASCADE delete, unique |
| `extracted_text` | TEXT | Full plain text from parser |

### `rfp_jobs`
One analysis job per document. Analysis results are written here by the Celery worker.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `document_id` | UUID FK → `rfp_documents` | CASCADE delete, indexed |
| `status` | ENUM | `pending` → `processing` → `completed` / `failed` |
| `error_message` | TEXT | Set on failure |
| `risk_level` | VARCHAR(10) | `Low`, `Medium`, `High` — indexed |
| `effort` | VARCHAR(10) | `Small`, `Medium`, `Large` — indexed |
| `recommendation` | VARCHAR(20) | `Go`, `No-Go`, `Needs Discussion` — indexed |
| `summary` | JSON | List of 4–5 bullet strings |
| `requirements` | JSON | List of detected requirement strings |
| `risk_reasons` | JSON | List of matched risk keyword strings |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | Set on update |

---

## Backend — Layer by Layer

### Configuration

**`app/config.py`** — `Settings` class (Pydantic BaseSettings). Reads all config from environment variables / `.env` file. Fields:

- `DATABASE_URL` — async PostgreSQL URL (`postgresql+asyncpg://...`)
- `SYNC_DATABASE_URL` — sync URL (`postgresql+psycopg2://...`) used by Celery
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

**`app/constants.py`**:
- `ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}`
- `MAX_FILE_SIZE_BYTES = 10 MB`
- `MIN_EXTRACTED_TEXT_LENGTH = 50` characters

---

### Models

**`models/rfp_document.py`** — `RFPDocument`
- SQLAlchemy mapped class for `rfp_documents`
- Has `content` (one-to-one) and `jobs` (one-to-many) relationships

**`models/rfp_document_content.py`** — `RFPDocumentContent`
- SQLAlchemy mapped class for `rfp_document_content`
- `document_id` has a unique constraint (one content row per document)

**`models/rfp_job.py`** — `RFPJob` + `JobStatus` enum
- `JobStatus`: `pending | processing | completed | failed`
- `risk_level`, `effort`, `recommendation` are proper indexed columns (not inside JSON)
- `summary`, `requirements`, `risk_reasons` stored as JSON arrays

**`models/__init__.py`** — imports all three models so SQLAlchemy's `Base.metadata` registers every table before Alembic runs.

---

### Parsers

Strategy pattern. Each parser implements `BaseFileParser.extract_text(file_bytes) -> str`.

| Class | File | Library |
|---|---|---|
| `PDFParser` | `pdf_parser.py` | pdfplumber — also strips `(cid:NNN)` font encoding artifacts |
| `DOCXParser` | `docx_parser.py` | python-docx |
| `TXTParser` | `txt_parser.py` | stdlib — UTF-8 with latin-1 fallback |

**`ParserFactory`** (`parser_factory.py`) — maps extension strings to parser classes and returns the correct instance. Raises `ValueError` for unknown types.

---

### Analysis Engine

All strategies are pure functions of text — no I/O, no DB, no HTTP.

**`engine.py`**:
- `AnalysisResult` dataclass — `summary`, `requirements`, `risk_level`, `risk_reasons`, `effort`, `recommendation`
- `BaseAnalysisEngine` ABC — defines `analyse(title, text) -> AnalysisResult`
- `RuleBasedAnalysisEngine` — orchestrates the four strategies below
- `AnalysisEngineFactory` — returns a configured engine instance

**`summariser.py`** — `Summariser`
Extracts 4–5 bullet-point sentences from the document as a summary.

**`risk_analyser.py`** — `RiskAnalyser`
Scores the text by counting keyword matches:
- High-risk keywords (score 2 each): `compliance`, `gdpr`, `migration`, `legacy`, `sla`, `penalty`, `audit`, `security`, `encryption`, `hipaa`, `pci`, `real-time`, `regulation`
- Medium-risk keywords (score 1 each): `integration`, `api`, `third-party`, `custom`, `timeline`, `budget`, `offshore`, `vendor`, `deadline`

Score → Level: `0–2` = Low, `3–5` = Medium, `6+` = High

**`effort_estimator.py`** — `EffortEstimator`
- Base: word count — `<200` = Small, `200–600` = Medium, `>600` = Large
- Bump: if more than 8 list-style requirement lines found → bump up one size

**`recommender.py`** — `Recommender`
4-rule matrix:
- High risk + Large effort → `No-Go`
- High risk + any other → `Needs Discussion`
- Medium risk + Large effort → `Needs Discussion`
- Everything else → `Go`

---

### Repositories

Two separate repository classes because FastAPI uses async sessions (asyncpg) and Celery uses sync sessions (psycopg2). They cannot share a session.

**`rfp_job_repository.py`** — `RFPJobRepository` (async, for FastAPI)
- `create(title, filename, file_type, extracted_text)` — inserts `RFPDocument` + `RFPDocumentContent` + `RFPJob` in one transaction
- `get_by_id(job_id)` — eagerly loads the `document` relationship
- `list_all()` — all jobs newest first, with document loaded
- `update_status(job_id, status)` — guards against overwriting terminal states
- `save_results(job_id, results)` — writes all analysis fields + sets status to `completed`
- `save_error(job_id, message)` — sets `error_message` + status to `failed`
- `get_content(document_id)` — returns `RFPDocumentContent` row

**`sync_rfp_job_repository.py`** — `SyncRFPJobRepository` (sync, for Celery)
- Same operations without `async/await`
- Adds `get_extracted_text(document_id)` — used by the Celery task to fetch text from the content table

---

### Services

**`services/rfp_job_service.py`** — `RFPJobService`

Business logic lives here. Routers call service methods; services call repositories and tasks.

- `submit_rfp_file(filename, file_bytes)`:
  1. Validates extension (must be pdf/docx/txt)
  2. Validates file size (≤ 10 MB)
  3. Calls `ParserFactory` to get the right parser
  4. Extracts text; validates length (≥ 50 chars)
  5. Creates DB rows via repository
  6. Dispatches `analyse_rfp.delay(job_id)` to Celery

- `submit_rfp_text(title, text)`:
  1. Validates title is not blank
  2. Validates text length (≥ 50 chars)
  3. Creates DB rows and dispatches Celery task

- `get_job(job_id)` — delegates to repository
- `list_jobs()` — delegates to repository

---

### Celery Task

**`tasks/analysis_task.py`** — `analyse_rfp`

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def analyse_rfp(self, job_id: str) -> None:
```

Runs in its own process (Celery worker container). Uses a sync SQLAlchemy session.

Steps:
1. Fetch `RFPJob` from DB
2. Fetch extracted text from `rfp_document_content` via `get_extracted_text()`
3. Update status → `processing`
4. Run `RuleBasedAnalysisEngine().analyse()`
5. Write `AnalysisResult` fields to `rfp_jobs` + set status → `completed`
6. On any exception: set status → `failed` + save error message

**`celery_app.py`** — Celery instance configured with:
- `include=["app.tasks.analysis_task"]` — registers the task
- JSON serialization
- UTC timezone

---

### API Routers

**`routers/rfp_jobs.py`** — prefix `/api/v1/jobs`, tag `RFP Jobs`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/jobs` | Upload RFP file (multipart/form-data). Returns 202. |
| `POST` | `/api/v1/jobs/text` | Submit RFP as JSON text body. Returns 202. |
| `GET` | `/api/v1/jobs` | List all jobs, newest first. |
| `GET` | `/api/v1/jobs/{job_id}` | Get full job detail including results. |

`redirect_slashes=False` is set on the FastAPI app to prevent 307 redirects breaking the Vite proxy.

**`main.py`** — `create_app()`:
- CORS middleware: allows `http://localhost:5173`
- Global 500 handler (never leaks stack traces)
- `GET /health` endpoint
- Includes the jobs router

---

### Schemas

**`schemas/rfp_job.py`**

- `RFPTextSubmitRequest` — `title` (1–255 chars) + `text` (≥ 50 chars)
- `RFPJobResponse` — lightweight list response: `id`, `status`, `created_at`, `title`, `original_filename`, `file_type` (last three flattened from the `document` relationship)
- `RFPJobDetailResponse` — extends response with: `error_message`, `summary`, `requirements`, `risk_level`, `risk_reasons`, `effort`, `recommendation`, `updated_at`

---

## Frontend

Single-page React app. No routing library — view is managed by `useState` in `App.jsx`.

### Views
- **`list`** — default view, shows `JobList`
- **`upload`** — shows `FileUploadForm`
- **`detail`** — shows `JobDetail` for a selected job ID

### Components

**`App.jsx`** — root component. Holds `view` state and `selectedJobId`. Nav bar with "All Jobs" and "Upload RFP" buttons.

**`FileUploadForm.jsx`** — two-tab form:
- **Upload File tab** — drag-and-drop zone or file picker. Accepts PDF, DOCX, TXT ≤ 10 MB. Calls `uploadRFP(file)`.
- **Enter Text tab** — title input + textarea with character counter. Calls `submitText(title, text)`.
On success, navigates to the detail view for the new job.

**`JobList.jsx`** — table of all jobs. Columns: `#` (sequential number), Filename, Type, Status, Submitted. Clicking a row opens the detail view. Empty state prompts to upload. Refresh button.

**`JobDetail.jsx`** — polls `GET /api/v1/jobs/{id}` every 3 seconds. Shows spinner while `pending` or `processing`. On `completed` renders five result sections: Summary, Requirements, Risk Level, Effort, Recommendation. On `failed` shows error message. Back button returns to list.

### API Client

**`api/rfpClient.js`** — all `fetch` calls in one place:
- `uploadRFP(file)` — `POST /api/v1/jobs` multipart
- `submitText(title, text)` — `POST /api/v1/jobs/text` JSON
- `listJobs()` — `GET /api/v1/jobs`
- `getJob(jobId)` — `GET /api/v1/jobs/{jobId}`

`BASE_URL = "/api/v1"` — relative path, proxied by Vite to the backend container.

### Styling

**`styles/main.css`** — plain CSS, no libraries:
- CSS custom properties on `:root`: `--bg`, `--ink`, `--green`, `--red`, `--amber`, `--blue`, etc.
- Fonts: IBM Plex Mono (IDs, badges, metadata), Georgia (body text)
- Includes: nav bar, card layouts, badge system (status, risk, effort, recommendation), tab bar, drag-and-drop zone, spinner animation, empty state, alert styles

---

## Infrastructure

### Docker Compose Services

| Service | Image | Port |
|---|---|---|
| `postgres` | postgres:16-alpine | 5432 |
| `redis` | redis:7-alpine | 6379 |
| `backend` | rfp-analyzer-backend | 8001→8000 |
| `worker` | rfp-analyzer-worker | (internal only) |
| `frontend` | rfp-analyzer-frontend | 5173 |

### Dockerfile (root, multi-stage)

**`frontend` stage** — Node 20 Alpine: installs npm packages, copies source, runs `vite --host 0.0.0.0`

**`backend` stage** — Python 3.12 slim: installs `curl` + `uv`, syncs packages, copies source, runs `entrypoint.sh`

### `entrypoint.sh`
```sh
if [ "$#" -gt 0 ]; then
  exec uv run "$@"       # ← Celery worker uses this path
fi
uv run alembic upgrade head
exec uv run uvicorn app.main:app --reload
```

The worker service passes `celery -A app.celery_app worker --loglevel=info` as the Docker command, which the entrypoint passes through to `uv run`.

### Vite Proxy (`vite.config.js`)
```js
proxy: {
  "/api": { target: "http://backend:8000", changeOrigin: true }
}
```
All API calls from the browser go to Vite's dev server, which forwards them to the `backend` container by Docker DNS name — no CORS issues, no hardcoded ports in browser JS.

---

## Environment Variables

Create a `.env` file in the project root:

```env
POSTGRES_USER=rfp
POSTGRES_PASSWORD=rfp
POSTGRES_DB=rfp_analyzer

DATABASE_URL=postgresql+asyncpg://rfp:rfp@postgres:5432/rfp_analyzer
SYNC_DATABASE_URL=postgresql+psycopg2://rfp:rfp@postgres:5432/rfp_analyzer
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## Running the Project

### Prerequisites
- Docker Desktop

### Start everything
```powershell
cd rfp-analyzer
docker compose up --build
```

All 5 containers start. Alembic migrations run automatically on backend startup.

### Access
- **Frontend**: http://localhost:5173
- **API docs (Swagger)**: http://localhost:8001/docs
- **Health check**: http://localhost:8001/health

### Stop and wipe database
```powershell
docker compose down -v
```

### Rebuild from scratch (after code changes)
```powershell
docker compose down -v
docker compose up --build
```

---

## API Reference

### `POST /api/v1/jobs`
Upload an RFP file for analysis.

- **Content-Type**: `multipart/form-data`
- **Field**: `file` — PDF, DOCX, or TXT, max 10 MB
- **Response 202**: `RFPJobResponse`
- **Response 422**: validation error (bad extension, too large, no extractable text)

### `POST /api/v1/jobs/text`
Submit RFP content as plain text.

- **Content-Type**: `application/json`
- **Body**: `{ "title": "string", "text": "string (min 50 chars)" }`
- **Response 202**: `RFPJobResponse`

### `GET /api/v1/jobs`
List all submitted jobs, newest first.

- **Response 200**: array of `RFPJobResponse`

### `GET /api/v1/jobs/{job_id}`
Get full detail for a single job including analysis results.

- **Response 200**: `RFPJobDetailResponse`
- **Response 404**: job not found

### Job lifecycle
```
pending → processing → completed
                    ↘ failed
```
Poll the detail endpoint every few seconds — the frontend does this automatically every 3 seconds.

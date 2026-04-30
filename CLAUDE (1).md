N# CLAUDE.md — RFP Insight & Risk Analyzer

> **For the AI assistant reading this file:** You are acting as a **senior software engineer**
> embedded in this project. Follow every instruction in this file precisely. Do not deviate from
> the tech stack. Do not skip phases. Do not implement multiple phases in a single step.
> Stop and wait for user confirmation before starting the next phase.

---

## 0. Project North Star

Build a small internal tool for pre-sales teams to evaluate incoming RFPs (Request for Proposals).
Users upload an RFP document (PDF, DOCX, or TXT). The system extracts text from the file,
processes the analysis asynchronously in a background worker, and returns five structured outputs:
a summary, key requirements, risk level, effort estimate, and a Go/No-Go recommendation.

**There is no manual text form.** File upload is the only input method.

---

## 1. Mandatory Tech Stack

You MUST use **only** the technologies listed below. Do not introduce any alternative library,
framework, or tool that is not in this list without explicit user approval.

### 1.1 Backend

| Layer                  | Technology                          |
|------------------------|-------------------------------------|
| API Framework          | FastAPI                             |
| Background Jobs        | Celery                              |
| Message Broker         | Redis                               |
| Database               | PostgreSQL                          |
| ORM                    | SQLAlchemy (async)                  |
| Migrations             | Alembic                             |
| Containerisation       | Docker + Docker Compose             |
| Dependency Mgmt        | uv                                  |
| File Upload Handling   | python-multipart (FastAPI built-in) |
| PDF Text Extraction    | pdfplumber                          |
| DOCX Text Extraction   | python-docx                         |
| TXT Handling           | Python stdlib (no extra library)    |

### 1.2 Frontend

| Layer              | Technology                            |
|--------------------|---------------------------------------|
| Framework          | React (Vite)                          |
| Styling            | Plain CSS (no Tailwind, no CSS-in-JS) |
| HTTP Client        | Native fetch API                      |

> **No additional npm packages** beyond what Vite scaffolds. No axios, no react-router,
> no react-query, no UI libraries.

---

## 2. Guiding Engineering Principles

Apply all of the following on every file you touch. These are non-negotiable.

### 2.1 SOLID

- **S** — Every class/module has one reason to change. Parser, analysis, service, task, and
  router are all separate modules. The PDFParser only parses PDFs; it does not know about jobs.
- **O** — Adding a new file format (e.g., XLSX) requires only a new parser class and one line
  in the factory. Nothing else changes.
- **L** — Every concrete parser must be a drop-in replacement for BaseFileParser.
  Every concrete analyser must be a drop-in for BaseAnalysisEngine.
- **I** — BaseFileParser exposes only extract_text(file_bytes) -> str. Nothing more.
- **D** — Routers depend on RFPJobService (abstraction), not on any repository or parser
  directly. Services depend on BaseFileParser and BaseAnalysisEngine, not on concrete types.

### 2.2 Clean Code

- Functions do ONE thing and are <= 20 lines wherever possible.
- No magic strings — use Enum or module-level ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB.
- All public functions, classes, and modules have docstrings.
- Variable names are intention-revealing (extracted_text not txt, rfp_job not r).
- No commented-out dead code is committed.

### 2.3 Design Patterns in Use

| Pattern            | Where applied                                                    |
|--------------------|------------------------------------------------------------------|
| Strategy Pattern   | Each file format is a separate parser strategy                   |
| Factory Pattern    | ParserFactory selects the right parser by file extension         |
| Strategy Pattern   | Risk, effort, recommendation logic are independent strategies    |
| Factory Pattern    | AnalysisEngineFactory wires and returns the analysis engine      |
| Repository Pattern | All DB access is encapsulated in RFPJobRepository                |
| Service Layer      | All business logic (parse -> queue -> fetch) lives in service    |
| DTO / Schema       | Pydantic models are the only objects crossing API boundaries     |

---

## 3. Project Structure (Create This Exactly)

```
rfp-analyzer/
├── backend/
│   ├── pyproject.toml              # uv-managed dependencies
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory + lifespan
│   │   ├── config.py               # Settings via pydantic-settings
│   │   ├── database.py             # Async SQLAlchemy engine + session
│   │   ├── constants.py            # ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, etc.
│   │   ├── models/
│   │   │   └── rfp_job.py          # SQLAlchemy ORM model
│   │   ├── schemas/
│   │   │   └── rfp_job.py          # Pydantic request/response schemas
│   │   ├── repositories/
│   │   │   └── rfp_job_repository.py
│   │   ├── services/
│   │   │   └── rfp_job_service.py
│   │   ├── parsers/                # NEW: file parsing layer
│   │   │   ├── base_parser.py      # Abstract BaseFileParser
│   │   │   ├── pdf_parser.py       # PDFParser using pdfplumber
│   │   │   ├── docx_parser.py      # DOCXParser using python-docx
│   │   │   ├── txt_parser.py       # TXTParser using stdlib
│   │   │   └── parser_factory.py   # ParserFactory
│   │   ├── analysis/
│   │   │   ├── engine.py           # Abstract base + AnalysisResult + factory
│   │   │   ├── summariser.py
│   │   │   ├── risk_analyser.py
│   │   │   ├── effort_estimator.py
│   │   │   └── recommender.py
│   │   ├── tasks/
│   │   │   └── analysis_task.py    # Celery task (receives extracted text only)
│   │   ├── routers/
│   │   │   └── rfp_jobs.py
│   │   └── celery_app.py
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── rfpClient.js        # All fetch/upload calls centralised here
│       ├── components/
│       │   ├── FileUploadForm.jsx  # replaces SubmitForm — file upload only
│       │   ├── JobList.jsx
│       │   └── JobDetail.jsx
│       └── styles/
│           └── main.css
├── docker-compose.yml
└── CLAUDE.md
```

---

## 4. File Handling Architecture — Read This Before Coding

This section defines how a file flows through the system. Do not deviate from this flow.

```
Browser
  │
  │  multipart/form-data  (file binary)
  ▼
FastAPI Router  (POST /api/v1/jobs)
  │
  │  1. Validate extension (pdf | docx | txt)
  │  2. Validate file size (<= MAX_FILE_SIZE_BYTES)
  │  3. Read file bytes: await file.read()
  │  4. Call service.submit_rfp_file(filename, file_bytes)
  ▼
RFPJobService
  │
  │  5. Derive title from filename stem (replace _ and - with spaces, title-case)
  │  6. ParserFactory.get_parser(extension).extract_text(file_bytes)
  │  7. Validate extracted text length >= MIN_EXTRACTED_TEXT_LENGTH
  │  8. repository.create(title, filename, file_type, extracted_text)
  │  9. analyse_rfp.delay(job_id, title, extracted_text)
  │ 10. Return the new RFPJob
  ▼
Celery Worker  (analyse_rfp task)
  │
  │ 11. Update status -> "processing"
  │ 12. AnalysisEngineFactory.create().analyse(title, extracted_text)
  │ 13. repository.save_results(job_id, result_fields)
  │ 14. Update status -> "completed"
  │     (on any error -> "failed" + save error_message)
  ▼
PostgreSQL
```

> KEY RULE: The file is parsed BEFORE it enters the task queue.
> Celery receives only a plain str (the extracted text).
> Never pass file bytes or file paths through the message broker.

---

## 5. Implementation Phases

> **Rule:** Implement ONE phase at a time. Stop after each phase and wait for the user to
> confirm before starting the next one. Never bundle two phases in one response.

---

### PHASE 1 — Project Scaffolding and Infrastructure

**Goal:** All Docker services start cleanly. No application logic yet.

**Tasks:**

1. **docker-compose.yml** — Five services:
   - postgres — postgres:16-alpine, named volume postgres_data.
     Env: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB. Port 5432.
   - redis — redis:7-alpine. Port 6379.
   - backend — build ./backend/Dockerfile. Depends on postgres, redis.
     Volume mount ./backend:/app for hot-reload. Port 8000:8000.
   - worker — same build as backend.
     Command: celery -A app.celery_app worker --loglevel=info.
     Depends on postgres, redis. Same env vars as backend.
   - frontend — build ./frontend/Dockerfile. Port 5173:5173.

2. **backend/pyproject.toml** — uv project. Exact dependencies:
   ```
   fastapi
   uvicorn[standard]
   python-multipart
   celery[redis]
   redis
   sqlalchemy[asyncio]
   asyncpg
   psycopg2-binary
   alembic
   pydantic-settings
   python-dotenv
   pdfplumber
   python-docx
   ```

3. **backend/Dockerfile** — Single stage, python:3.12-slim. Install uv. Copy project.
   Run uv sync. Expose 8000.
   entrypoint.sh:
   ```bash
   #!/bin/sh
   alembic upgrade head
   exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The worker service overrides the command so migrations only run from the backend service.

4. **backend/app/config.py** — Settings(BaseSettings) with:
   DATABASE_URL, SYNC_DATABASE_URL, REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND.

5. **backend/app/constants.py** — Never hardcode these values elsewhere:
   ```python
   ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
   MAX_FILE_SIZE_MB = 10
   MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
   MIN_EXTRACTED_TEXT_LENGTH = 50  # characters
   ```

6. **backend/app/main.py** — Minimal FastAPI app with lifespan.
   GET /health returns {"status": "ok"}. No routers yet.

7. **frontend/** — Bare Vite + React scaffold.
   Single App.jsx rendering "RFP Analyzer — Coming Soon".

**Acceptance criteria for Phase 1:**
- docker compose up --build completes without errors.
- All five containers are running.
- GET http://localhost:8000/health returns {"status": "ok"}.
- http://localhost:5173 renders the placeholder.

---

### PHASE 2 — Database Layer (Model, Migration, Repository)

**Goal:** Persist job data including file metadata and extracted text.

**Tasks:**

1. **backend/app/database.py**
   - Async engine from DATABASE_URL.
   - AsyncSessionLocal via async_sessionmaker.
   - get_db FastAPI dependency (async generator).
   - Base declarative base for all models.

2. **backend/app/models/rfp_job.py** — RFPJob ORM model. All columns:
   ```
   id                UUID, primary_key, default=uuid4
   title             String(255), not null         derived from filename
   original_filename String(512), not null         e.g. "acme_rfp_2024.pdf"
   file_type         String(10), not null          "pdf" | "docx" | "txt"
   extracted_text    Text, not null                full text pulled from file
   status            Enum("pending","processing","completed","failed"), default="pending"
   error_message     Text, nullable
   summary           JSON, nullable                list[str]
   requirements      JSON, nullable                list[str]
   risk_level        String(10), nullable          "Low" | "Medium" | "High"
   risk_reasons      JSON, nullable                list[str]
   effort            String(10), nullable          "Small" | "Medium" | "Large"
   recommendation    String(20), nullable          "Go" | "No-Go" | "Needs Discussion"
   created_at        DateTime, server_default=now()
   updated_at        DateTime, onupdate=now()
   ```

3. **Alembic setup** — alembic init alembic. Configure env.py:
   - Import Base and all models.
   - Use SYNC_DATABASE_URL (psycopg2) for the migration runner.

4. **First migration** — alembic revision --autogenerate -m "create_rfp_jobs".
   Verify the generated SQL creates the table with the status enum type.

5. **backend/app/repositories/rfp_job_repository.py** — RFPJobRepository:

   | Method                                         | Description                              |
   |------------------------------------------------|------------------------------------------|
   | create(title, filename, file_type, text)       | Insert new row, return RFPJob            |
   | get_by_id(job_id) -> RFPJob or None            | Fetch single job                         |
   | list_all() -> list[RFPJob]                     | All jobs, ordered by created_at desc     |
   | update_status(job_id, status)                  | Guard: cannot downgrade completed/failed |
   | save_results(job_id, results_dict)             | Write all five output fields             |
   | save_error(job_id, message)                    | Write error message, set status=failed   |

   All methods async. Zero business logic. Zero raw SQL.

**Acceptance criteria for Phase 2:**
- alembic upgrade head runs cleanly inside the backend container.
- rfp_jobs table exists in PostgreSQL with all columns and correct types.
- RFPJobRepository can be imported without errors.

---

### PHASE 3 — File Parser Layer

**Goal:** Extensible file-parsing module that converts uploaded bytes to plain text.
This is a pure Python layer with no FastAPI or DB dependencies.

**Tasks:**

1. **backend/app/parsers/base_parser.py** — Abstract base:
   ```python
   from abc import ABC, abstractmethod

   class BaseFileParser(ABC):
       """Contract for all file format parsers."""

       @abstractmethod
       def extract_text(self, file_bytes: bytes) -> str:
           """Extract and return all readable text from the file bytes."""
   ```

2. **backend/app/parsers/pdf_parser.py** — PDFParser(BaseFileParser):
   - Use pdfplumber.open(io.BytesIO(file_bytes)).
   - Iterate all pages. Call page.extract_text().
   - Join page texts with "\n\n". Strip whitespace.
   - If all pages return None raise ValueError:
     "PDF contains no extractable text. Scanned image PDFs are not supported."

3. **backend/app/parsers/docx_parser.py** — DOCXParser(BaseFileParser):
   - Use docx.Document(io.BytesIO(file_bytes)).
   - Join paragraph.text for non-empty paragraphs, separated by "\n".
   - Raise ValueError("DOCX file contains no readable text.") if result is blank.

4. **backend/app/parsers/txt_parser.py** — TXTParser(BaseFileParser):
   - Decode file_bytes as UTF-8. Fall back to latin-1 if UTF-8 fails.
   - Strip result. Raise ValueError("TXT file is empty.") if blank after strip.

5. **backend/app/parsers/parser_factory.py** — ParserFactory:
   ```python
   class ParserFactory:
       """Returns the correct parser for a given file extension."""

       _PARSERS: dict[str, BaseFileParser] = {
           "pdf":  PDFParser(),
           "docx": DOCXParser(),
           "txt":  TXTParser(),
       }

       @classmethod
       def get_parser(cls, extension: str) -> BaseFileParser:
           parser = cls._PARSERS.get(extension.lower())
           if parser is None:
               raise ValueError(f"Unsupported file type: .{extension}")
           return parser
   ```

**Acceptance criteria for Phase 3:**
- Write a scratch script that loads a real PDF, DOCX, and TXT file. Confirm each returns text.
- ParserFactory.get_parser("xlsx") raises ValueError.
- PDFParser raises ValueError on an empty or image-only PDF.
- No FastAPI or DB imports appear anywhere in parsers/.

---

### PHASE 4 — Analysis Engine (Business Logic)

**Goal:** Rule-based strategies that convert extracted text into five structured outputs.
This layer has no knowledge of files, HTTP, or databases.

**Tasks:**

1. **backend/app/analysis/engine.py**

   AnalysisResult dataclass:
   ```python
   @dataclass
   class AnalysisResult:
       summary: list[str]
       requirements: list[str]
       risk_level: str          # "Low" | "Medium" | "High"
       risk_reasons: list[str]
       effort: str              # "Small" | "Medium" | "Large"
       recommendation: str      # "Go" | "No-Go" | "Needs Discussion"
   ```

   BaseAnalysisEngine(ABC) — one abstract method:
   analyse(title: str, text: str) -> AnalysisResult

   RuleBasedAnalysisEngine(BaseAnalysisEngine):
   - Constructor injects: Summariser, RiskAnalyser, EffortEstimator, Recommender.
   - analyse() calls each strategy and assembles AnalysisResult.

   AnalysisEngineFactory:
   - create() -> BaseAnalysisEngine
   - Builds and returns a fully wired RuleBasedAnalysisEngine.
   - This is the only place concrete strategies are instantiated.

2. **backend/app/analysis/summariser.py** — Summariser:
   - summarise(title: str, text: str) -> list[str] — returns 4-5 bullets.
   - Rules:
     1. First non-empty sentence -> bullet 1.
     2. Up to 3 sentences containing: require, must, shall, deliver, integrate, provide -> bullets 2-4.
     3. Final bullet: f"Document contains approximately {word_count} words."

3. **backend/app/analysis/risk_analyser.py** — RiskAnalyser:
   - analyse_risk(text: str) -> tuple[str, list[str]] returning (level, reasons).
   - Case-insensitive keyword scoring:
     ```
     HIGH   (+2): compliance, regulation, GDPR, migration, legacy, real-time,
                  SLA, penalty, audit, security, encryption, HIPAA, PCI
     MEDIUM (+1): integration, API, third-party, custom, timeline, budget,
                  offshore, vendor, deadline
     ```
   - Score >= 4 -> "High". 2-3 -> "Medium". < 2 -> "Low".
   - reasons = list of matched keyword strings (deduped).

4. **backend/app/analysis/effort_estimator.py** — EffortEstimator:
   - estimate(text: str) -> str
   - Word count rules:
     - < 200  -> "Small"
     - 200-600 -> "Medium"
     - > 600  -> "Large"
   - Additionally: count lines starting with -, bullet, or digit+period as requirements.
     If count > 8, bump up one size level.

5. **backend/app/analysis/recommender.py** — Recommender:
   - recommend(risk_level: str, effort: str) -> str
   - Decision matrix (first match wins):
     ```
     High   + Large  -> "No-Go"
     High   + any    -> "Needs Discussion"
     Medium + Large  -> "Needs Discussion"
     any    + any    -> "Go"
     ```

**Acceptance criteria for Phase 4:**
- Call AnalysisEngineFactory.create().analyse("Test RFP", sample_text) with a realistic
  multi-paragraph string. Confirm all six fields are populated with sensible values.
- No file I/O. No HTTP calls. No DB calls.

---

### PHASE 5 — Celery Task and Service Layer

**Goal:** Wire analysis into a background worker. Define the service layer that orchestrates
file parsing, job creation, and task dispatch.

**Tasks:**

1. **backend/app/celery_app.py**
   - Celery("rfp_analyzer", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
   - Config: task_serializer="json", result_serializer="json",
     accept_content=["json"], task_track_started=True.

2. **backend/app/tasks/analysis_task.py** — analyse_rfp Celery task:
   - @celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
   - Signature: analyse_rfp(self, job_id: str, title: str, extracted_text: str)
   - Workflow:
     ```
     1. Open a SYNCHRONOUS DB session (SYNC_DATABASE_URL + create_engine + sessionmaker).
     2. Instantiate RFPJobRepository(sync_session).
     3. repository.update_status(job_id, "processing").
     4. AnalysisEngineFactory.create().analyse(title, extracted_text).
     5. repository.save_results(job_id, asdict(analysis_result)).
     6. repository.update_status(job_id, "completed").
     7. On any Exception: repository.save_error(job_id, str(exc)). Re-raise.
     ```
   - IMPORTANT: Use a synchronous SQLAlchemy session here.
     Do NOT import or use AsyncSession, asyncpg, or async/await inside this file.

3. **backend/app/services/rfp_job_service.py** — RFPJobService:

   Constructor: __init__(self, repository: RFPJobRepository)

   Methods:
   - async submit_rfp_file(filename: str, file_bytes: bytes) -> RFPJob
   - async get_job(job_id: UUID) -> RFPJob | None
   - async list_jobs() -> list[RFPJob]

   submit_rfp_file steps:
   1. Extract extension from filename. Validate against ALLOWED_EXTENSIONS.
      Raise ValueError if not in set.
   2. Validate len(file_bytes) <= MAX_FILE_SIZE_BYTES.
      Raise ValueError("File exceeds maximum size of 10 MB.") if too large.
   3. parser = ParserFactory.get_parser(extension)
      extracted_text = parser.extract_text(file_bytes)
   4. Validate len(extracted_text.strip()) >= MIN_EXTRACTED_TEXT_LENGTH.
      Raise ValueError("Could not extract meaningful text from the file.") if too short.
   5. Derive title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
   6. job = await self.repository.create(title, filename, extension, extracted_text)
   7. analyse_rfp.delay(str(job.id), job.title, extracted_text)
   8. Return job.

**Acceptance criteria for Phase 5:**
- Upload a real PDF via a Python requests script (no UI yet).
- Confirm Celery worker logs show it picked up and processed the task.
- Confirm DB row transitions: pending -> processing -> completed.
- Upload a corrupted or image-only PDF. Confirm job ends in "failed" with an error message.

---

### PHASE 6 — FastAPI Routers and API Layer

**Goal:** Expose REST endpoints. The submit endpoint accepts multipart/form-data.

**API Contract:**

| Method | Path                | Input                        | Response               | Status |
|--------|---------------------|------------------------------|------------------------|--------|
| POST   | /api/v1/jobs        | multipart/form-data (file)   | RFPJobResponse         | 202    |
| GET    | /api/v1/jobs        | none                         | list[RFPJobResponse]   | 200    |
| GET    | /api/v1/jobs/{id}   | path param UUID              | RFPJobDetailResponse   | 200    |

**Tasks:**

1. **backend/app/schemas/rfp_job.py** — Pydantic v2 schemas:

   ```python
   class RFPJobResponse(BaseModel):
       id: UUID
       title: str
       original_filename: str
       file_type: str
       status: str
       created_at: datetime
       model_config = ConfigDict(from_attributes=True)

   class RFPJobDetailResponse(RFPJobResponse):
       error_message: str | None = None
       summary: list[str] | None = None
       requirements: list[str] | None = None
       risk_level: str | None = None
       risk_reasons: list[str] | None = None
       effort: str | None = None
       recommendation: str | None = None
       updated_at: datetime | None = None
   ```

   There is no RFPJobSubmitRequest schema. The input is UploadFile, not a JSON body.

2. **backend/app/routers/rfp_jobs.py** — Router prefix /api/v1/jobs:

   POST / — File upload endpoint:
   ```python
   @router.post("/", status_code=202, response_model=RFPJobResponse)
   async def submit_rfp(
       file: UploadFile = File(...),
       service: RFPJobService = Depends(get_service),
   ):
   ```
   - Await file.read() to get bytes.
   - Call service.submit_rfp_file(file.filename, file_bytes).
   - Catch ValueError from service -> HTTPException(status_code=422, detail=str(e)).
   - Return job as RFPJobResponse.

   GET / — Return list[RFPJobResponse].

   GET /{job_id} — Return RFPJobDetailResponse.
   - Return 404 if job is None.

   Dependency injection (in router file):
   ```python
   def get_repository(db: AsyncSession = Depends(get_db)) -> RFPJobRepository:
       return RFPJobRepository(db)

   def get_service(repo: RFPJobRepository = Depends(get_repository)) -> RFPJobService:
       return RFPJobService(repo)
   ```

3. **backend/app/main.py update**:
   - Include the router with prefix /api/v1.
   - CORS middleware: allow http://localhost:5173, all methods, all headers.
   - Global 500 handler for unhandled exceptions (safe message, no stack trace leaked).

**Acceptance criteria for Phase 6:**
- POST /api/v1/jobs with a valid PDF -> 202 + job ID.
- POST /api/v1/jobs with a .xlsx file -> 422 with "Unsupported file type".
- POST /api/v1/jobs with an empty TXT -> 422 "Could not extract meaningful text".
- GET /api/v1/jobs returns the job list.
- GET /api/v1/jobs/{id} returns full results once the worker completes.
- GET /api/v1/jobs/not-a-real-id -> 404.
- FastAPI /docs shows a file upload field (not a JSON body) for the POST endpoint.

---

### PHASE 7 — React Frontend

**Goal:** Three-screen UI with file upload, job list, and polled detail view.
No UI libraries. No routing library. Plain CSS only.

**Tasks:**

1. **frontend/src/api/rfpClient.js** — All API calls in one module:
   ```js
   const BASE_URL = "http://localhost:8000/api/v1";

   // Uses FormData. Do NOT set Content-Type manually — browser sets multipart boundary.
   export const uploadRFP = async (file) => {
     const form = new FormData();
     form.append("file", file);
     const res = await fetch(`${BASE_URL}/jobs`, { method: "POST", body: form });
     if (!res.ok) {
       const err = await res.json();
       throw new Error(err.detail ?? "Upload failed");
     }
     return res.json();
   };

   export const listJobs = async () => { ... };   // GET /jobs
   export const getJob   = async (jobId) => { ... }; // GET /jobs/:id
   ```

2. **FileUploadForm.jsx** — File upload is the ONLY input. No text fields.
   - Styled drop-zone div that handles dragover and drop events.
   - Hidden file input triggered by clicking the drop-zone.
     accept=".pdf,.docx,.txt"
   - Once a file is chosen: show filename and file size (KB or MB).
   - "Analyse RFP" button — disabled until a file is selected.
   - On submit:
     - Disable button, show "Uploading and queuing analysis…".
     - Call uploadRFP(file).
     - On success: show the job ID + "View Results" button.
     - On error: show the error message in red below the drop-zone.
   - Static label under the drop-zone: "Accepted formats: PDF, DOCX, TXT — max 10 MB"

3. **JobList.jsx** — Table with columns:
   Job ID (first 8 chars) | Original Filename | Type | Status | Submitted At

   - Status badge colours:
     pending    -> grey (#9ca3af)
     processing -> amber (#f59e0b)
     completed  -> green (#10b981)
     failed     -> red (#ef4444)
   - Each row is clickable -> opens JobDetail view.
   - Refresh button in the table header to re-fetch without page reload.

4. **JobDetail.jsx** — Accepts jobId prop.
   - On mount: getJob(jobId).
   - Polling: if status is pending or processing, poll every 3 seconds via setInterval.
     Clear interval when status becomes completed or failed.
     Clean up interval in useEffect return function.
   - Display:
     - Header: original filename + file type badge.
     - Status badge.
     - If completed: five output sections as labelled blocks:
         Summary        -> unordered list of bullets
         Key Requirements -> ordered list
         Risk Level     -> coloured badge (Low=green, Medium=amber, High=red) + reasons list
         Effort         -> badge (Small=blue, Medium=orange, Large=red)
         Recommendation -> large prominent badge (Go=green, No-Go=red, Needs Discussion=amber)
     - If failed: red error box containing the error_message text.
     - If pending or processing: CSS-only animated "Analysing document…" indicator.

5. **App.jsx** — useState manages current view: "list" | "upload" | "detail".
   - Nav bar with "All Jobs" and "Upload RFP" links.
   - selectedJobId state passed to JobDetail.
   - Clicking a job row in JobList -> setView("detail") + setSelectedJobId(id).

6. **styles/main.css**:
   - Aesthetic: utilitarian, document-centric. High information density.
   - Fonts: "IBM Plex Mono" for job IDs and metadata values.
     Body text: "Georgia" (serif — document feel).
   - Background: off-white #f7f6f2. Borders: 1px solid #c8c4b8.
   - Drop-zone: dashed border, darkens slightly on drag-over (CSS :focus-within or JS class).
   - Status badges: solid fill, white text, uppercase, letter-spaced, small caps size.
   - No box-shadows. No rounded corners on table rows.
   - Output section cards: 2px solid left border as accent only.

**Acceptance criteria for Phase 7:**
- Dropping a PDF onto the drop-zone -> upload starts, job ID appears on screen.
- Dropping an XLSX file -> error "Unsupported file type" shown inline (client-side check).
- Job list shows filename, file type badge, and status badge with correct colours.
- Clicking a job -> detail view shows spinner -> auto-updates when Celery finishes.
- All five output sections render correctly for a completed job.
- A failed job shows the error message in the red error box.

---

## 6. Cross-Cutting Rules (Apply in Every Phase)

- No inline SQL. All DB access through RFPJobRepository.
- No business logic in routers. Routers: validate input, call service, return response.
- No file I/O in Celery tasks. Tasks receive plain strings only.
- No hardcoded config values. Everything env-sensitive comes from app/config.py.
- Type hints on every function signature. Avoid Any.
- Pydantic at the API boundary. Never return raw ORM objects from a router.
- Status transitions are one-way. completed or failed jobs cannot revert to pending.
  Enforce this guard inside repository.update_status.
- All public functions, classes, and modules must have docstrings.
- constants.py is the single source of truth for ALLOWED_EXTENSIONS, size limits,
  keyword lists used by analysis strategies.

---

## 7. Environment Variables Reference

Set in docker-compose.yml for backend and worker services:

```
POSTGRES_USER=rfp_user
POSTGRES_PASSWORD=rfp_pass
POSTGRES_DB=rfp_db

DATABASE_URL=postgresql+asyncpg://rfp_user:rfp_pass@postgres:5432/rfp_db
SYNC_DATABASE_URL=postgresql+psycopg2://rfp_user:rfp_pass@postgres:5432/rfp_db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## 8. Definition of Done (Full Project)

All of the following must pass before the project is considered complete:

- [ ] docker compose up --build brings up all five services without errors.
- [ ] Alembic migration runs automatically on backend container startup.
- [ ] POST /api/v1/jobs with a valid PDF -> 202 + job ID.
- [ ] POST /api/v1/jobs with .xlsx -> 422 "Unsupported file type".
- [ ] POST /api/v1/jobs with empty TXT -> 422 "Could not extract meaningful text".
- [ ] Celery worker processes a job and updates DB to completed within ~10 seconds.
- [ ] GET /api/v1/jobs/{id} returns all five analysis fields when completed.
- [ ] A corrupted or image-only PDF results in status "failed" with a readable error message.
- [ ] React drop-zone accepts PDF, DOCX, TXT and rejects other types with a clear error.
- [ ] Job list shows filename, file type badge, and status badge with correct colours.
- [ ] Detail view auto-updates via polling without a manual page refresh.
- [ ] All five output sections render correctly for a completed job.
- [ ] FastAPI /docs shows the POST endpoint with a file picker (not a JSON body input).

---

## 9. What NOT to Build

- Manual text entry form (removed — file upload is the only input)
- Authentication or user sessions
- Pagination (return all jobs)
- External LLM API calls (analysis is rule-based only)
- Email or webhook notifications
- Admin panel
- Unit test suite (good to have, not required for this sprint)
- Any npm package beyond the Vite scaffold defaults
- Any CSS framework (no Tailwind, no Bootstrap, no MUI)

---

*End of CLAUDE.md*

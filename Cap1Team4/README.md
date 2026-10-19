# ClaimsIQ

ClaimsIQ is a backend API for insurance policies, claim processing, role-based access, document-grounded policy Q&A, analytics, and audit history. It is built with FastAPI, SQLAlchemy, PostgreSQL (Docker), SQLite (local development), and Pandas.

This repository contains the backend only; it does not include a web or mobile frontend.

## Implemented MVP

- JWT login and one-use refresh-token rotation, bcrypt password hashing, failed-login lockout, and role checks.
- Admin user and region administration; policy creation, search, status changes, and region-scoped reads.
- Claim submission against active policies, assignment validation, region-scoped visibility, status workflow, approval controls for high-value claims, notes, append-only status history, and audit events.
- Text, Markdown, and text-based PDF upload; SHA-256 duplicate detection; configurable size limits; searchable chunk indexing; admin activation/deactivation.
- Extractive RAG over active approved document chunks. Answers quote retrieved passages and return document/section/page citations; no-match responses never guess. This does not call an external LLM or vector database and does not require a paid API key.
- Pandas claims metrics and breakdowns, SLA breach counts, and AI query volume/theme reporting.
- PII redaction in AI-query logs, encryption at rest for submitted national ID values, and a verifiable hash-chained audit log.
- Alembic schema migration, synthetic demo data, Docker Compose for API + PostgreSQL, pytest tests, and GitHub Actions CI.

## Requirements

- Python 3.11 or newer.
- Docker Desktop only if running the PostgreSQL Compose deployment.

## Local setup (Windows PowerShell)

Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install -e ".[dev]"
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into `SECRET_KEY` in `.env`. Keep `.env` private; it is ignored by Git. `DATABASE_URL=sqlite:///./claims.db` is the local default.

Create the schema, bootstrap an administrator (password is prompted, not stored in command history), and optionally load the synthetic demo dataset:

```powershell
alembic upgrade head
python scripts/create_admin.py
python scripts/seed_demo_data.py --admin-email your.admin@example.com
```

The demo script creates four regions, five policies, up to 500 synthetic claims, and six sample guideline documents. It is safe to rerun; existing rows are skipped.

Start the API:

```powershell
uvicorn app.main:app --app-dir src --reload --host 127.0.0.1 --port 8000
```

Verify it is responding at <http://127.0.0.1:8000/health>. Interactive API docs are at <http://127.0.0.1:8000/docs>.

## Docker Compose (PostgreSQL)

Copy `.env.example` to `.env`, set a generated `SECRET_KEY`, and replace the three `POSTGRES_*` placeholders with local-only values. Use a URL-safe password (letters, digits, hyphens, and underscores) for `POSTGRES_PASSWORD`, since it is included in the connection URL. Then run:

```powershell
docker compose up --build
```

Compose waits for PostgreSQL, applies the Alembic migration, starts the API on port 8000, and persists database/document files in named volumes. Stop with `Ctrl+C`; use `docker compose down` to stop containers. Avoid `docker compose down -v` unless you intend to delete the persisted database and uploaded documents.

## Tests and lint

```powershell
python -m pytest -q
ruff check .
```

## Main API routes

All application routes use the `/api/v1` prefix. `/health` is public and checks database connectivity.

| Area | Routes |
| --- | --- |
| Authentication | `POST /auth/login`, `POST /auth/refresh` |
| Users and regions (Admin) | `GET/POST /users`, `PATCH /users/{id}/active`, `GET/POST /regions` |
| Policies | `GET/POST /policies`, `GET /policies/{id}`, `PATCH /policies/{id}/status` |
| Claims | `POST/GET /claims`, `GET /claims/{id}`, `PATCH /claims/{id}/assignment`, `PATCH /claims/{id}/status`, `GET /claims/{id}/history`, `GET /claims/{id}/notes` |
| Documents (Admin) | `GET/POST /documents`, `PATCH /documents/{id}/status` |
| AI assistant | `POST /ai/query` |
| Analytics (Admin/Manager) | `GET /analytics/claims`, `GET /analytics/ai` |
| Audit (Admin) | `GET /audit`, `GET /audit/verify` |

### Authentication walkthrough

1. `POST /api/v1/auth/login` with JSON `{"email":"...","password":"..."}`.
2. Send the returned `access_token` as `Authorization: Bearer <token>`.
3. Use the refresh token once at `POST /api/v1/auth/refresh`; the previous refresh token is revoked.
4. Create a policy, submit a claim against its active policy ID, then move it through `submitted → under_review → approved/rejected → closed`. A manager/admin must approve a high-value claim; overrides require justification.
5. An Admin uploads `.txt`, `.md`, or text-based `.pdf` using multipart form data (`file`, `doc_type`, optional `applies_to`, `title`, and `version`). Ask `POST /api/v1/ai/query` for a policy type and question; verify the returned citations before acting.

## Roles and data access

- Admin: all records; user/region/document administration; audit records.
- Claims Manager: policy management, all claims, overrides, and analytics.
- Claims Adjuster: records in their region or assigned to them; claim submission/processing and AI Q&A.
- Support Agent: read-only policy/claim lookup within their region and AI Q&A.

Unknown or out-of-scope claim/policy IDs return 404 to avoid disclosing records. Invalid request data returns a field-level 422 response.

## Configuration

Settings are read from environment variables or the root `.env` file. See `.env.example`. Important options include `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `DOCUMENT_STORAGE_DIR`, `MAX_UPLOAD_BYTES`, `SLA_DEFAULT_DAYS`, `HIGH_VALUE_THRESHOLD`, `RAG_TOP_K`, `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`, and `AI_RATE_LIMIT_PER_MINUTE`.

The AI rate limiter is process-local; use a shared store before running multiple API workers. Uploaded PDFs must contain extractable text; scanned-image OCR and external LLM generation are not included in this MVP. Do not deploy with development database credentials or a shared/committed secret key.

## Project layout

- `src/app/api/`: routes, auth dependencies, and role enforcement.
- `src/app/models/`, `schemas/`, `services/`: SQLAlchemy entities, request/response validation, and claim/audit logic.
- `src/app/rag/`: chunking, retrieval, and source-excerpt responses.
- `migrations/`: Alembic schema revisions.
- `scripts/`: database initialization, admin bootstrap, and synthetic demo data.
- `tests/`: unit and HTTP integration coverage.
- `data/sample_documents/`: fictional sample documents; generated uploads stay under ignored `data/documents/`.
- `docs/architecture.md`: system boundaries and request flow.

## Manual production checklist

Before a real deployment, provision a managed PostgreSQL database, replace the in-process rate limit with shared storage, configure trusted CORS origins and secret management, add TLS/reverse-proxy and backups, establish a key-rotation plan for encrypted PII, and run migrations as a separate deployment step. Review retention, privacy, and authorization policies with the organization; the included sample content and synthetic claims are for demonstration only.

# ClaimIQ — Claims, Analytics, Document Management and RAG

ClaimIQ provides claims management, analytics, document management, and
Azure-backed retrieval-augmented generation (RAG) for policy questions.

The FastAPI backend and Streamlit dashboard can run locally or as Docker
containers. PostgreSQL runs in a Docker container for local use and in a
persistent StatefulSet inside AKS for deployment; no Azure Database for
PostgreSQL instance is used. See [utilities/README.md](utilities/README.md)
for Compose and GitHub Actions deployment instructions.

## Included modules

- Authentication using JWT bearer tokens
- Role-based access control: `admin`, `reviewer`, `adjuster`, `customer`
- User listing for authorized roles
- Policy creation and listing
- Claim submission and retrieval
- Adjuster assignment
- Claim status workflow and append-only status history
- Claim notes
- Pandas-based analytics summary
- Audit log for key actions
- Automated unit/API tests using an isolated in-memory SQLite database

## Folder structure

```text
claimsIQ-Project/
├── .github/
│   └── workflows/
│       └── deploy-aks.yml
├── app/
│   ├── api/
│   │   ├── document_routes.py
│   │   └── query_routes.py
│   ├── prompts/
│   │   └── rag_prompt.py
│   ├── services/
│   │   ├── audit_service.py
│   │   ├── azure_auth.py
│   │   ├── blob_service.py
│   │   ├── chunking_service.py
│   │   ├── embedding_service.py
│   │   ├── extraction_service.py
│   │   ├── ingestion_service.py
│   │   ├── rag_service.py
│   │   └── search_service.py
│   ├── __init__.py
│   ├── bootstrap_admin.py
│   ├── config.py
│   ├── database.py
│   ├── init_db.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── seed.py
├── dashboard/
│   └── app.py
├── documents_to_Upload/
├── scripts/
│   └── create_search_index.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_bootstrap_admin.py
│   ├── test_rag_routes.py
│   └── test_rag_services.py
├── utilities/
│   ├── k8s/
│   │   ├── api.yaml
│   │   ├── bootstrap-job.yaml
│   │   ├── configmap.yaml
│   │   ├── dashboard.yaml
│   │   ├── namespace.yaml
│   │   └── postgres.yaml
│   ├── .env.example
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── README.md
├── .dockerignore
├── .env.example
├── .gitignore
├── INTEGRATION_NOTES.md
├── README.md
├── arch_readme.md
├── requirements.txt
└── swagger_testing_readme.md
```

## 1. Check your existing PostgreSQL container

In PowerShell or a terminal:

```bash
docker ps
```

Find the PostgreSQL container and check its `PORTS` value. If it shows
`127.0.0.1:5433->5432/tcp`, connect through host port `5433`. If it shows
`0.0.0.0:5432->5432/tcp`, connect through host port `5432`.

The container must publish a port to the host so the locally running Python
process can connect to it.

## 2. Create the application database

If a `claimiq` database already exists, keep using it; do not drop it.
Otherwise, connect to the PostgreSQL container and create the database.

Example command (replace the container name and PostgreSQL username with your
values):

```bash
docker exec -it <your-postgres-container-name> psql -U postgres -d postgres
```

At the `psql` prompt, create the database only if it does not already exist:

```sql
CREATE DATABASE claimiq;
```

If you prefer to use a dedicated database user, create that role and make it the database owner. Use your own password:

```sql
CREATE ROLE claimiq_local LOGIN PASSWORD 'YOUR_DATABASE_PASSWORD';
ALTER DATABASE claimiq OWNER TO claimiq_local;
```

If the role already exists, do not recreate it. Exit `psql` with `\q`.

## 3. Create `.env`

Copy `.env.example` to `.env` in the project root if `.env` does not already
exist. Update `DATABASE_URL` with your database username, password, and
published host port. Replace the other `YOUR_*` values you need with your own
settings and credentials.

Example if PostgreSQL is published on port 5433:

```env
DATABASE_URL=postgresql+psycopg2://claimiq_local:YOUR_DATABASE_PASSWORD@127.0.0.1:5433/claimiq
JWT_SECRET=YOUR_LONG_RANDOM_JWT_SECRET_REPLACE_WITH_AT_LEAST_32_RANDOM_CHARACTERS
ACCESS_TOKEN_MINUTES=120
CLAIMIQ_DEMO_PASSWORD=YOUR_UNIQUE_DEMO_USER_PASSWORD
```

URL-encode reserved characters in the database password (for example, `@` as
`%40`), or choose a local password without URL-reserved characters.

Set `CLAIMIQ_DEMO_PASSWORD` in `.env` before initializing the local database.
It is used for demo accounts created by the seeder. Choose a unique password;
do not use it for production accounts. Existing accounts are not assigned a
new password when the seeder runs again.

## 4. Create a Python virtual environment and install dependencies

Run these commands from the project root—the directory containing
`requirements.txt`.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this in that terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

If `.env` already exists, do not overwrite it; edit its `DATABASE_URL` instead.

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
```

If `.env` already exists, do not overwrite it. Edit it to add or update the
required settings. Then install the project dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Create tables and demo data

From the project root with the virtual environment active:

```bash
python -m app.init_db
```

This creates missing tables and adds demo accounts, policies, and a sample
claim when they do not already exist. It does not drop or reset the database.

Newly created demo accounts use the password set in `CLAIMIQ_DEMO_PASSWORD` in
`.env`:

| Username | Role |
|---|---|
| `admin` | admin |
| `reviewer` | reviewer |
| `adjuster1` through `adjuster5` | adjuster |
| `customer` | customer |
| `customer2` through `customer50` | customer |
| `support_agent` | support_agent |

The seed creates policies `POL-0001` through `POL-0050`; each sample policy is
assigned to its matching customer account (`POL-0001` belongs to `customer`,
`POL-0002` belongs to `customer2`, and so on). New claims are automatically
assigned to the active adjuster with the fewest open claims. Demo data and
passwords are for local development only.

**Policy ownership:** `POST /policies` is admin-only and requires `number`,
`holder`, `owner_id`, and optional `active`. The `owner_id` must identify an
active customer. Customers can submit claims only against their own policies.
When upgrading an existing local database, `python -m app.init_db` adds the
policy-owner column if needed and backfills ownership for known sample
policies. Other legacy policies are left unowned; assign each to the correct
customer before accepting claims against it.

## 6. Start the API locally

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open Swagger UI at:

- http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

In Swagger, click **Authorize** and sign in through `/auth/token`. The OAuth2
form expects a `username` and `password`. After sign-in, Swagger automatically
uses the returned bearer token for protected endpoints.

## 7. Suggested Swagger testing sequence

1. `POST /auth/token` — sign in as `admin` or `customer`.
2. `GET /users/me` — verify the logged-in user and role.
3. `GET /policies` — list policies.
4. `GET /users` as admin — find the intended customer's numeric `id`.
5. `POST /policies` as admin — create a policy with `number`, `holder`, and that customer's `owner_id`.
6. `POST /claims` as the policy's customer — create a claim using the policy's numeric `id`. A different customer should receive `403`.
7. `GET /claims` — verify role-based filtering.
8. `POST /claims/{claim_id}/assignment` as admin/reviewer — assign to the adjuster user ID if reassignment is needed.
9. `POST /claims/{claim_id}/status` as adjuster — move the claim to `under_review`.
10. `POST /claims/{claim_id}/status` as reviewer/admin — move it to `approved` or `denied`.
11. `GET /claims/{claim_id}/history` — verify status history.
12. `POST /claims/{claim_id}/notes` and `GET /claims/{claim_id}/notes`.
13. `GET /analytics/summary` as admin/reviewer.
14. `GET /audit` as admin.

Valid workflow:

```text
submitted -> under_review -> approved -> closed
                           -> denied ----> closed
```

An admin may override a transition only by providing a non-empty `justification`. Adjusters cannot make approval/denial decisions.

## 8. Run tests

Tests use an isolated in-memory SQLite database and do **not** connect to, delete, or modify your PostgreSQL database.

```bash
python -m pytest -v
```

## Troubleshooting

- `connection refused`: check `docker ps`, the container's published port, and the `DATABASE_URL` host port.
- `password authentication failed`: correct the database credentials in `.env`.
- `database "claimiq" does not exist`: create the database inside the running PostgreSQL server first.
- `ModuleNotFoundError`: activate `.venv` and run `pip install -r requirements.txt`.
- `Address already in use`: use another API port, e.g. `--port 8001`, and open the matching URL.

This is a local development starter, not production deployment configuration. Do not expose it publicly or use demo credentials for real data.


## Document Management and RAG

The existing Claims Management and Analytics endpoints remain in place. New endpoints:

- `POST /api/v1/documents` (also available at `/documents`) — Admin uploads a PDF/DOCX using multipart fields `policy_code`, `document_name`, `version`, `effective_from`, optional `replaces_document_id`, and `file`.
- `POST /api/v1/documents/{document_id}/process` (also `/documents/{document_id}/process`) — Admin extracts text, chunks it, generates Azure OpenAI embeddings, and indexes chunks in Azure AI Search.
- `GET /api/v1/documents` and `GET /api/v1/documents/{document_id}` (also available unversioned) — authorized operational roles inspect document metadata.
- `PATCH /api/v1/documents/{document_id}/activation` (also unversioned) — Admin activates/deactivates a processed document; send multipart field `active=true` or `active=false`.
- `POST /api/v1/ai/query` (also `/ai/query`) — authenticated Admin, Reviewer, Adjuster, or Support Agent asks a policy question. JSON: `{"question":"What is covered?","policy_code":"optional policy code"}`. The response contains an answer, document/page/chunk sources, response time, and status.

### Azure setup

1. Create a private Blob Storage container (default `policy-documents`).
2. Configure Azure AI Search and Azure OpenAI embedding/chat deployments.
3. Copy `.env.example` to `.env` and set the Azure endpoints and exact deployment names. Use Microsoft Entra ID or optional keys/connection string.
4. With Entra ID, run `az login` and grant the identity appropriate Blob data permissions, Search index/document permissions, and `Cognitive Services OpenAI User` on the Azure OpenAI resource.
5. Install dependencies with `pip install -r requirements.txt`.
6. Create the vector index with `python -m scripts.create_search_index`.
7. Create/update database tables with `python -m app.init_db`.
8. Start the API and use `/docs`.

Uploader/query identities come from the existing JWT, not client-supplied user IDs. Only Admin can upload/process/activate/deactivate documents. Retrieval filters to active chunks. Scanned PDFs without embedded text currently require OCR. Azure configuration is only needed for RAG endpoints; Claims and Analytics do not initialize Azure clients.

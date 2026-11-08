# RepoPulse

Track public GitHub repositories, keep a history of how their metrics change,
and export that history as CSV for analysis in BigQuery Sandbox.

Add a repository by owner and name, and RepoPulse validates it against the
GitHub REST API, stores its current metadata, and appends an immutable snapshot
of its stars, forks, open issues, watchers and language breakdown on every
successful sync. Failed and rate-limited syncs are recorded without touching the
metric history.

> **Status: unverified.** The code in this repository has never been run. No
> dependencies were installed, no migration was applied, no test was executed and
> nothing was deployed. Treat the setup steps below as the intended path, not as
> a verified one, and expect to fix issues on the first run.

## Features

- **Dashboard** — tracked repository count, aggregate stars and forks from the
  latest known values, recently synced list, searchable repository table, and a
  useful empty state before anything is added.
- **Add a repository** — validated owner and name, existence checked against
  GitHub, duplicates rejected case-insensitively, first sync run immediately.
- **Repository details** — description, owner, URL, primary language, current
  metrics, a stars/forks line chart over the stored snapshots, the latest
  language breakdown, and recent sync attempts.
- **Manual sync** — a **Sync now** action per repository. The backend does all
  GitHub calls; the browser never talks to GitHub directly.
- **Safe failures** — rate limits, timeouts and 5xx responses are surfaced
  clearly and recorded as failed sync runs. No snapshot is written from
  incomplete data.
- **CSV exports** — flat `repository_snapshots.csv` and `language_stats.csv`
  with stable headers and ISO-8601 UTC timestamps.
- **API docs and health** — FastAPI's OpenAPI UI at `/docs` and a `GET /health`
  that reports database connectivity without exposing credentials.

Out of scope in this release: authentication, multi-user support, private
repositories, webhooks, background workers and scheduled syncs.

## Architecture

```mermaid
flowchart TD
    U[User] -->|Uses dashboard| FE[React + Vite frontend]
    FE -->|HTTPS REST requests| API[FastAPI backend]
    API --> VAL[Validate owner and repository name]
    VAL -->|Fetch public repository data| GH[GitHub REST API]
    GH -->|Repository metadata and languages| SVC[Repository sync service]
    SVC -->|Save latest metadata, snapshot, languages, sync result| DB[(PostgreSQL)]
    DB -->|Repository data and history| API
    API -->|JSON response| FE
    FE -->|Request CSV download| API
    API -->|Generate CSV exports| CSV[CSV files]
    CSV -->|Manual batch upload| BQ[BigQuery Sandbox]
```

Layering, outermost in:

| Layer | Path | Responsibility |
|---|---|---|
| Routers | `backend/app/api/v1/` | Input validation, status codes, response schemas |
| Services | `backend/app/services/` | Sync rules, transactions, CSV generation |
| GitHub client | `backend/app/services/github.py` | The only code that calls GitHub; raises typed errors |
| Models | `backend/app/models/` | SQLAlchemy schema with cascades and constraints |

A sync writes a `sync_run` row as `in_progress` **before** contacting GitHub, so
an interrupted sync leaves evidence. The snapshot, language rows and repository
update are committed together only after both GitHub calls succeed.

## Data model

```mermaid
erDiagram
    REPOSITORY ||--o{ REPOSITORY_SNAPSHOT : has
    REPOSITORY ||--o{ SYNC_RUN : records
    REPOSITORY_SNAPSHOT ||--o{ LANGUAGE_STAT : contains

    REPOSITORY {
        uuid id PK
        string owner
        string name
        string full_name UK
        string html_url
        text description
        string primary_language
        int stars_count
        int forks_count
        int open_issues_count
        int watchers_count
        datetime github_created_at
        datetime last_synced_at
        datetime created_at
        datetime updated_at
    }

    REPOSITORY_SNAPSHOT {
        uuid id PK
        uuid repository_id FK
        int stars_count
        int forks_count
        int open_issues_count
        int watchers_count
        datetime captured_at
    }

    LANGUAGE_STAT {
        uuid id PK
        uuid snapshot_id FK
        string language
        bigint bytes_of_code
    }

    SYNC_RUN {
        uuid id PK
        uuid repository_id FK
        string status
        datetime started_at
        datetime finished_at
        int records_processed
        text error_message
    }
```

- `repository.full_name` is `owner/name`, unique, with a `lower(full_name)`
  unique index backing case-insensitive duplicate detection.
- `repository_snapshot` is append-only; rows are never updated.
- `language_stat` belongs to a snapshot, not a repository, so language mixes stay
  comparable across syncs. Unique on `(snapshot_id, language)`.
- `sync_run.status` is `in_progress`, `success` or `failed`, enforced by a check
  constraint. Error messages are sanitised and truncated; tokens are never
  stored.
- Deleting a repository cascades to its snapshots, language rows and sync runs.

**On watchers:** GitHub's REST API returns `watchers_count` as a copy of
`stargazers_count` and exposes true subscribers as `subscribers_count`. This app
stores and labels `watchers_count` as specified; it is not a separate audience
metric from stars.

## API

All application endpoints sit under `/api/v1`. Errors share one JSON shape:
`{"detail": "...", "code": "..."}`.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API and database health check |
| `GET` | `/api/v1/repositories` | List tracked repositories; optional `q` search |
| `POST` | `/api/v1/repositories` | Validate and add a public repository, then sync it |
| `GET` | `/api/v1/repositories/{id}` | Repository details and latest language data |
| `POST` | `/api/v1/repositories/{id}/sync` | Trigger a manual sync and save a snapshot |
| `GET` | `/api/v1/repositories/{id}/snapshots` | Historical metrics, oldest first |
| `GET` | `/api/v1/repositories/{id}/sync-runs` | Recent sync attempts and statuses |
| `DELETE` | `/api/v1/repositories/{id}` | Delete the repository and dependent records |
| `GET` | `/api/v1/analytics/summary` | Aggregate dashboard metrics |
| `GET` | `/api/v1/exports/repository-snapshots.csv` | Flat CSV of snapshots |
| `GET` | `/api/v1/exports/language-stats.csv` | Flat CSV of language statistics |

Status codes: `404` unknown repository ID or unavailable GitHub repository,
`409` duplicate, `422` invalid input, `429` GitHub rate limit, `502`/`503`
upstream failure.

Example add request:

```json
{ "owner": "fastapi", "name": "fastapi" }
```

Interactive docs: <http://localhost:8000/docs>.

## Local setup

### 1. Create the database

1. Sign in at <https://supabase.com> and create a free project.
2. Open **Project settings → Database → Connection string → URI**.
3. Copy the URI and substitute your database password.

A local PostgreSQL 15+ instance works equally well — point `DATABASE_URL` at it
instead. The app accepts `postgresql://`, `postgres://` and
`postgresql+psycopg://` and normalises the driver itself.

### 2. Configure the backend

```bash
cd backend
cp ../.env.example .env
```

Edit `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres
GITHUB_TOKEN=
FRONTEND_ORIGIN=http://localhost:5173
```

`GITHUB_TOKEN` is optional. Without it GitHub allows 60 unauthenticated requests
per hour per IP, which is enough for light use; with a token the limit is 5,000.

### 3. Install, migrate and run the backend

```bash
cd backend
python -m venv .venv
```

```bash
source .venv/bin/activate
```

On Windows PowerShell use `.venv\Scripts\Activate.ps1` instead.

```bash
pip install -r requirements.txt
```

```bash
alembic upgrade head
```

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Run the frontend

```bash
cd frontend
cp .env.example .env
```

```bash
npm install
```

```bash
npm run dev
```

The app runs at <http://localhost:5173> and talks to the backend at the
`VITE_API_BASE_URL` set in `frontend/.env`.

### 5. Tests and production build

```bash
cd backend && DATABASE_URL=sqlite+pysqlite:///./test.db pytest -q
```

```bash
cd frontend && npm run build
```

Backend tests run against SQLite with the GitHub API mocked at the HTTP
transport, so they need neither a database server nor network access.

## Deployment

### Backend on Render

1. Create a **Web Service** from this repository with root directory `backend`.
2. Build command: `pip install -r requirements.txt`
3. Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Environment variables: `DATABASE_URL`, `GITHUB_TOKEN` (optional), and
   `FRONTEND_ORIGIN` set to your deployed frontend origin.

A `Dockerfile` is included if you would rather deploy the backend as a container.
Docker is not needed for local development.

### Frontend on Render Static Site

1. Create a **Static Site** with root directory `frontend`.
2. Build command: `npm install && npm run build`
3. Publish directory: `dist`
4. Environment variable: `VITE_API_BASE_URL` pointing at the deployed backend.
5. Add a rewrite rule from `/*` to `/index.html` so client-side routes resolve.

### Production CORS

`FRONTEND_ORIGIN` accepts a comma-separated list and is applied verbatim — no
wildcard origin is used in any environment. Set it to exactly the origins that
should reach the API.

## Analytics

See [`analytics/bigquery/README.md`](analytics/bigquery/README.md) for loading
the CSV exports into BigQuery Sandbox, plus
[`repository_trends.sql`](analytics/bigquery/repository_trends.sql) and
[`language_popularity.sql`](analytics/bigquery/language_popularity.sql).

BigQuery is a destination for exported history, never a runtime dependency.

## Security notes

- Secrets come from environment variables only; `.env` is git-ignored and
  `.env.example` holds placeholders.
- `GITHUB_TOKEN` stays server-side and is never sent to the browser.
- Owner and name are pattern-validated, so the backend cannot be pointed at an
  arbitrary host.
- All queries go through SQLAlchemy parameters; no SQL is built by string
  concatenation.
- Logs are filtered for credential-like keys, and sync errors are sanitised
  before they are stored.

## Known free-tier limitations

Free-tier quotas change; these were the terms at the time of writing.

- **Render free web services spin down when idle.** The first request after a
  quiet period can take 30–60 seconds while the service wakes.
- **Supabase free projects pause after a period of inactivity** and must be
  resumed from the dashboard before the API can reach the database. `/health`
  reports `degraded` while that is the case.
- **Unauthenticated GitHub requests are limited to 60 per hour per IP.** Set
  `GITHUB_TOKEN` if you sync often.
- **BigQuery Sandbox tables expire after 60 days** and no billing-backed
  features (streaming, scheduled queries) are available.

None of these services promise production-grade availability on a free plan.

## Screenshots

Add screenshots here once the app has been run locally:

- `docs/dashboard.png` — dashboard with KPI cards and the tracked list
- `docs/repository-detail.png` — history chart and language breakdown
- `docs/analytics.png` — the BigQuery help page

## Repository layout

```text
repopulse/
├── backend/      FastAPI app, SQLAlchemy models, Alembic migrations, tests
├── frontend/     React + Vite dashboard
├── analytics/    BigQuery Sandbox instructions and SQL
├── .github/      CI workflow
└── PLAN.md       Design notes, task list and assumptions
```

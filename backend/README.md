# Backend

FastAPI service for DM Assistant. It owns conversations, retrieval, ingestion, and
every model call. The SPA in `frontend/` talks to it over HTTP; streaming uses
[AG-UI](https://docs.ag-ui.com/) over SSE ([ADR-0009](../docs/adr/adr-0009-ag-ui-protocol.md)).

## What runs today

A Research chat turn, stored in PostgreSQL, answered by a fake model.

- `POST /api/v1/campaigns/{cid}/conversations` — start a conversation (`mode: research`)
- `GET /api/v1/campaigns/{cid}/conversations/{id}/messages` — history
- `POST /api/v1/campaigns/{cid}/conversations/{id}/messages` — send a message; response is
  `text/event-stream` (`RunStarted`, text deltas, `RunFinished`)

The reply comes from `adapters/llm/fake.py`. Conversations live in PostgreSQL when
`DATABASE_URL` is set, and in memory (with a warning in the log) when it is not. A
conversation must belong to an existing campaign; there is no campaign API yet, so local
development seeds one, `ashfall`. Auth, Claude, Ollama, and retrieval are not wired yet.
The HTTP surface is specified in [docs/api-contract.md](../docs/api-contract.md).

## Architecture

Hexagonal, as in [docs/folder-structure.md](../docs/folder-structure.md). Dependencies
point inward. The conversation rules do not import FastAPI, a database, or a model SDK.

```
entrypoints  →  application  →  ports  ←  adapters
                     │            │
                     └──── domain ┘
composition.py is the only module that names both sides of a port
```

| Package | Role | Present now |
|---------|------|-------------|
| `app/domain/` | Entities and values. Stdlib only | `assistant/` — `Conversation`, `Message`, `Mode` |
| `app/ports/` | Protocols the use cases depend on | `ConversationRepo`, `LLMProvider`, `Clock` |
| `app/application/` | Use cases. Receives ports, never an adapter | `StartConversation`, `RunAssistantTurn`, `ListMessages` |
| `app/adapters/` | Implementations of ports | SQLAlchemy and in-memory repos, fake LLM, clocks |
| `app/entrypoints/http/` | Driving adapter. Routers, Pydantic schemas, SSE, error mapping | Assistant routes |
| `app/composition.py` | Wires ports to adapters and hangs use cases on `app.state` | `build_app()` |
| `app/config.py` | Runtime settings from the environment | `DATABASE_URL` |

`import-linter` (contracts in `pyproject.toml`) and `tests/architecture/` fail the build
if a layer imports inward the wrong way, if a provider SDK is imported outside
`app/adapters/llm/` (BND-002, [ADR-0006](../docs/adr/adr-0006-llm-gateway.md)), or if
SQLAlchemy, psycopg, or Alembic is imported outside `app/adapters/persistence/sqlalchemy/`.

## Develop

Python 3.11 or newer.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

ruff check app tests
lint-imports
pytest
```

Application tests use the in-memory repository and the fake LLM, so they need no
database. The repository contract tests in `tests/adapters/` run against both the
in-memory repo and PostgreSQL; the PostgreSQL half is skipped locally unless
`TEST_DATABASE_URL` is set (see [Run the Postgres tests](#run-the-postgres-tests)), and
fails rather than skips in CI.

## Run both apps

From the repository root, `docker compose up --build`. See the
[root README](../README.md#run-it-with-docker) for URLs and everyday commands. The
backend container runs `alembic upgrade head`, seeds the `ashfall` campaign, then starts
uvicorn.

## Database

PostgreSQL 16 with the `pgvector` extension, in the `db` service of `compose.yaml`
([ADR-0013](../docs/adr/adr-0013-postgres-for-local-and-hosted.md)). Its data lives in
the `pgdata` Docker volume, so it survives `docker compose down` and container restarts.

### What to install

| Need | Install | Notes |
|------|---------|-------|
| Docker runtime (required) | [OrbStack](https://orbstack.dev/) or [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Runs Postgres. Check with `docker compose version` |
| A GUI to browse tables (pick one) | [TablePlus](https://tableplus.com/), [DBeaver](https://dbeaver.io/) (free), [Postico](https://eggerapps.at/postico2/) (macOS) | All connect with the details below |
| `psql` on your machine (optional) | `brew install libpq`, then `brew link --force libpq` | Or skip it and use `psql` inside the container |

### Connect

Start only the database if that is all you need:

```bash
docker compose up -d db
```

| Field | Value |
|-------|-------|
| Host | `localhost` |
| Port | `5432` |
| User | `dm` |
| Password | `dm` |
| Database | `dm_assistant` |
| URL | `postgresql://dm:dm@localhost:5432/dm_assistant` |

These credentials are for local development only. Inside compose, the backend reaches
the database as `db:5432`, not `localhost` — inside a container, `localhost` is the
container itself.

A shell on the database, without installing anything:

```bash
docker compose exec db psql -U dm -d dm_assistant
```

Things worth typing there:

```sql
\dt                                   -- list tables
\d message                            -- one table's columns, indexes, foreign keys
SELECT * FROM alembic_version;        -- which migration the schema is at
SELECT id, campaign_id, mode, started_at FROM conversation ORDER BY id DESC LIMIT 10;
SELECT role, mode, left(content, 60) FROM message WHERE conversation_id = 1 ORDER BY id;
\q                                    -- quit
```

### Run the backend outside Docker against it

```bash
docker compose up -d db
cd backend && source .venv/bin/activate
export DATABASE_URL=postgresql+psycopg://dm:dm@localhost:5432/dm_assistant
alembic upgrade head
python -m app.adapters.persistence.sqlalchemy.seed
uvicorn app.composition:build_app --factory --reload
```

`postgresql+psycopg://` tells SQLAlchemy which driver to use; GUI clients take the plain
`postgresql://` form.

### Change the schema

The tables are defined in `app/adapters/persistence/sqlalchemy/tables.py`. Every change
to them needs a migration in `.../migrations/versions/` — a schema change must never
require deleting a campaign (ADR-0013 IMP-002).

```bash
alembic revision --autogenerate -m "add document table"   # drafts a migration; read it
alembic upgrade head                                      # apply
alembic downgrade -1                                      # undo the last one
```

Autogenerate compares `tables.py` with the live database. Review what it writes:
it cannot detect renames, and data changes are yours to add. `tests/adapters/test_migrations.py`
fails if `tables.py` and the migrations disagree, and every migration is run down and up
again in the test suite.

### Run the Postgres tests

The tests empty the tables they use. Point them at a separate database, never at
`dm_assistant`:

```bash
docker compose exec db createdb -U dm dm_test
export TEST_DATABASE_URL=postgresql+psycopg://dm:dm@localhost:5432/dm_test
pytest -rs
```

### Start over

```bash
docker compose down -v      # -v also deletes the pgdata volume: every row is gone
```

## Deployment (later)

Two modes, same code and the same database engine
([ADR-0013](../docs/adr/adr-0013-postgres-for-local-and-hosted.md), PRIN-004). Neither is
a migration of the other.

**Local.** PostgreSQL runs beside the API — a container or an installed service
(ADR-0013 IMP-001). There is no SQLite fallback. Uploaded files go to local disk through
the `FileStore` port. Ollama can serve the chat model with no outbound API; embeddings still call Voyage, so uploading needs the network and search without it is keyword-only ([ADR-0016](../docs/adr/adr-0016-voyage-embeddings.md)).

**Hosted.** The same PostgreSQL, as a managed service or self-hosted on the operator's
hardware. The backend image runs `alembic upgrade head` before it serves and needs
`DATABASE_URL`. Uploaded files stay behind `FileStore`: disk or an object store. Which
object store is a deployment note, not an ADR (ADR-0013 IMP-005). Claude is reached
through the LLM Gateway; switching providers is settings, not a redeploy
([ADR-0006](../docs/adr/adr-0006-llm-gateway.md)).

In both modes, schema changes go through versioned migrations. Ingestion runs as a
worker (`entrypoints/worker/`), separate from the request process, so document processing
does not block a session (PRIN-003).

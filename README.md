# Quillbert

An in-session workspace for tabletop RPG game masters: campaign material on the left,
an assistant grounded in that material on the right.

Upload your rulebooks, modules, and notes; they are extracted and indexed. During a
session, ask questions in natural language and get answers drawn from **your** books,
with sources shown. Around that sits the workspace for running a game — NPCs, players,
factions, a quest log, session records, and a knowledge graph of how everyone connects.

## Status

Live at **https://quillbert.app** (hosted on Mikrus behind Cloudflare; see
[docs/deployment.md](docs/deployment.md)). Sign-in works through Supabase Auth, email and
password or Google. The frontend workspace shell is in progress. The backend runs a Research
chat turn against a fake LLM, with conversations stored in PostgreSQL (no provider SDKs yet).
The API docs (Swagger UI) are served locally only, never on the public site.

Start with [docs/README.md](docs/README.md).

## Run it

**Prerequisites**

- A Docker runtime with Compose v2 — [OrbStack](https://orbstack.dev/) on macOS, or
  [Docker Desktop](https://www.docker.com/products/docker-desktop/). Check with
  `docker compose version`. Python and Node run inside the containers.
- A **Supabase** project for the database. There is no local Postgres on purpose: you
  develop against Supabase Cloud, so local and hosted share the same Auth, RLS, and
  pgvector and nothing drifts between them
  ([ADR-0018](docs/adr/adr-0018-hosted-first-local-v2.md),
  [ADR-0020](docs/adr/adr-0020-supabase-auth.md)). Use your own or a dedicated dev
  project — local runs write to whatever database `DATABASE_URL` names.

**1. Configure.** Copy the template and fill in the Supabase values:

```bash
cp .env.example .env
# DATABASE_URL = the Supabase *session pooler* string (port 5432),
#   scheme rewritten to postgresql+psycopg://  (Supabase → Settings → Database)
# VITE_SUPABASE_URL, VITE_SUPABASE_PUBLISHABLE_KEY = Supabase → Settings → API
#   (public values; the login screen and token verification need them)
# ENABLE_API_DOCS=true is already in the template: it turns on /docs and /redoc locally
```

**Sign-in locally.** In the Supabase dashboard (Authentication → URL Configuration), add
`http://localhost:8080` and `http://localhost:5173` to **Redirect URLs**. Email and password
sign-up works as soon as the project allows it; **Continue with Google** needs the Google
provider enabled (Authentication → Sign In / Providers) with an OAuth client — see
[docs/setup-guide.md](docs/setup-guide.md). Without the two `VITE_SUPABASE_*` values the
login page stays blank.

**2. Apply the schema** to that database once — migrations no longer run on container
boot ([docs/setup-guide.md](docs/setup-guide.md); in the hosted deploy this is the
**Migrate database** GitHub Action):

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL='postgresql+psycopg://…'            # same value as in .env; alembic reads it
alembic upgrade head
cd ..
```

**3. Run both apps:**

```bash
docker compose up --build
```

The first build takes a few minutes. When the logs settle:

| URL | What |
|-----|------|
| http://localhost:8080 | The app. nginx serves the SPA and proxies `/api` to the backend |
| http://localhost:8000/docs | The API contract: OpenAPI (Swagger UI), with "Try it out" |
| http://localhost:8000/redoc | The same contract as a reference page; raw JSON at `/openapi.json` |

The API docs live on the backend port only and only while `ENABLE_API_DOCS=true`. The nginx
on :8080 (and the public site) serves just the SPA and `/api/`, and deployed environments
leave the variable unset.

Everyday commands:

| Command | Does |
|---------|------|
| `docker compose up --build -d` | Start in the background (`-d`); rebuild after code changes |
| `docker compose logs -f backend` | Follow one service's logs |
| `docker compose ps` | What is running, and whether it is healthy |
| `docker compose down` | Stop and remove the containers |

Data lives in Supabase, so it survives restarts and a `docker compose down` never touches
it.

## Working on one app without Docker

Most work needs neither containers nor a database: the backend falls back to an in-memory
store (with a log warning) when `DATABASE_URL` is unset, and the assistant replies from a
fake LLM until a provider is wired.

**Backend** — Python 3.11+:

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check app tests && lint-imports && pytest          # checks + tests; need no database
uvicorn app.composition:build_app --factory --reload    # http://localhost:8000
```

Export `DATABASE_URL` first if you want conversations persisted to Supabase; leave it
unset for a throwaway in-memory run. Export `SUPABASE_URL` (the same value as
`VITE_SUPABASE_URL`) so the API can verify sign-in tokens; without it every authenticated
route answers 401. `export ENABLE_API_DOCS=true` turns on `/docs` and `/redoc`. Schema
changes and the Postgres contract tests are in [backend/README.md](backend/README.md).

**Frontend** — Node 22 (the image builds on `node:22-alpine`):

```bash
cd frontend
npm install
cat > .env.local <<'EOF'
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
EOF
npm run dev         # http://localhost:5173, Vite with hot reload
npm run build       # production build   ·   npm run lint runs oxlint
```

Vite reads `frontend/.env.local` (gitignored), not the root `.env`. The dev server has no
`/api` proxy yet, and the UI does not call the backend yet, so sign-in is the part you can
exercise: use Docker (`:8080`) when you need the full path through nginx.

## Documentation

| Document | What it answers |
|----------|-----------------|
| [Product brief](docs/product-brief.md) | What we are building, for whom, and why |
| [MVP scope](docs/mvp-scope.md) | What ships in v1 and what explicitly does not |
| [Data model](docs/data-model.md) | Entities, relationships, and storage |
| [Architecture](docs/architecture.md) | System shape, stack, and boundaries |
| [Folder structure](docs/folder-structure.md) | Folder layout and dependency rules for both apps |
| [Design spec](docs/design/overview.md) | Screens, layout, and interaction behaviour |
| [Design tokens](docs/design/reference.md) | Colors, type, spacing, radii, shadows |
| [API contract](docs/api-contract.md) | HTTP surface between frontend and backend |
| [Roadmap](docs/roadmap.md) | Delivery phases and acceptance gates |
| [ADRs](docs/adr/) | Architectural Decision Records |

## Planned stack

| Layer | Choice |
|-------|--------|
| Frontend | React 19 + TypeScript + Vite, React Router v7 |
| Styling | CSS Modules over CSS custom properties — **no Tailwind** |
| Components | Radix UI primitives, documented in Storybook |
| State | TanStack Query (server) + Zustand (UI) |
| Backend | Python 3.11+ / FastAPI |
| Storage | PostgreSQL (Supabase Cloud) — `tsvector` + `pgvector` |
| Extraction | PyMuPDF, pdfplumber — deterministic, no generative model |
| AI | OpenRouter gateway, zero-retention providers only ([ADR-0019](docs/adr/adr-0019-openrouter-privacy-routing.md)) |

See [ADR-0001](docs/adr/adr-0001-react-vite-spa.md) for the stack rationale.

## Design

**▶ [Open the interactive design](https://claude.ai/code/artifact/a7d4de30-0826-4747-b295-a584fe6f0f28)**

The running prototype, and the source of truth for layout, tokens, and interaction. Click
through it — login, campaign picker, the workspace views, the graph, and the mobile shell
below 900px. Interaction is most of what this design specifies, so a screenshot would
convey little of it.

It is a **reference, not production code**: values are transcribed into
[design tokens](docs/design/reference.md) and markup is rebuilt with the project's own
primitives.

## Architecture at a glance

**▶ [Open the architecture board](https://miro.com/app/board/uXjVHrcVIJQ=/)**

A Miro board with the system shape and both data flows — ingestion and retrieval —
mirroring [docs/architecture.md](docs/architecture.md). Useful for walking someone through
the two boundaries that define this system: extraction never calls a model, and every
model call goes through one gateway.

## Folder structure

Two applications, one dependency direction: volatile things at the edge, stable things at
the centre, every arrow pointing inward. Full layout and the enforced import rules are in
[docs/folder-structure.md](docs/folder-structure.md).

**Backend — hexagonal (ports and adapters).** The domain knows nothing about the world.

```
backend/app/
├── domain/          # entities, value objects, invariants. Pure — no I/O, no framework.
├── ports/           # interfaces the domain declares: repositories, search, llm,
│                    #   extraction, files, clock
├── application/     # use cases. Orchestrates domain + ports; never imports an adapter.
├── adapters/        # the outside world — the only place SDKs are imported
│   ├── persistence/ #   sqlalchemy/ + memory/ (the fast test double)
│   ├── search/      #   hybrid/ + memory/
│   ├── llm/         #   claude, ollama, fake, prompts per mode
│   └── extraction/  #   pymupdf, ocr
├── entrypoints/     # driving adapters: http/, worker/, cli/. Transport only.
└── composition.py   # the ONLY module wiring ports to adapters
```

```
entrypoints ──→ application ──→ ports ←── adapters
                     │           │          │
                     └───────────┴──→ domain ┘
```

**Frontend — domain-oriented split.** Bounded contexts with published interfaces.

```
frontend/src/
├── app/         # router, providers, shell
├── domains/     # campaign · cast · world · adventure · library · graph · assistant
│   └── <ctx>/   #   model/ · api/ · components/ · store.ts · index.ts ← public API
├── screens/     # routed pages. Compose domains, own no logic.
├── ui/          # design-system primitives. Knows no domain.
├── styles/      # tokens.css, reset, global
└── lib/         # http client, SSE reader, utils
```

**One rule does most of the work:** a domain may only be imported through its `index.ts`.
Deep imports are what turn a domain split into a ball of mud. On Python, `import-linter`
fails the build on a violation. On TypeScript the rules are not enforced by a tool yet;
see [Enforcement](docs/folder-structure.md#enforcement) for what is and is not checked.

## Two ideas worth knowing up front

**Extraction never uses a language model.** Parsing is deterministic, so the index
contains only text that is genuinely in your documents. That is what makes citations
trustworthy. Models are used at query time only.
See [ADR-0002](docs/adr/adr-0002-deterministic-extraction.md).

**Infrastructure is deferred with a trigger — and the trigger can fire.** v1 deferred both
a server database and a vector store, each with a written revisit condition. When the
product's target grew to include hosted deployment, ADR-0003's own condition was met and
both decisions were re-made: one PostgreSQL for local and hosted
([ADR-0013](docs/adr/adr-0013-postgres-for-local-and-hosted.md)), and hybrid keyword +
vector retrieval in that same database
([ADR-0014](docs/adr/adr-0014-hybrid-retrieval.md)). The superseded records are kept —
the premise changed, not the analysis.

# Setup guide (finishing the stack)

A runbook for wiring the deployment the first time. The *architecture* (what runs where)
lives in [deployment.md](deployment.md); this is the step-by-step and, most importantly,
**where each variable goes**.

The stack: **Supabase Cloud** (Postgres + pgvector + Auth + Storage), **`ted106`** (the app
host, via the self-hosted Openship control plane on the maintainer's Mac), **Cloudflare R2**
(files), **OpenRouter** (LLM).

## Variable placement — the one table to get right

The rule: **public** values (safe in the browser bundle) go in **GitHub *variables*** and the
frontend build; **secrets** go in **GitHub *secrets*** and the backend's runtime env, never
in the frontend and never committed. Supabase data is protected by Row-Level Security, not by
hiding the publishable key — that's why it's public.

| Variable | Sensitivity | GitHub | Openship env | Frontend build | Where to get it |
|----------|-------------|--------|--------------|----------------|-----------------|
| `SUPABASE_URL` | **public** | **Variable** | ✓ | ✓ as `VITE_SUPABASE_URL` | Supabase → Settings → API (Project URL) |
| `SUPABASE_PUBLISHABLE_KEY` | **public** | **Variable** | ✓ | ✓ as `VITE_SUPABASE_PUBLISHABLE_KEY` | Supabase → Settings → API (publishable / anon) |
| `OPEN_ROUTER_API_KEY` | **secret** | **Secret** | ✓ (backend) | ✗ | openrouter.ai → Keys |
| `DATABASE_URL` | **secret** | **Secret** (for the migrate Action) | ✓ (backend) | ✗ | Supabase → Settings → Database (see note) |
| `SUPABASE_SERVICE_ROLE_KEY` | **secret** | — | ✓ backend *(optional)* | ✗ | Supabase → Settings → API — only if the backend calls Supabase's Auth-admin or Storage APIs; **not needed** with direct Postgres + JWKS + R2 |
| `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_ENDPOINT` | **secret** | — | ✓ (backend) | ✗ | Cloudflare → R2 → API tokens |
| `FILE_STORE_PATH` | config | — | set by compose (`/data/files`) | ✗ | Where uploads live until the R2 adapter ships; a named volume (`files`) |
| `MAX_UPLOAD_MB` | config | — | optional (default 200) | ✗ | Upload size limit. Behind Cloudflare Free the real cap is 100 MB |

**No JWT secret.** This project uses asymmetric signing keys, so there's no shared secret to
store — see [Auth tokens](#auth-tokens-verified-via-jwks-no-secret) below.

**So, directly:** `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` are GitHub **variables**
(public); `OPEN_ROUTER_API_KEY` is a GitHub **secret**.

> **`DATABASE_URL` gotcha (two of them).** Use the **Session pooler** connection string
> (port `5432`) — alembic runs DDL, which the transaction pooler (`6543`) does not support
> well. And change the scheme from `postgresql://…` to **`postgresql+psycopg://…`** — the
> backend uses the psycopg driver.

## Auth tokens: verified via JWKS, no secret

This project uses Supabase's **asymmetric JWT signing keys**, so there is **no shared JWT
secret to store or paste anywhere**. The backend verifies Supabase-issued tokens against the
public JWKS endpoint, derived from `SUPABASE_URL`:

```
<SUPABASE_URL>/auth/v1/.well-known/jwks.json
```

Those are verify-only public keys, so nothing secret is involved — consistent with
[ADR-0020](adr/adr-0020-supabase-auth.md) IMP-001 ("JWKS / shared secret"). The legacy shared
JWT secret (Settings → JWT Keys) is deprecated for new projects; don't use it.

## Database migrations run in CI, not on app boot

Migrations are applied by the **`Migrate database`** GitHub Action
([.github/workflows/migrate.yml](../.github/workflows/migrate.yml)) — a dedicated, gated
step. The backend container no longer runs `alembic upgrade head` on boot; it only serves.

- **Alembic in the repo is the single source of truth** for the schema
  ([ADR-0013](adr/adr-0013-postgres-for-local-and-hosted.md) IMP-002). Do **not** apply
  schema through the Supabase dashboard or MCP — that creates a parallel history that fights
  alembic.
- The Action runs on push to `main` when migrations/alembic/deps change, and on manual
  **Run workflow** (`workflow_dispatch`). It needs the `DATABASE_URL` secret.
- **Ordering:** run migrations **before** the app deploy that depends on them. Easiest on a
  single maintainer: let the Action go green, then deploy the app in Openship. (Gate it
  further by adding required reviewers to the `production` environment in repo settings.)

## Runbook

**1. Supabase (dashboard)**
- Confirm `pgvector` is enabled (`create extension if not exists vector with schema extensions;`).
- Collect the values from the table above (Settings → API / Database).
- For login: Auth → Providers → enable **Google** (add the OAuth client ID/secret and the
  redirect URL Supabase shows); Auth → Emails for password reset. (Needed before auth works;
  can wait if you're only testing the API.)

**2. GitHub (repo → Settings)**
- **Secrets and variables → Actions → Variables:** add `SUPABASE_URL`,
  `SUPABASE_PUBLISHABLE_KEY`.
- **Secrets and variables → Actions → Secrets:** add `DATABASE_URL` (session-pooler,
  `postgresql+psycopg://…`), `OPEN_ROUTER_API_KEY`. (Add others only if a workflow needs
  them.)

**3. Run the first migration**
- Actions → **Migrate database** → **Run workflow** (on `main`). It applies the current
  schema to Supabase. Confirm it's green before deploying the app.

**4. Openship (deploy the app to `ted106`)**
- Create a project for the repo (two services: `backend` and `frontend`, each from its
  `Dockerfile`), targeting the `mikrus ted106` server.
- Set the project **env**:
  - backend: `DATABASE_URL`, `SUPABASE_URL` (verifies login tokens; without it every
    request is 401), `OPEN_ROUTER_API_KEY`, the four `R2_*` (plus
    `SUPABASE_SERVICE_ROLE_KEY` only if you call Supabase's Auth-admin/Storage APIs) — set
    these as secrets in Openship (not committed). No JWT secret — tokens verify via JWKS.
  - frontend build: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` (public; passed as
    Docker build args — the login screen throws at startup without them).
- Public endpoint: override the service ports in Openship to bind IPv6 only
  (`openship service update frontend <file>` with `{"ports":[":::80:80"]}`, backend
  `{"ports":[":::30106:8000"]}`; `[::]:…` is not parsed, use `:::`; one binding per container
  port). Then, in Cloudflare, add an `AAAA` record `@` → the server's IPv6 (proxied) and set
  SSL/TLS to **Flexible** (the origin serves plain HTTP; **Full** gives a 521). Optional
  Mikrus subdomains via the `domains` tool: `quillbert` → port `80`, `quillbertapi` → port
  `30106`, zone `mikrus.dev`. Keep nothing else public; Supabase is reached as an external
  HTTPS service.
- Deploy and check health (see **Check it's live** below).
- **Deploy on merge:** `.github/workflows/deploy.yml` runs `openship deploy` after CI is
  green on `main`. Openship lives on the Mac, so the job needs a **self-hosted runner on
  the Mac** labelled `openship` (repo Settings → Actions → Runners → New self-hosted
  runner, macOS; add the label `openship`; run it as a service). The runner user must be
  logged in to Openship. Never let it run PR code — the workflow triggers on `main` only.

**Supabase dashboard, once (Authentication)**
- URL Configuration → **Site URL** and **Redirect URLs**: `https://quillbert.app` (plus
  `https://quillbert.app/**`, and `http://localhost:8080` for local compose). Sign-in with Google and password-reset links
  return there; anything not listed is refused.
- Providers → **Google**: enable it with a Google OAuth client whose redirect URI is
  `<SUPABASE_URL>/auth/v1/callback`.

**Check it's live**
- Frontend: `https://quillbert.app/` → 200 (the SPA).
- Backend: `https://quillbertapi.mikrus.dev/openapi.json` → 200. Swagger UI and ReDoc are
  off in production (`/docs` and `/redoc` → 404 there): the `ENABLE_API_DOCS` variable is
  unset, and the frontend nginx does not proxy `/docs`, `/redoc` or `/openapi.json`. The API
  itself is reachable through the proxy at `https://quillbert.app/api/…`; without a token it
  answers 401.

**5. Local development**
- A gitignored `.env` with the **public** `VITE_*` values and a local/dev `DATABASE_URL`.
  Apply migrations locally with `alembic upgrade head` (from `backend/`) — the app no longer
  does it on start.

## Notes

- Supabase free tier: ~500 MB database, 1 GB storage, and it **pauses after ~7 days idle**
  (one click to resume) — expect that on a tool used only on session nights.
- Openship's control plane runs on the Mac; deploys/management need it on, the running app
  on `ted106` does not.

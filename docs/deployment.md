# Deployment

How v1 runs. v1 is **hosted-first** ([ADR-0018](adr/adr-0018-hosted-first-local-v2.md));
running the full stack on a game master's own machine is a v2 goal.

Which host, database, and file store sit behind the architecture is a **deployment choice,
not an ADR** — the decision records fix the *ports* (PostgreSQL per
[ADR-0013](adr/adr-0013-postgres-for-local-and-hosted.md); the `FileStore` object store per
[ADR-0013](adr/adr-0013-postgres-for-local-and-hosted.md) IMP-005,
[ADR-0017](adr/adr-0017-import-sources.md)), and this file records the concrete providers.
Swapping any is a change *here*, not to a decision record.

## Shape

The app runs on one small server the maintainer owns; the database and auth are a **managed
service**; files are object storage. Openship is the deploy manager, run **self-hosted**.

| Layer | Choice | Notes |
|-------|--------|-------|
| Deploy manager | **Openship, self-hosted** — the desktop app on the maintainer's Mac | Free, open-source control plane. It connects to `ted106` over SSH and deploys the app there; the `openship` CLI drives the same local control plane. **Openship Cloud is not used** — its free tier only rents managed servers and gates domain routing behind a paid plan, so the self-hosted control plane is the free path. |
| App host | **Mikrus `ted106`** (8 GB / 2 vCPU, Ubuntu 24.04, Docker) | Unprivileged LXC, connected to Openship over SSH (IPv4 `37.27.111.248:10106`, key auth). Runs **only the DM app** (FastAPI + ingestion worker + the built frontend). Public ingress is IPv6:80 (`ted106.mikrus.cloud`) + two TCP ports `20106`/`30106` (`ted106-20106.mikrus.cloud`); TLS is terminated by Mikrus — never bind 443. |
| Data + Auth + Storage | **Supabase Cloud** (free tier) — project `DM Assistant` (`zfhluuonhmexjfhjjghf`), region `eu-west-3`; Postgres 17 + **pgvector** + Auth (GoTrue) + Storage | Managed, so **zero load on `ted106`**. pgvector enabled ([ADR-0016](adr/adr-0016-voyage-embeddings.md)). The box now hosts only the app, which fits 2 vCPU / 8 GB comfortably. |
| Auth | **Supabase Auth** (GoTrue, hosted) | The backend validates Supabase-issued JWTs. Supersedes hand-built auth — [ADR-0020](adr/adr-0020-supabase-auth.md). |
| Files | **Cloudflare R2** (S3-compatible, the `FileStore` object-store adapter) | Off-box, zero egress, presigned URLs. Supabase Storage (free 1 GB) is an alternative; R2 keeps files independent. **Today** uploads go through the local-disk `FileStore` onto the `files` Docker volume on `ted106` (`FILE_STORE_PATH`); the R2 adapter replaces it, and until then those files live only on the box. Cloudflare Free caps a proxied upload at 100 MB. |
| LLM | **OpenRouter**, zero-retention allowlist ([ADR-0019](adr/adr-0019-openrouter-privacy-routing.md)) | Reached with `OPEN_ROUTER_API_KEY`. |

## How it's wired

- **Openship (on the Mac) manages, `ted106` is the compute.** The self-hosted Openship
  control plane runs on the maintainer's Mac and deploys the DM app onto `ted106` over SSH
  (in Docker). The Mac must be on to deploy or manage; the deployed app keeps running on
  `ted106` independently.
- **The app talks to Supabase Cloud over the network** — Postgres (connection string /
  pooler) for data, and the Supabase API (Auth, Storage) over HTTPS. Nothing
  database-related runs on `ted106`.
- **Publishing (Mikrus model).** Only Quillbert needs a public endpoint, and it is reached
  over the server's **IPv6**. The frontend is published on IPv6 port 80 and the backend on
  `30106` (`:::80:80`, `:::30106:8000` as Openship service port overrides), so the raw IPv4
  URLs (`http://37.27.111.248:20106`) no longer answer. Three names point at it:
  `quillbert.app` (Cloudflare `AAAA` → the server's IPv6, proxied, SSL mode **Flexible**:
  Cloudflare reaches the origin over plain HTTP on port 80), `quillbert.mikrus.dev` (Mikrus
  free subdomain → port 80) and `quillbertapi.mikrus.dev` (→ `30106`). The API is also
  reachable through the frontend's proxy, so `quillbert.app` alone is enough. Supabase is
  reached as an external HTTPS service, not published from the box.

## Environment & secrets

Frontend variables are **public** (they ship in the browser bundle); backend values are
**secret**. Never commit secrets.

**Public — frontend build (`VITE_` prefix, our Vite stack), fine as plain CI variables:**

| Variable | Value / source |
|----------|----------------|
| `VITE_SUPABASE_URL` | `https://zfhluuonhmexjfhjjghf.supabase.co` |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_…` (Supabase → Settings → API) |

Data is protected by Supabase **Row-Level Security**, not by hiding these — that's why they
are safe in the bundle and in plain CI variables.

**Secret — backend runtime (Openship project env) + CI secrets:**

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Supabase Postgres connection string (Settings → Database) |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend-only Supabase access (Settings → API) |
| `SUPABASE_JWT_SECRET` | Validate Supabase JWTs ([ADR-0020](adr/adr-0020-supabase-auth.md); Settings → API) |
| `OPEN_ROUTER_API_KEY` | LLM gateway ([ADR-0019](adr/adr-0019-openrouter-privacy-routing.md)); a GitHub Actions **secret**, not a variable |
| `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_ENDPOINT` | Cloudflare R2 |

## Resourcing

`ted106` (8 GB / 2 vCPU) now hosts **only the app** — comfortable, since the database's
compute is Supabase's problem (Cloud). The limits to watch are on the **Supabase free
tier**:

- ~**500 MB** database — embeddings are what grow it; prune/trim as needed,
- **1 GB** Storage — moot, files are on R2,
- the project **pauses after ~7 days idle** (one click to resume) — a personal
  weekly-session tool will hit this occasionally.

## Backups

- **Database:** Supabase Cloud's own backups (free tier is limited — no PITR), plus a
  periodic off-box `pg_dump` as the real safety net; migrations are versioned
  ([ADR-0013](adr/adr-0013-postgres-for-local-and-hosted.md) IMP-002).
- **Files:** R2 bucket versioning.

## Status (2026-10-14)

- **Supabase Cloud:** project live, **pgvector enabled** ✅, MCP-managed.
- **`ted106`:** connected to Openship (self-hosted on the Mac) as an SSH server, **Healthy**
  (Docker / Git / rsync green). No workloads yet.
- **App:** not built — the repo is pre-implementation, so **nothing is deployed to `ted106`
  yet**.
- **Next:** build the DM app (backend + frontend) against this foundation, then deploy it to
  `ted106` via Openship and wire its env to Supabase Cloud + R2 + OpenRouter.

## Notes / risks

- Openship's control plane lives on the **Mac** — fine for a solo maintainer, but deploys
  and management need the Mac on (the running app on `ted106` does not).
- Mikrus is best-effort hosting (no SLA); `ted106` is an unprivileged LXC.
- The Supabase free-tier **pause** and **500 MB** cap are the limits most likely to bite.

## References

- [ADR-0018](adr/adr-0018-hosted-first-local-v2.md) — hosted-first MVP
- [ADR-0013](adr/adr-0013-postgres-for-local-and-hosted.md) — PostgreSQL store and the `FileStore` port
- [ADR-0016](adr/adr-0016-voyage-embeddings.md) — embeddings / `pgvector`
- [ADR-0019](adr/adr-0019-openrouter-privacy-routing.md) — OpenRouter provider and the API key
- [ADR-0020](adr/adr-0020-supabase-auth.md) — Supabase Auth (supersedes ADR-0008)

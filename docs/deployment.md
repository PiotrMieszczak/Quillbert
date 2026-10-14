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

One self-hosted server, managed through Openship:

| Layer | Choice | Notes |
|-------|--------|-------|
| Manager / dashboard | **Openship** (free tier, control-plane only) | Deploys and manages workloads on *your own* server. The free tier can manage a connected server; only workloads hosted on **Openship Cloud's own compute** need a paid plan (verified via host-fit: "static sites only"). |
| Server | **Mikrus `ted106`** (plan 4.1 — 8 GB / 2 vCPU, Ubuntu 24.04, Docker) | Unprivileged LXC. Public ingress is **IPv6 port 80** (`ted106.mikrus.cloud`) + **two TCP ports `20106` / `30106`** (`ted106-20106.mikrus.cloud`). TLS is terminated by Mikrus — never bind 443. |
| Data | **Supabase** (one-click Openship app) — Postgres + pgvector + Auth + Storage + Studio | Gives `pgvector` with zero doubt ([ADR-0016](adr/adr-0016-voyage-embeddings.md)). Advisory minimum 4 vCPU / 8 GB (~8 containers), so **tight on 2 vCPU**. |
| Auth | **Supabase Auth** (GoTrue) | Bundled with the stack; the backend validates Supabase JWTs. Supersedes hand-built auth — [ADR-0020](adr/adr-0020-supabase-auth.md). |
| Files | **Cloudflare R2** (S3-compatible, the `FileStore` object-store adapter) | Off-box, zero egress, presigned URLs. Supabase Storage is bundled as an alternative; R2 keeps files independent of the box. |
| LLM | **OpenRouter**, zero-retention allowlist ([ADR-0019](adr/adr-0019-openrouter-privacy-routing.md)) | Not hosted here; reached with `OPEN_ROUTER_API_KEY`. |

## How it's wired

- **Openship manages, `ted106` is the compute.** Openship (free) is the external control
  plane: you register `ted106` as a self-hosted server, and Openship deploys the Supabase
  app and the DM Assistant onto it through its agent. Openship Cloud's own compute (the paid
  tier) is not used — this is the "manager over your own box" path, not Cloud hosting.
- **Publishing (Mikrus model).** With only two public TCP ports, the DM app takes one
  (e.g. `20106` → `ted106-20106.mikrus.cloud`) and Supabase Studio/API the other; Postgres
  (`5432`) stays internal to the box.
- **Admin access.** Supabase Studio and the Openship dashboard carry their own logins; a
  separate WireGuard admin VPN is impractical on an unprivileged Mikrus LXC (userspace-only,
  no spare public port), so it is dropped. Admin goes through Openship + Studio auth, and
  Postgres is never published.

## Resourcing reality

`ted106` is **8 GB / 2 vCPU**; Supabase's advisory minimum is **4 vCPU / 8 GB**, and the DM
backend + ingestion worker run alongside it. The advisory minimum does not hard-block a
self-hosted deploy, so it will run, but expect it to be **tight** — plan to **upsize Mikrus
(e.g. 4.2, 16 GB)** if ingestion/embeddings starve. Files on R2 keep disk off the box.

## Secrets

Environment variables via Openship's project env — never committed:

| Variable | Purpose |
|----------|---------|
| `OPEN_ROUTER_API_KEY` | LLM gateway ([ADR-0019](adr/adr-0019-openrouter-privacy-routing.md)); in CI a GitHub **secret**, not a variable |
| `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_ENDPOINT` | Cloudflare R2 |
| Supabase anon / service-role keys, JWT secret | App ↔ Supabase (database + Auth) |

## Backups

- **Postgres** (inside Supabase): scheduled `pg_dump` off-box; versioned migrations
  ([ADR-0013](adr/adr-0013-postgres-for-local-and-hosted.md) IMP-002).
- **Files**: R2 bucket versioning.
- Mikrus is best-effort hosting (no SLA), so the restore path is the safety net.

## Status (2026-10-14)

- **`ted106`**: Ubuntu 24.04 LXC, Docker installed, **no workloads yet**, and **not yet
  enrolled in Openship** (no agent/service/containers present).
- **Openship**: workspace present, **zero projects**, free tier (Cloud hosting is
  static-only on this plan).
- **Next step**: register `ted106` as a self-hosted server in the Openship **dashboard**
  (this mints an enroll command) — registering a server is **not** in the Openship API. Then
  deploy Supabase, verify health, then the DM app. The enroll is also the live test of
  whether Openship's agent runs on a Mikrus unprivileged LXC.

## Open risks

Technical, not billing — all surface at or after enrollment:

1. Openship's agent may not install cleanly on an **unprivileged LXC**.
2. **2 vCPU** is under Supabase's advisory 4 — tight; upsize Mikrus if needed.
3. **Two public ports** must cover both the app and Supabase's Studio/API.

## References

- [ADR-0018](adr/adr-0018-hosted-first-local-v2.md) — hosted-first MVP
- [ADR-0013](adr/adr-0013-postgres-for-local-and-hosted.md) — PostgreSQL store and the `FileStore` port
- [ADR-0016](adr/adr-0016-voyage-embeddings.md) — embeddings / `pgvector`
- [ADR-0019](adr/adr-0019-openrouter-privacy-routing.md) — OpenRouter provider and the API key
- [ADR-0020](adr/adr-0020-supabase-auth.md) — Supabase Auth (supersedes ADR-0008)

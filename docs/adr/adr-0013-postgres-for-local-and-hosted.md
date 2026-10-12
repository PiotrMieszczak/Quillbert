---
title: "ADR-0013: PostgreSQL as the single store for both local and hosted deployment"
status: "Superseded"
date: "2026-09-15"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "storage", "database", "deployment"]
supersedes: "ADR-0003"
superseded_by: "ADR-0018"
---

# ADR-0013: PostgreSQL as the single store for both local and hosted deployment

## Status

Proposed | Accepted | Rejected | **Superseded** | Deprecated

> Superseded by [ADR-0018](adr-0018-hosted-first-local-v2.md). The PostgreSQL store
> decision is **retained** — one engine, one dialect, one migration path, in whichever mode
> ships. What changed is the deployment framing: the MVP now targets hosted only, and local
> deployment (CON-001's co-equal second target) is deferred to v2. Keeping PostgreSQL rather
> than reverting to SQLite is precisely what keeps that v2 local path cheap to add.

## Context

[ADR-0003](adr-0003-sqlite-single-store.md) chose SQLite as the only data store. Its
reasoning was sound under the premise it was given: a local-first, single-user tool where
*"every additional store is something the user must install and run"* (ADR-0003 CON-001).
It considered PostgreSQL and rejected it in ALT-004 — *"still a server the user must run
for a single-user local tool"* — with an explicit note: **"Revisit if the product ever
becomes hosted or multi-user."**

That condition has now been met. This record is that revisit.

- **CON-001**: The product must run **well in both modes**: locally on a game master's own
  machine, and hosted — on the user's own hardware or a third-party service. Neither is a
  secondary path or a future migration; both are targets now.
- **CON-002**: In the hosted mode a database server exists regardless. ADR-0003 ALT-004's
  rejection reason — the burden of running a server — does not apply to a deployment that
  is already a server. The cost it priced is not paid in that mode.
- **CON-003**: Keeping SQLite locally and PostgreSQL when hosted means **two databases**,
  and therefore two SQL dialects, two migration paths, two sets of concurrency semantics,
  and two things to test. That is more operational burden than one server, not less.
- **CON-004**: Retrieval is moving to hybrid keyword + vector search
  ([ADR-0014](adr-0014-hybrid-retrieval.md)). SQLite reaches vectors through the
  `sqlite-vec` extension; PostgreSQL reaches them through `pgvector`, alongside a mature
  full-text implementation in the same engine and the same transaction.
- **CON-005**: Uploaded files are already modelled behind a `FileStore` port in
  `docs/folder-structure.md`. Where the bytes physically live is therefore a deployment
  choice, not a schema choice, and does not need settling here.

## Decision

**PostgreSQL is the single data store in both deployment modes.**

- **Local**: PostgreSQL runs alongside the application — a container, or an installed
  service. The application does not fall back to SQLite.
- **Hosted**: the same PostgreSQL, provided as a managed service or self-hosted.
- **Search**: PostgreSQL full-text (`tsvector`) and `pgvector` live in the same database
  and the same transaction as the rest of the schema ([ADR-0014](adr-0014-hybrid-retrieval.md)).
- **Uploaded files**: behind the existing `FileStore` port. Local deployment writes to
  disk; hosted deployment may write to disk or to an object store. **The provider is not
  decided here** and does not need to be: the port is the decision.

One database engine, one dialect, one migration path, one set of semantics — in both modes.

## Consequences

### Positive

- **POS-001**: One code path. No dialect branching, no "works locally, fails hosted" class
  of bug, and the local mode genuinely exercises what the hosted mode runs.
- **POS-002**: Hybrid retrieval becomes ordinary rather than exotic — `tsvector` and
  `pgvector` are the same database, joined in one query and one transaction.
- **POS-003**: Real concurrency. ADR-0003 NEG-003 flagged SQLite's write concurrency as
  needing WAL mode and care for a worker writing beside the API; PostgreSQL removes that
  concern rather than mitigating it.
- **POS-004**: Multi-user becomes a deployment question rather than a rewrite, which is
  what PRIN-004 already anticipated for hosting.
- **POS-005**: The graph queries ADR-0003 worried about gain recursive CTEs that are
  materially better than SQLite's, should they ever exceed one hop.

### Negative

- **NEG-001**: The local mode loses "zero setup". ADR-0003 POS-001 — *the database is a
  file; the application creates it on first run* — is genuinely given up. A game master
  running locally needs Docker or an installed PostgreSQL.
- **NEG-002**: Backup and portability are no longer "copy one file" (ADR-0003 POS-003).
  They become `pg_dump` plus the file store.
- **NEG-003**: Tests need a real PostgreSQL. The in-memory SQLite trick is gone;
  containerised fixtures are slower than a temp file.
- **NEG-004**: A dependency the user must keep running is now a support surface — a
  stopped container reads to the user as a broken application.

### Neutral

- **NEU-001**: ADR-0003's ALT-011 argument is untouched and still correct: a graph-shaped
  domain does not imply a graph database, because what selects a store is the shape of the
  **queries**. Nothing here adds Neo4j; the queries are still zero or one hop.

## Alternatives Considered

### Keep SQLite locally, PostgreSQL when hosted

- **ALT-001**: **Description**: Storage behind a port with two implementations, selected
  per deployment.
- **ALT-002**: **Rejection Reason**: The abstraction is real but the cost lands in the
  worst place — two dialects, two migration paths, two concurrency models, and a local
  mode that no longer exercises what hosted runs. FTS5 and `tsvector` are not
  interchangeable behind one interface without reimplementing ranking above it, which is
  where the retrieval logic actually lives.

### Keep ADR-0003 unchanged; treat hosting as a later migration

- **ALT-003**: **Description**: Ship SQLite, port to PostgreSQL if hosting materialises.
- **ALT-004**: **Rejection Reason**: The premise has already changed — hosting is a stated
  target now, not a hypothetical. Deferring the change means writing schema, migrations,
  and retrieval twice, with the second pass under pressure.

### SQLite everywhere, including hosted

- **ALT-005**: **Description**: Keep one store by hosting SQLite (LiteFS, Turso, or a
  single-writer deployment).
- **ALT-006**: **Rejection Reason**: Preserves the single-engine property, but constrains
  the hosted mode to one writer and makes multi-user a genuine rewrite. It optimises for
  the mode that tolerates a server least.

## Implementation Notes

- **IMP-001**: Ship a `docker compose` file that brings up PostgreSQL for local
  development and local use, so NEG-001's setup cost is one documented command.
- **IMP-002**: Migrations are versioned from the start (carried over from ADR-0003
  IMP-003) — a schema change must never require discarding campaigns.
- **IMP-003**: `campaign_id` scoping stays enforced in the repository layer, unchanged by
  the engine (BND-003, DEC-005).
- **IMP-004**: Tests run against a containerised PostgreSQL. Keep the suite fast by
  sharing one instance across tests with per-test transactions rolled back, rather than a
  fresh database each.
- **IMP-005**: The `FileStore` port already exists in `docs/folder-structure.md`. The
  hosted file provider (object store or mounted volume) is decided when hosting is
  actually set up, and is a deployment note rather than an ADR.
- **IMP-006**: Revisit trigger — if the local-setup burden (NEG-001) measurably stops
  people using the tool locally, reconsider ALT-001 with that evidence.

## References

- **REF-001**: [ADR-0003](adr-0003-sqlite-single-store.md) — superseded by this record
- **REF-002**: [ADR-0014](adr-0014-hybrid-retrieval.md) — hybrid retrieval, which this enables
- **REF-003**: `docs/data-model.md` — the resulting schema
- **REF-004**: `docs/folder-structure.md` — the `FileStore` port

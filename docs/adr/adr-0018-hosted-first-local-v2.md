---
title: "ADR-0018: Hosted-first MVP; local deployment deferred to v2"
status: "Accepted"
date: "2026-10-12"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "deployment", "scope", "database"]
supersedes: "ADR-0013"
superseded_by: ""
---

# ADR-0018: Hosted-first MVP; local deployment deferred to v2

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[ADR-0013](adr-0013-postgres-for-local-and-hosted.md) chose PostgreSQL as the single store
and framed local and hosted as **co-equal targets now** — *"Neither is a secondary path or
a future migration; both are targets now"* (ADR-0013 CON-001). That framing is also a
product principle: PRIN-004, *"targets two deployments as equals."*

The premise has moved. The MVP's job is to prove the product — trustworthy grounded
retrieval over a GM's own material — not to prove that it runs in two deployment shapes.
Carrying local deployment as a v1 gate adds setup surface (ADR-0013 NEG-001: Docker or an
installed PostgreSQL) and, together with a local model provider, a whole offline path to
build, document, and support before the core value is demonstrated.

- **CON-001**: Local deployment is still **wanted** — it is a genuine appeal of a
  single-user GM tool — but it is not what the MVP must prove. It becomes an optional v2
  goal, not a v1 acceptance gate.
- **CON-002**: A hosted-first MVP pairs with a hosted model provider
  ([ADR-0019](adr-0019-openrouter-privacy-routing.md)). The local-only model provider
  (Ollama) that ADR-0006 CON-004 justified for fully-offline operation moves to v2 with
  local deployment; the two were always coupled.
- **CON-003**: ADR-0013's *storage* conclusion is not in dispute. PostgreSQL remains the
  single store. What this record changes is the deployment framing around it, not the
  engine.
- **CON-004**: Keeping one engine (PostgreSQL) rather than reverting to SQLite is exactly
  what keeps local deployment cheap to add in v2 — one dialect, one migration path, one
  set of semantics. Deferring local must not reintroduce a second store.

## Decision

**The v1 MVP targets hosted deployment only. Local self-hosting is a v2 goal.**

- **MVP (hosted)**: a single PostgreSQL instance (managed service or self-hosted),
  reached by the same code path the application already assumes. This is the only
  deployment v1 acceptance criteria are written against.
- **v2 (local)**: running the full stack on a game master's own machine — PostgreSQL via
  `docker compose` or an installed service, as ADR-0013 IMP-001 described. The work is
  deferred, not designed away.
- **PostgreSQL stays the single store** in both. Nothing in the schema, migrations, or
  repository layer may foreclose the v2 local path. No second engine is introduced for
  either mode (ADR-0013 ALT-001 rejection still holds).

The engine decision from ADR-0013 survives intact; this record narrows *when* each
deployment ships, not *what it stores*.

## Consequences

### Positive

- **POS-001**: Smaller v1 surface. No local DB-setup flow to document and support, no
  "works hosted, broken locally" support load, as a v1 gate (ADR-0013 NEG-001, NEG-004
  are deferred with the mode that incurs them).
- **POS-002**: The MVP can assume a reachable, always-on PostgreSQL and a hosted model
  provider, which simplifies the offline/unreachable-dependency handling v1 must build.
- **POS-003**: Because PostgreSQL stays the single store, v2 local deployment is adding a
  deployment recipe (ADR-0013 IMP-001) and a local model provider — not a schema rewrite.
  The single-engine investment pays off later rather than now.

### Negative

- **NEG-001**: Local-first operation — a real selling point of a single-user tool — is not
  in v1. PRIN-004 is rewritten from "two deployments as equals" to hosted-first with local
  as a v2 goal.
- **NEG-002**: The fully-offline story (no network, local model) is gone from the MVP
  entirely, since the local model provider moves to v2 with local deployment
  ([ADR-0019](adr-0019-openrouter-privacy-routing.md) NEG-002).
- **NEG-003**: ADR-0013 POS-001's claim that "the local mode genuinely exercises what the
  hosted mode runs" is not realised in v1 — there is only the hosted mode to exercise.

### Neutral

- **NEU-001**: ADR-0013's rejection of a second store (ALT-001, ALT-005) is untouched and
  still binding. Deferring local is not permission to reach for SQLite later; the v2 local
  path runs the same PostgreSQL.

## Alternatives Considered

### Keep local and hosted as co-equal v1 targets (ADR-0013 as written)

- **ALT-001**: **Description**: Ship both deployment modes in v1, as ADR-0013 and PRIN-004
  specify.
- **ALT-002**: **Rejection Reason**: Spends v1 effort proving a deployment shape rather
  than the product. The local setup burden and the local model path are surface the MVP
  does not need to demonstrate that grounded retrieval is trustworthy.

### Defer local *and* revert to SQLite for the eventual local mode

- **ALT-003**: **Description**: Since local is v2, use SQLite there and PostgreSQL hosted.
- **ALT-004**: **Rejection Reason**: Reintroduces exactly the two-engine cost ADR-0013
  ALT-001 priced and rejected — two dialects, two migration paths, two concurrency models.
  Deferring *when* local ships is cheap; splitting the engine is not.

## Implementation Notes

- **IMP-001**: v1 acceptance criteria assume a single hosted PostgreSQL. ADR-0013's local
  `docker compose` recipe (IMP-001) is retained in the repository as the v2 starting
  point, not deleted.
- **IMP-002**: Migrations stay versioned from the start (ADR-0013 IMP-002) — a v2 local
  deployment must be able to run the same migration history.
- **IMP-003**: `campaign_id` scoping in the repository layer is unchanged (ADR-0013
  IMP-003, BND-003, DEC-005) and is independent of deployment mode.
- **IMP-004**: Revisit trigger — promote local deployment to active work when v1 is proven
  and there is demand to run the tool fully on a GM's own hardware. It pairs with the
  v2 local model provider (ADR-0019 IMP-005).

## References

- **REF-001**: [ADR-0013](adr-0013-postgres-for-local-and-hosted.md) — superseded by this
  record; its PostgreSQL store decision is retained, its co-equal-deployment framing is not
- **REF-002**: [ADR-0019](adr-0019-openrouter-privacy-routing.md) — the paired model-provider
  change; the local model provider defers with local deployment
- **REF-003**: `docs/product-brief.md` PRIN-004 — rewritten to hosted-first by this record
- **REF-004**: `docs/mvp-scope.md` — the hosted-only v1 scope and deferred local row

---
title: "ADR-0020: Supabase Auth in v1; the project is tool-first"
status: "Accepted"
date: "2026-10-14"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "auth", "security", "supabase"]
supersedes: "ADR-0008"
superseded_by: ""
---

# ADR-0020: Supabase Auth in v1; the project is tool-first

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[ADR-0008](adr-0008-own-auth-v1.md) built authentication by hand, and its **sole**
justification was CON-001: *"The project is a learning exercise as much as a tool.
Understanding how authentication works is a goal, not a cost."* Every other point in that
record — CON-002 "a managed provider hides the mechanism", the rejection of Supabase Auth —
follows from that premise.

That premise has been restated. The project's main purpose is a **personal tool**: a
replacement for NotebookLM + Claude Desktop for building and running tabletop RPG campaigns.
Learning is a welcome side effect, not the origin. When the goal is a tool the maintainer
wants to *use*, "work unrelated to the product's value" is a cost again, not the point —
which is the reasoning [ADR-0007](adr-0007-local-profile-auth.md) made before 0008 inverted
it.

Two facts make a bundled provider the obvious choice now, where they did not hold under 0008:

- **CON-001**: **Supabase is already the datastore.** The deployment runs full self-hosted
  Supabase for Postgres + `pgvector` + Storage (`docs/deployment.md`). Its Auth (GoTrue) is
  already present, so using it adds nothing new to operate. ADR-0008 CON-003's "no new
  infrastructure" argument now points the other way.
- **CON-002**: **The product is single-user.** Auth gates the maintainer's own account, not
  a multi-tenant signup system, so the surface is small and the stakes are low.

## Decision

**Authentication in v1 uses Supabase Auth (GoTrue).**

- Supabase Auth handles signup/login, **Google OAuth**, and **password reset** — the surface
  the design draws and AC-009/AC-011 require — as configuration rather than hand-written code.
- The FastAPI backend **validates Supabase-issued JWTs**; it does not mint its own sessions
  or hash passwords. User identity lives in Supabase's `auth` schema.
- Owner scoping stays enforced in the application (`BND-003`, `campaign_id`), independent of
  who issues the token.

## Consequences

### Positive

- **POS-001**: AC-009/AC-011 are met by configuration — signup, Google OAuth, reset, and
  password hashing are Supabase's, not code to write and secure.
- **POS-002**: Nothing new to run — GoTrue ships inside the Supabase stack already deployed.
- **POS-003**: Matches the tool-first purpose: effort goes to campaign features, not to
  re-implementing auth primitives.

### Negative

- **NEG-001**: The learning value ADR-0008 existed to capture is given up. That is the
  accepted trade now that learning is secondary.
- **NEG-002**: Identity and tokens are **coupled to Supabase** — swapping auth later is no
  longer a local change. (Swapping the database would already move Supabase, so this widens
  an existing blast radius rather than adding new infrastructure.)
- **NEG-003**: Self-hosted GoTrue is operated, not merely consumed — one more of the
  Supabase stack's containers to keep healthy.

### Neutral

- **NOTE-001**: This is the mirror of 0007 → 0008. 0007 pointed at Supabase Auth; 0008
  reversed it for learning; 0020 reverses again because the stated purpose moved back to the
  tool. The premise moved, the reasoning held, the conclusion inverted — the shape this ADR
  set already documents.

## Alternatives Considered

### Keep hand-built auth (ADR-0008 as written)

- **ALT-001**: **Description**: Build signup, argon2, JWT sessions, OAuth, and reset by hand.
- **ALT-002**: **Rejection Reason**: Its only justification was learning-first, which no
  longer holds. It is more code to write and secure, for a single-user tool whose datastore
  already bundles auth.

### A different managed provider (Clerk, Auth0)

- **ALT-003**: **Description**: Use a third-party auth SaaS.
- **ALT-004**: **Rejection Reason**: Supabase is already present and self-hosted; a separate
  provider is new infrastructure and, typically, an external dependency holding user data.

### No auth, or a single hard-coded account

- **ALT-005**: **Description**: Gate the tool with one static credential.
- **ALT-006**: **Rejection Reason**: The design specifies Google login and password reset,
  and the app is hosted and reachable — a real login is cheap via Supabase and worth having.

## Implementation Notes

- **IMP-001**: The backend verifies Supabase JWTs (JWKS / shared secret) and issues none —
  no argon2, no custom session cookies.
- **IMP-002**: `BND-003` owner scoping is unchanged and still tested; the auth provider does
  not relax it.
- **IMP-003**: Supabase keys (anon, service-role, JWT secret) come from env/secrets, never
  committed (`docs/deployment.md`).
- **IMP-004**: Single-user: signup can be closed once the owner account exists, or left open
  behind Supabase — a deployment choice, not a schema one.

## References

- **REF-001**: [ADR-0008](adr-0008-own-auth-v1.md) — superseded by this record
- **REF-002**: [ADR-0007](adr-0007-local-profile-auth.md) — which first pointed at a managed provider
- **REF-003**: `docs/deployment.md` — the Supabase stack that provides GoTrue
- **REF-004**: `docs/mvp-scope.md` — AC-009/AC-010/AC-011, reframed onto Supabase Auth
- **REF-005**: `docs/product-brief.md` PRIN-004 — auth wording updated by this record

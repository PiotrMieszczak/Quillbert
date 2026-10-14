---
title: "ADR-0008: Build authentication by hand in v1"
status: "Superseded"
date: "2026-09-02"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "auth", "learning", "security"]
supersedes: "ADR-0007"
superseded_by: "ADR-0020"
---

# ADR-0008: Build authentication by hand in v1

## Status

Proposed | Accepted | Rejected | **Superseded** | Deprecated

> Superseded by [ADR-0020](adr-0020-supabase-auth.md). This record's sole justification was
> CON-001 — the project as a learning exercise. That premise was restated as tool-first
> (learning a side effect), and Supabase became the datastore, so its bundled Auth (GoTrue)
> is now the choice. Kept because the analysis is correct under its premise — the mirror of
> how 0008 itself superseded 0007.

## Context

[ADR-0007](adr-0007-local-profile-auth.md) deferred authentication to a hosted provider,
reasoning that password-reset email deliverability is "real work unrelated to this
product."

That reasoning assumed a product optimising for time-to-working-software. **DM Assistant is
also a learning project**, which inverts it: work that is unrelated to a product's value
can be exactly the work worth doing when the goal is understanding.

Constraints, restated for this purpose:

- **CON-001**: The project is a learning exercise as much as a tool. Understanding how
  authentication works is a goal, not a cost.
- **CON-002**: A managed provider hides the mechanism. `supabase.auth.signUp()` teaches
  that SDK, not sessions, hashing, or OAuth. One can ship with it and still be unable to
  explain what a JWT is.
- **CON-003**: The stack is already FastAPI + SQLAlchemy + SQLite
  ([ADR-0001](adr-0001-react-vite-spa.md), [ADR-0003](adr-0003-sqlite-single-store.md)).
  Auth built here needs no new infrastructure.
- **CON-004**: Cost must stay at or near zero.
- **CON-005**: The design already specifies the full surface — email, password, "Forgot?",
  "Continue with Google", and "Create a table". Building real auth implements the screen
  as drawn rather than faking half of it.
- **CON-006**: The security-critical part is password hashing, and that is a library call.
  The rest — sessions, redirects, token expiry — is application logic, not cryptography.

## Decision

**Build authentication in FastAPI in v1**, covering the whole surface the design shows:

1. **Email and password** — signup, login, logout. Argon2 hashing via `passlib`.
2. **Sessions** — a signed JWT delivered in an **httpOnly, Secure, SameSite cookie**.
3. **Google OAuth** — the real authorization-code flow: redirect, callback, token exchange.
4. **Password reset** — single-use expiring tokens and an email send.

No managed auth provider, and no self-hosted identity server.

Storage stays SQLite ([ADR-0003](adr-0003-sqlite-single-store.md)); a `user` table replaces
the single `profile` row that ADR-0007 proposed.

### Why httpOnly cookies rather than localStorage

The common tutorial pattern stores a JWT in `localStorage` and sends it in an
`Authorization` header. It is easier to write and **strictly worse**: any script running on
the page can read `localStorage`, so a single XSS bug hands over the token.

An httpOnly cookie is not readable from JavaScript at all. The browser attaches it
automatically, so the frontend gets simpler as well as safer. The trade is that cookies are
sent automatically, which is what CSRF exploits — hence `SameSite` (IMP-005).

That trade-off is worth understanding directly, which is a reason to build it rather than
adopt a library that has already decided it.

## Consequences

### Positive

- **POS-001**: The mechanism is learned rather than delegated — hashing, sessions, token
  expiry, the OAuth handshake, and why cookie flags exist.
- **POS-002**: No vendor, no free-tier limits, nothing external to be down, and no account
  data in a third party.
- **POS-003**: The design's login screen is implemented as drawn, including the Google
  button and the "Forgot?" link, rather than as a shell.
- **POS-004**: [ADR-0003](adr-0003-sqlite-single-store.md) stands. Auth adds one table; no
  new infrastructure.
- **POS-005**: Multi-user becomes possible earlier, since real users exist from v1. Adding
  `owner_id` remains one column plus a backfill (DEC-005).
- **POS-006**: Cost stays zero. Transactional email has a free tier at the volume a
  personal project produces.

### Negative

- **NEG-001**: More code to own and maintain than a provider call — roughly 300–400 lines
  across hashing, sessions, OAuth, and reset.
- **NEG-002**: Email deliverability is now our problem. Reset mail requires a sending
  domain with SPF and DKIM, or it lands in spam.
- **NEG-003**: Security bugs are ours. The hashing is safe by library, but session expiry,
  token reuse, and redirect validation are all places to get it wrong.
- **NEG-004**: No MFA, SSO, device management, or account recovery beyond email reset.
  Acceptable here; it would not be for a product with real customers.
- **NEG-005**: Per-user isolation stays application-level (`BND-003`) rather than enforced
  by row-level security as Postgres would allow. Every query must filter by owner, and a
  missed filter is a data leak.
- **NEG-006**: Auth is built before the retrieval core is proven — the sequencing
  ADR-0007's CON-001 warned about. Accepted deliberately: under CON-001 here, the auth work
  has value even if retrieval never works out.

## Alternatives Considered

### Supabase Auth (the superseded decision)

- **ALT-001**: **Description**: Managed auth on a free tier covering 50,000 monthly active
  users, with password reset, verification email, and social login handled.
- **ALT-002**: **Rejection Reason**: It solves the problem by hiding it, which defeats
  CON-001. Remains the right answer for a product on a deadline, and the analysis in
  [ADR-0007](adr-0007-local-profile-auth.md) still holds for that case.

### Local profile with no authentication

- **ALT-003**: **Description**: A single row, no password, the login screen as a profile
  picker.
- **ALT-004**: **Rejection Reason**: Cheapest and adequate for a single local user, but
  teaches nothing and leaves half the designed screen non-functional.

### A framework library (FastAPI-Users, Authlib end to end)

- **ALT-005**: **Description**: A batteries-included auth package providing routes, models,
  and flows.
- **ALT-006**: **Rejection Reason**: The same objection as a managed provider, one layer
  down — it supplies the flows rather than teaching them. `passlib` and `python-jose` are
  used deliberately as *primitives*: they handle the cryptography, which should never be
  hand-written, while the flows stay visible. Authlib is still used for the Google OAuth
  client, since implementing an OAuth client from scratch teaches protocol trivia rather
  than concepts.

### JWT in localStorage

- **ALT-007**: **Description**: The common tutorial pattern — token in `localStorage`, sent
  via an `Authorization` header.
- **ALT-008**: **Rejection Reason**: Readable by any script on the page, so one XSS bug
  leaks the session. Worth knowing as a pattern to recognise and avoid, not to adopt.

## Implementation Notes

- **IMP-001**: `user` table — `id`, `email` (unique), `password_hash` (nullable, for
  OAuth-only accounts), `display_name`, `table_name`, `avatar_path`, `email_verified`,
  `created_at`. `password_hash` being nullable is what lets a Google-only account exist.
- **IMP-002**: Hash with **argon2** via `passlib`. Never write a hashing routine, never use
  a plain SHA family for passwords, and never store anything reversible.
- **IMP-003**: Access tokens are short-lived (~15 minutes) with a longer-lived refresh
  token. Short expiry is what limits the damage of a leaked token.
- **IMP-004**: Cookie flags: `httpOnly`, `Secure`, `SameSite=Lax`, and a `Path`. `Lax`
  allows the OAuth redirect to return while still blocking cross-site POSTs.
- **IMP-005**: `SameSite=Lax` is the CSRF defence. If a flow later needs `SameSite=None`,
  a CSRF token becomes mandatory — do not change that flag casually.
- **IMP-006**: Password-reset tokens are random, **single-use**, and expire in about an
  hour. Store a hash of the token, not the token, for the same reason passwords are hashed.
- **IMP-007**: Reset must not reveal whether an address is registered. Return the same
  response either way, or the endpoint becomes an account-enumeration oracle.
- **IMP-008**: Validate the OAuth `state` parameter on callback. Skipping it is the classic
  OAuth CSRF hole, and it is a two-line check.
- **IMP-009**: Rate-limit login and reset endpoints. Without it, the login route is a
  brute-force target and reset is an email-bombing tool.
- **IMP-010**: Email via a transactional provider's free tier (Resend, Postmark). Expect to
  configure SPF and DKIM on a sending domain — that is NEG-002 in practice.
- **IMP-011**: Keep every route filtered by owner (`BND-003`). With NEG-005 in force, add a
  test asserting that one user cannot read another's campaign.
- **IMP-012**: Secrets — JWT signing key, OAuth client secret — come from environment
  configuration and never reach the frontend or a commit.

## References

- **REF-001**: [ADR-0007](adr-0007-local-profile-auth.md) — superseded; its provider
  analysis remains accurate for a product context
- **REF-002**: [ADR-0003](adr-0003-sqlite-single-store.md) — storage, unchanged by this
- **REF-003**: `docs/product-brief.md` PRIN-004 — local-first, now with real accounts
- **REF-004**: [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- **REF-005**: [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

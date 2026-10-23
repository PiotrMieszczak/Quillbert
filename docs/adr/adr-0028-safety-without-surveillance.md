---
title: "ADR-0028: Safety without surveillance"
status: "Accepted"
date: "2026-10-23"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "security", "privacy", "admin", "moderation"]
supersedes: ""
superseded_by: ""
---

# ADR-0028: Safety without surveillance

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

Quillbert will host other GMs' campaigns. The admin needs to know that nobody is breaking
the app, running up its costs, or uploading illegal material.

- **CON-001**: GMs' campaigns are private creative work. The product promises privacy
  down to its model routing (zero-retention, ADR-0019).
- **CON-002**: The operator is in the EU. Under GDPR, looking at users' content needs a
  stated purpose, must be disclosed, and should be limited to what that purpose needs.
- **CON-003**: TTRPG material is full of violence, horror and adult themes that are
  legitimate. Watching content by hand would mostly find those.
- **CON-004**: Some content is illegal everywhere, CSAM above all, and has to be acted on
  and reported.
- **CON-005**: Most ways to "break the app" (floods, oversized uploads, runaway model
  spend) can be stopped without reading anything.

## Decision

**The admin sees metadata, never GMs' content in general. Abuse is stopped by limits.
Prohibited content is found by automated flags and user reports, and only the flagged
item can be opened, with every opening logged.**

1. **Limits.**
   - Per-user rate limits on chat and uploads.
   - Storage and document quotas.
   - A daily model-cost cap.
   - Alerts on anomalies.
   - Exceeding a limit answers 429 and never touches the GM's data.
2. **Metadata-only overview.**
   - Shows: users, campaign and document counts, storage, model spend, errors, limit hits,
     open flags.
   - Never shows: document text, chat text, or campaign content.
3. **Content policy.** The Terms ban illegal content and harassment, not mature themes. A
   GM accepts the current version at sign-up, and the accepted version is stored.
4. **Flag-only screening.**
   - Uploads, images and generated output are screened by a classifier through the
     Gateway, on the zero-retention allowlist (BND-002).
   - It writes a flag and nothing else.
5. **User reports.** Anything shared with another user can be reported, which creates a
   flag.
6. **Break-glass review.**
   - The admin can open only a flagged item, must give a reason, and every opening
     writes an audit event (who, what, when, why).
   - No route lists or opens another user's content without a flag.
7. **Action.** Suspend the account. Preserve a confirmed illegal item and report it as the
   law requires.
8. **Disclosure and control.** The privacy policy states 1–7. A GM can export all their
   data and delete their account.

## Consequences

### Positive

- **POS-001**: The privacy promise holds for the operator too, not only for model
  providers.
- **POS-002**: Most abuse is stopped automatically, before anyone looks at anything.
- **POS-003**: Every content access by the admin is justified and auditable.

### Negative

- **NEG-001**: Screening is an **exception to BND-001**: a model sees uploaded content at
  ingestion time. It is bounded:
  - It runs after extraction, and only produces a flag.
  - It can never alter extracted text, chunks or citations, and a test enforces that.
  - It goes through the Gateway like every other model call.
- **NEG-002**: Classifiers produce false positives on dark fiction. A flag is a reason to
  look at one item, never an automatic punishment.
- **NEG-003**: An admin can't browse a GM's campaign to help them debug it. Support needs
  the GM to share or export.
- **NEG-004**: Legal texts (Terms, privacy policy) need review by a lawyer before public
  sign-up. That is outside engineering.

## Alternatives Considered

- **ALT-001: Admin can read all content.** Simplest to build. Rejected: it fails CON-001
  and CON-002, and doesn't scale to finding anything (CON-003).
- **ALT-002: No screening, reports only.** Rejected: uploads in private campaigns are seen
  by nobody else, so nobody would report them.
- **ALT-003: Block on a flag automatically.** Rejected: false positives on legitimate dark
  themes would punish GMs for genre fiction.

## Implementation Notes

- **IMP-001**: Tables:
  - `flag`: subject, owner, source (`auto` | `report`), reason, status.
  - `audit_event`: admin, action, subject, reason, at; append-only.
  - `terms_acceptance`: user, version, at.
- **IMP-002**: The admin check is `Identity.is_admin`
  ([ADR-0027](adr-0027-layered-knowledge-admin-vault.md) IMP-005). Break-glass routes
  also require an open flag on that subject.
- **IMP-003**: Limits sit in the HTTP layer and the use cases. Cost is read from the trace
  the Gateway already records (ADR-0024).
- **IMP-004**: Stories: #103 (limits and overview), #104 (moderation), #105 (Terms,
  privacy, export and delete), under epic #99. #105 blocks opening sign-up beyond the
  maintainer.

## References

- **REF-001**: [ADR-0019](adr-0019-openrouter-privacy-routing.md): zero-retention routing.
- **REF-002**: [ADR-0002](adr-0002-deterministic-extraction.md): deterministic ingestion,
  and the exception in NEG-001.
- **REF-003**: [ADR-0027](adr-0027-layered-knowledge-admin-vault.md): the admin role.

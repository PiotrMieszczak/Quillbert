---
title: "ADR-0027: The shared rules library is Arkon, and citations are snapshots"
status: "Accepted"
date: "2026-10-23"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "retrieval", "assistant", "data-model"]
supersedes: "ADR-0023"
superseded_by: ""
---

# ADR-0027: The shared rules library is Arkon, and citations are snapshots

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[ADR-0023](adr-0023-system-rules-library.md) put the shared rules library in Quillbert's
own Postgres. The maintainer wants one reusable TTRPG knowledge service that Quillbert
and other MCP clients (Claude Code, Codex) all read. Arkon is that candidate
([report](../../reports/Modular%20TTRPG%20knowledge%20service.md), #95, #97).

- **CON-001**: Arkon runs as its own stack on `ted106`, with its own Postgres, pgvector,
  Redis and MinIO ([deployment.md](../deployment.md)). It speaks MCP, not a JSON API.
- **CON-002**: At `5e4069d` its only meaning-based search, `search_wiki`, crashed on a
  missing `ResolvedIdentity.project_ids`. It runs under a one-line local patch kept in
  `/opt/arkon/patches`. The tool returns formatted text, not records.
- **CON-003**: Arkon scopes what a token sees by the employee's departments. The token is
  the only trustworthy filter; there is no per-call scope argument.
- **CON-004**: A citation row had a foreign key to `chunk`. An Arkon passage has no chunk
  here, so it could not be cited.
- **CON-005**: The project is pre-release; breaking the citation shape is acceptable.

## Decision

**The shared rules library is Arkon. Quillbert reads it at question time and cites what
it returns as a self-contained snapshot.**

- Each game system maps to one read-only Arkon token (`ARKON_TOKENS`). Its employee
  belongs to that system's department only, and to nothing else.
- Retrieval asks the campaign's own index for k hits and Arkon for at most
  `LIBRARY_TOP_K`. The library hits take that many slots at the end of the list.
  Rankings are never merged by score.
- Only 📄 verbatim source matches are used, one whole page per source. 📘 wiki pages are
  model-written summaries and are never cited.
- A citation stores what the GM sees: `filename`, `page_from`, `heading` and
  `attribution`. `chunk_id` and `document_id` are set for a campaign passage and null for
  a library one. A non-null `attribution` marks a library passage.
- Arkon being unreachable or failing costs the library hits only. The turn answers from
  the campaign's own documents, and the failure is logged.
- `ARKON_URL` unset means no library.

## Consequences

### Positive

- **POS-001**: One library serves Quillbert and every other MCP client the GM uses.
- **POS-002**: Citations reload exactly as cited, even if the source changes later.
- **POS-003**: The repository join on `chunk`/`document` for citations is gone.

### Negative

- **NEG-001**: BND-001 now depends on Arkon's configuration: documents uploaded with
  *preserve verbatim* and no vision model set. Quillbert's tests cannot check this. D0
  (#95) must observe it during import.
- **NEG-002**: Arkon embeds queries and documents itself, outside the Gateway (BND-002).
  The text sent is shared rules only, never campaign material. Its OpenRouter key must be
  separate, with zero-retention enforced on the account.
- **NEG-003**: The adapter parses Arkon's text output with a regex. An upstream format
  change breaks it, which shows as library-unavailable warnings, not wrong citations.
- **NEG-004**: A library passage is a whole page capped at 2,000 characters, which is
  coarser than a campaign chunk.
- **NEG-005**: A patched third-party service under PolyForm Internal Use is the
  maintainer's alone to run.

## Alternatives Considered

- **ALT-001**: Keep ADR-0023: deterministic and simpler, but a second library that other
  AI tools can't use.
- **ALT-002**: Copy Arkon passages into `chunk`. That would mean two indexes of the same
  files, which the report rules out.
- **ALT-003**: Add a JSON search tool to Arkon. Cleaner to read, but a larger fork to
  maintain. Revisit if NEG-003 starts to bite.

## Implementation Notes

- **IMP-001**: `app/adapters/library/arkon.py` (MCP `tools/call` over HTTP, stateless) and
  `combined.py` (quota). Wired in `composition.py` only when `ARKON_URL` is set.
- **IMP-002**: Migration `0010_citation_snapshot` backfills the snapshot from `chunk`.
  A campaign citation still cascades away with its document.
- **IMP-003**: `RunAssistantTurn.execute` takes the campaign's `system_id`. The HTTP route
  supplies it from the owned campaign.
- **IMP-004**: The frontend chip for a library citation has `aria-disabled` and shows the
  attribution in its tooltip.

## References

- **REF-001**: [ADR-0023](adr-0023-system-rules-library.md) — superseded.
- **REF-002**: [ADR-0026](adr-0026-one-assistant-claim-provenance.md) — a citation marks
  a fact; unchanged.
- **REF-003**: #95 (D0 evaluation), #97 (this integration).

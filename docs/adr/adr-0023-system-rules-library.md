---
title: "ADR-0023: Open rules references ship as a shared system library"
status: "Superseded"
date: "2026-10-20"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "retrieval", "assistant", "licensing"]
supersedes: ""
superseded_by: "ADR-0027"
---

# ADR-0023: Open rules references ship as a shared system library

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

A GM who opens a new D&D campaign and asks "how does grappling work?" gets
"Not in your material." until they upload a rulebook. That is correct under PRIN-001, but
it makes the first experience a refusal. The core rules of the systems the picker offers
are the most common Research questions.

- **CON-001**: Research never answers from training knowledge (PRIN-001, AC-003). A model
  that "knows D&D" is a model that invents D&D. Rules have to arrive as citable chunks.
- **CON-002**: A model does not read links. Fetching a URL at question time sends the query
  to a third party, yields text that cannot be cited to a chunk, and is not reproducible.
- **CON-003**: Some rules texts are openly licensed. The D&D 5e System Reference Document
  5.1 (2014 rules) and 5.2 (2024 rules) are published by Wizards of the Coast under
  CC-BY-4.0, which permits redistribution with attribution.
- **CON-004**: Traveller 2e (Mongoose) has no open SRD. Its rules reach Quillbert only as a
  rulebook the GM owns and uploads.
- **CON-005**: Every chunk is campaign-scoped today (BND-003; `document.campaign_id`,
  `chunk.campaign_id`). The same SRD in every campaign would be the same ~2,000 chunks and
  vectors copied per campaign.
- **CON-006**: Ingestion is deterministic and has no generative model (ADR-0002, BND-001).
  Whatever brings the SRD in must use the same pipeline.

## Decision

**Openly licensed rules texts are ingested once per game system into a shared, read-only
system library. Research retrieves from the campaign's own documents and from the library
of the campaign's system.**

- `document` and `chunk` gain a nullable `system_id` (FK → `system.id`). Exactly one of
  `campaign_id` and `system_id` is set, enforced by a check constraint.
- Library documents are added by an operator through a seed command that runs the ordinary
  `IngestDocument` pipeline. No HTTP endpoint creates, changes or deletes them, and the
  Documents page does not list them.
- Retrieval for a campaign searches `campaign_id = :campaign` **or**
  `system_id = :campaign_system`, in one query, ranked together.
- Only texts whose licence permits redistribution go in: CC-BY-4.0, or OGL 1.0a with its
  licence text. Each library document records its attribution line, and the citation shows
  it.
- First contents: SRD 5.1 for `dnd-2014` and SRD 5.2 for `dnd-2024`.
  Nothing for `traveller-2e` (CON-004).

## Consequences

### Positive

- **POS-001**: A new D&D campaign answers core rules questions on its first turn, with
  citations to page numbers, and without loosening PRIN-001.
- **POS-002**: One copy of the SRD and its vectors, no matter how many campaigns use it.
- **POS-003**: A GM's own rulebook and the SRD are ranked together. When they disagree, the
  Research rule for conflicts ("quote both, do not pick one") applies unchanged.

### Negative

- **NEG-001**: BND-003 now has one shared read scope. A query that forgets the
  `campaign_id OR system_id` shape could leak another campaign's chunks. The contract test
  must cover that leak, as well as the case where the library is missing.
- **NEG-002**: The SRD is a subset of the rules. "Not in your material" still answers
  questions about content outside the SRD (for example, most named monsters and spells
  outside the SRD list), which a GM may read as a bug.
- **NEG-003**: Licence obligations become a code concern: attribution must be visible
  wherever an SRD citation is.
- **NEG-004**: The `sha256` uniqueness, which today is per campaign, needs a per-system
  counterpart.

## Alternatives Considered

### Links as sources

- **ALT-001**: **Description**: Store SRD URLs. The model, or a fetcher at question time,
  reads them.
- **ALT-002**: **Rejection Reason**: CON-002. Also no page-level citation, and a dead link
  silently turns rules answers into refusals.

### Copy the SRD into each campaign

- **ALT-003**: **Description**: When a campaign is created, seed the system's SRD documents
  into it as ordinary campaign documents. No schema change.
- **ALT-004**: **Rejection Reason**: CON-005. Duplicated storage, and either duplicated
  embedding cost or a row-copy path that ingestion does not have. The SRD would also
  appear in the GM's Documents list as something they can delete.

### Rely on model training knowledge for core rules

- **ALT-005**: **Description**: Allow Research to answer core-rules questions from what the
  model knows.
- **ALT-006**: **Rejection Reason**: CON-001. It cannot be cited, it mixes editions, and it
  is exactly the invention PRIN-001 rules out.

## Implementation Notes

- **IMP-001**: The migration adds `system_id` to `document` and `chunk`, a check constraint
  that exactly one of `campaign_id` / `system_id` is set, and a unique index on
  `(system_id, sha256)`. The `dnd-2014` system row already shipped in migration 0007.
- **IMP-002**: The seed command is `python -m app.entrypoints.cli.seed_library --system <id>
  --file <pdf> --attribution "<line>"`. It calls `IngestDocument`, so the BND-001 test covers
  it. The PDFs are downloaded by hand from the publisher. Their sha256 and source URL are
  recorded in `docs/deployment.md`.
- **IMP-003**: `ChunkSearch.search` takes `system_id`. The contract test checks four things:
  a library chunk is found for a campaign of that system; it is not found for a campaign of
  another system; another campaign's chunks are never found; and the search works when no
  library exists.
- **IMP-004**: The citation payload carries the document's attribution. The UI shows it
  beside the source.

## References

- **REF-001**: [ADR-0002](adr-0002-deterministic-extraction.md) — the pipeline the seed
  reuses
- **REF-002**: [ADR-0021](adr-0021-gemini-embeddings-via-openrouter.md) — the hybrid
  retrieval this extends
- **REF-003**: `docs/product-brief.md` PRIN-001; `docs/architecture.md` BND-003
- **REF-004**: Wizards of the Coast, System Reference Document 5.1 and 5.2, CC-BY-4.0
  (licence and download from the official D&D SRD page; verify the URL when seeding)

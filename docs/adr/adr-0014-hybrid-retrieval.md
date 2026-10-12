---
title: "ADR-0014: Hybrid keyword + vector retrieval with embedded source chunks"
status: "Superseded"
date: "2026-09-15"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "retrieval", "search", "embeddings"]
supersedes: "ADR-0005"
superseded_by: "ADR-0016"
---

# ADR-0014: Hybrid keyword + vector retrieval with embedded source chunks

## Status

Proposed | Accepted | Rejected | **Superseded** | Deprecated

> Superseded by [ADR-0016](adr-0016-voyage-embeddings.md). The hybrid design below carries
> forward unchanged, with the same POS/NEG/IMP numbering. What changed is where embeddings
> come from: a local model became one fixed hosted model, because the product targets
> hosted multi-user use and every vector must come from the same model. Kept because the
> retrieval reasoning is still the reasoning in force.

## Context

[ADR-0005](adr-0005-fts5-before-vectors.md) chose FTS5 keyword retrieval and deferred
semantic search. It named hybrid keyword + vector with reciprocal rank fusion as
*"the likely long-term answer, and the intended evolution"* (ALT-003), rejecting it only
because *"it presumes the vector half, whose cost and benefit are unmeasured"* (ALT-004).

Two of that record's constraints have changed:

- **CON-001**: ADR-0005 CON-003 rested on FTS5 shipping inside SQLite, needing no extra
  dependency. [ADR-0013](adr-0013-postgres-for-local-and-hosted.md) moves the store to
  PostgreSQL, where `tsvector` and `pgvector` are both in the engine already. The
  "additional dependency" the deferral priced no longer exists.
- **CON-002**: ADR-0005 CON-002 priced embedding as an ingestion cost — API calls or a
  local model on every upload. That cost is real and unchanged, but it is now a **local
  model** decision rather than an inevitable API bill, and it is paid once per document
  rather than per query.
- **CON-003**: Keyword retrieval has a known failure mode that this corpus will hit:
  paraphrase. A game master asking *"what happens if I walk away from a monster"* will not
  match a chunk that only says *"opportunity attack"* (ADR-0005 NEG-001).
- **CON-004**: Keyword retrieval also has a genuine strength this corpus depends on. Proper
  nouns and rules notation — *Ahroay'if*, *2D6+2*, *the Pale Court* — are exactly where
  embeddings retrieve semantically adjacent but factually wrong passages, and where keyword
  matching wins (ADR-0005 POS-003). **Neither half is sufficient alone.**
- **CON-005**: Grounding requires that retrieval either finds supporting material or
  reports that it did not (PRIN-001, AC-003). A retriever that always returns its nearest
  neighbours — which a pure vector search does — makes refusal harder, because there is
  always something to show.

## Decision

**Retrieval is hybrid: PostgreSQL full-text (`tsvector`) and vector similarity
(`pgvector`), fused with reciprocal rank fusion.** Source chunks are embedded at ingestion
and stored alongside their text in the same table.

- Each chunk carries its text, its `tsvector`, and its embedding — one row, one store.
- Both retrievers run per query; rankings are fused with RRF rather than by a tuned weight.
- A **relevance floor** applies: results below it are treated as no result, so Research
  mode still refuses rather than answering from weak matches (CON-005, AC-003).
- **Embedding runs on a local model at ingestion.** It is deterministic in the sense that
  matters to [ADR-0002](adr-0002-deterministic-extraction.md): it derives from the
  document's own text and invents nothing. It does not make ingestion a generative step.

Reranking a fused candidate set with a cross-encoder is **not** adopted here. It is the
obvious next lever, but it adds a second model to the query path and should be justified
against the evaluation set rather than assumed (IMP-004).

## Consequences

### Positive

- **POS-001**: Paraphrase and terminology are both served. The fusion covers ADR-0005
  NEG-001 and NEG-002 without giving up POS-003's exact-term strength.
- **POS-002**: One store, one transaction. Chunk text, keyword index, and vector live in
  the same row — no cross-store consistency problem, and no separate vector service.
- **POS-003**: Citations are unaffected. A fused result is still a chunk with a page span,
  so the citation path stays exactly as designed.
- **POS-004**: The relevance floor makes refusal a property of retrieval rather than of
  prompting alone, which is where it is most reliable.

### Negative

- **NEG-001**: Ingestion is slower and heavier. Every chunk is embedded, which reintroduces
  the per-document cost ADR-0005 POS-001 avoided, plus an embedding model as a dependency.
- **NEG-002**: Two retrievers are harder to reason about than one. When a result is wrong,
  the cause may be either half or the fusion between them.
- **NEG-003**: The relevance floor is a tuned number, and tuning it wrong is a silent
  failure in both directions — refusing when material exists, or answering from noise.
- **NEG-004**: Re-embedding is required if the embedding model changes, which makes the
  model choice a migration concern rather than a swap.

## Alternatives Considered

### Keep FTS-only until measured to fail (ADR-0005 unchanged)

- **ALT-001**: **Description**: Retain keyword-only retrieval and its revisit trigger.
- **ALT-002**: **Rejection Reason**: The trigger's premise was that vectors cost a
  dependency and a store. Under ADR-0013 they cost neither, so waiting now buys only a
  delay — and ADR-0005 IMP-004 itself warned that "measure first" silently becomes "never
  revisit" without the instrumentation nobody has built yet.

### Vector-only retrieval

- **ALT-003**: **Description**: Embed chunks and retrieve purely by similarity.
- **ALT-004**: **Rejection Reason**: Loses exactly what this corpus needs most. Rules
  notation and proper nouns are where embeddings return plausible-but-wrong neighbours,
  and near-miss answers to rules questions are actively harmful (ADR-0005 ALT-002).

### Hybrid plus cross-encoder reranking from day one

- **ALT-005**: **Description**: Fuse, then rerank the top candidates with a cross-encoder.
- **ALT-006**: **Rejection Reason**: Likely the largest single quality gain available, but
  it puts a second model in the live query path (PRIN-003 — the session is the priority)
  and its benefit over RRF is unmeasured here. Adopt it against the evaluation set, not
  ahead of it.

### A dedicated vector database (Qdrant, Weaviate, Chroma)

- **ALT-007**: **Description**: Run a purpose-built vector store beside PostgreSQL.
- **ALT-008**: **Rejection Reason**: Reintroduces the multi-store consistency burden
  ADR-0003 and ADR-0013 both avoid, for corpus sizes — a few rulebooks per campaign — where
  `pgvector` is not the bottleneck. Revisit on measured recall or latency, not on scale
  anxiety.

## Implementation Notes

- **IMP-001**: Retrieval stays behind one interface (carried over from ADR-0005 IMP-001),
  so fusion strategy and floor are internal details.
- **IMP-002**: Chunk rows carry `embedding vector(n)` and `tsv tsvector` alongside
  `content`. See `docs/data-model.md`.
- **IMP-003**: Deduplicate by content hash at upload. The same file uploaded twice must not
  be extracted or embedded twice — pure cost with no benefit.
- **IMP-004**: Build the evaluation set of question/expected-chunk pairs (carried over from
  ADR-0005 IMP-005). It is now load-bearing for two decisions: tuning the relevance floor,
  and judging whether reranking (ALT-005) earns its place.
- **IMP-005**: Log queries returning nothing or rejected answers (carried over from
  ADR-0005 IMP-004). Under hybrid retrieval this is the only way to tell a floor set too
  high from a corpus genuinely lacking the answer.
- **IMP-006**: Chunk on paragraph and heading boundaries with overlap, not fixed character
  counts. Boundaries that split a sentence degrade both retrievers at once.
- **IMP-007**: Detect scanned pages — a page yielding almost no characters is an image, not
  an empty page — and route to the `awaiting OCR` state rather than `failed`.
- **IMP-008**: Embedding is part of ingestion and therefore inside BND-001's boundary: an
  embedding model is not a language model writing campaign content. The boundary test
  asserts no *generative* model is reachable from ingestion, not that no model is.

## References

- **REF-001**: [ADR-0005](adr-0005-fts5-before-vectors.md) — superseded by this record
- **REF-002**: [ADR-0013](adr-0013-postgres-for-local-and-hosted.md) — the store that enables this
- **REF-003**: [ADR-0002](adr-0002-deterministic-extraction.md) — deterministic ingestion
- **REF-004**: `docs/architecture.md` — retrieval and grounding flow

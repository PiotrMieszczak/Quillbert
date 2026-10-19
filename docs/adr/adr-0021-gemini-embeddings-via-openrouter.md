---
title: "ADR-0021: Hybrid retrieval with Gemini Embedding 2, reached through OpenRouter"
status: "Accepted"
date: "2026-10-19"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "retrieval", "embeddings", "search", "privacy"]
supersedes: "ADR-0016"
superseded_by: ""
---

# ADR-0021: Hybrid retrieval with Gemini Embedding 2, reached through OpenRouter

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[ADR-0016](adr-0016-voyage-embeddings.md) decided hybrid retrieval with one fixed hosted
embedding model, Voyage `voyage-4`, called through its own SDK and its own account. Its
hybrid design, fixed-model rule, and degrade-don't-fail rule stand. The provider does not,
for reasons that arrived with [ADR-0019](adr-0019-openrouter-privacy-routing.md):

- **CON-001**: ADR-0019 made OpenRouter the single route to every model, under a
  zero-retention allowlist, so that privacy is enforced in one place. A second vendor for
  embeddings means a second account, key, privacy opt-out, and failure mode.
- **CON-002**: ADR-0016 CON-005 recorded that Voyage trains on inputs by default and the
  opt-out needs an organization admin with a payment method and is irreversible. OpenRouter
  states per endpoint whether it is zero-retention, and exposes it as a routing filter.
- **CON-003**: ADR-0016 ALT-003 rejected Gemini on price (~$0.20/M against $0.06/M). At
  this scale the gap is cents: a typical campaign (about 1,500 pages, ~1.15M tokens with
  chunk overlap) costs ~$0.25 to embed, against ~$0.07.
- **CON-004**: Questions and material can be in different languages (Polish questions,
  English rulebooks). `gemini-embedding-2` is documented as supporting over 100 languages.
- **CON-005**: The remaining constraints of ADR-0016 (CON-001, CON-002, CON-006) are
  unchanged.

## Decision

**Retrieval stays hybrid exactly as ADR-0016 decided. Embeddings come from one fixed model,
`google/gemini-embedding-2` at 1024 dimensions, reached through OpenRouter on a pinned
zero-retention endpoint, behind an `Embedder` port.**

Carried over from ADR-0016 unchanged:

- Each chunk row carries its text, its `tsvector`, and its embedding: one row, one store.
- Both retrievers run per query; rankings are fused with RRF, not a tuned weight.
- A relevance floor applies: results below it are no result, so Research mode refuses.
- One model for every user and campaign. It is not a Settings choice and not part of the
  Gateway's model resolution (ADR-0019), which applies to the chat model only.
- The model is recorded with the vectors (`embedding_space`), and the backend refuses to
  start embedding with a different one. Changing model is a re-embed migration.
- If embedding a question fails, the query runs keyword-only and logs it. If embedding a
  chunk fails during ingestion, the document stays `processing` and retries; a provider
  outage is not `failed`.
- Embedding derives vectors from the document's own text and writes no content, so it is
  not a *generative* model in the sense of BND-001.

New:

1. **Model and size.** `google/gemini-embedding-2`, requested at `dimensions: 1024` (the
   model supports 128 to 3072 and normalizes truncated sizes). The `vector(1024)` column
   and its index are unchanged.
2. **Task by prefix.** The model has no `task_type`. Queries are sent as
   `task: search result | query: {text}` and documents as `title: none | text: {text}`.
3. **Pinned, fail-closed routing.** Every request carries
   `provider: {only: ["google-vertex/eu"], zdr: true, allow_fallbacks: false}`. OpenRouter
   refuses (404) rather than route to Google AI Studio, which retains data. The endpoint is
   configuration (`EMBEDDING_PROVIDER`); the EU endpoint is the default because the database
   is in `eu-west-3`. `data_collection: deny` is **not** used: measured below, it removes
   Vertex from the candidates.
4. **One text per request.** On zero-retention Vertex this model accepts a single input; a
   batch of two or more is routed only to AI Studio and is refused by `zdr`. The adapter
   therefore sends one request per text, eight at a time.
5. **Behind a port.** `Embedder.embed(texts, purpose) → vectors`, with an OpenRouter adapter
   and a deterministic fake, both under `adapters/llm/` (BND-002).
6. **Key.** `OPEN_ROUTER_API_KEY`, as ADR-0019 IMP-006; no second key.

## Consequences

### Positive

- **POS-001**: Paraphrase and terminology are both served (carried over).
- **POS-002**: One store, one transaction; no separate vector service (carried over).
- **POS-003**: Citations are unaffected: a fused hit is still a chunk (carried over).
- **POS-004**: The relevance floor makes refusal a property of retrieval (carried over).
- **POS-005**: One vendor, one key, one privacy control for every model call. Retention is
  refused by routing, not promised by a setting someone must remember to flip.
- **POS-006**: The worker carries no model, as in ADR-0016.
- **POS-007**: Cross-language retrieval works: in a spike, a Polish question scored 0.75
  against the matching English rule and 0.54 against an unrelated passage.
- **POS-008**: Vectors can never silently mix models (carried over).

### Negative

- **NEG-001**: Ingestion depends on OpenRouter and Google. An outage delays indexing; the
  document stays queued. OpenRouter is now a single point of failure for chat and
  embeddings (ADR-0019 NEG-001).
- **NEG-002**: Two retrievers are harder to reason about than one (carried over).
- **NEG-003**: The relevance floor is a tuned number (carried over). Gemini cosines differ
  from Voyage's, so any floor must be tuned on this model.
- **NEG-004**: Changing the model means re-embedding every chunk, paid per token.
- **NEG-005**: Document text and every question leave our infrastructure. Zero retention
  limits storage, not transmission.
- **NEG-006**: One request per chunk: a typical campaign is a few thousand requests, a few
  minutes at eight in parallel (40 requests in 3.9 s measured). The input limit is 8,192
  tokens and longer text is silently truncated, so chunks must stay well under it.
- **NEG-007**: A pinned endpoint name is a dependency on OpenRouter's naming. If Google
  retires it, requests are refused (fail closed) until the setting changes.
- **NEG-008**: About three times Voyage's price per token ($0.22/M on the EU endpoint).

## Alternatives Considered

### Keep Voyage (ADR-0016)

- **ALT-001**: **Description**: Voyage `voyage-4` through its SDK, with the account opt-out.
- **ALT-002**: **Rejection Reason**: Cheaper, but a second vendor, key, and irreversible
  admin opt-out to hold the same privacy line OpenRouter already enforces per request
  (CON-001, CON-002).

### `google/gemini-embedding-001`

- **ALT-003**: **Description**: The older Gemini model. $0.15/M, batches on Vertex.
- **ALT-004**: **Rejection Reason**: No `task_type` is exposed through OpenRouter, so queries
  and documents could not be embedded asymmetrically, and its multilingual coverage is not
  stated in Google's documentation. Vectors at 1024 dimensions also need manual
  normalization. The batching it allows does not outweigh the retrieval quality.

### `data_collection: "deny"` instead of `zdr`

- **ALT-005**: **Description**: Use OpenRouter's "no data collection" filter.
- **ALT-006**: **Rejection Reason**: Measured: with `deny`, the Vertex endpoints were not
  candidates and the request was served by Google AI Studio. `zdr` is the stricter filter
  and keeps Vertex.

### Local model, or a user-selectable model

- **ALT-007**: **Description**: As ADR-0016 ALT-001 and ALT-005.
- **ALT-008**: **Rejection Reason**: Unchanged from ADR-0016 (hosted product; vectors from
  two models are not comparable).

## Implementation Notes

- **IMP-001**: Retrieval stays behind one interface; fusion and floor are internal
  (carried over).
- **IMP-002**: Chunk rows carry `embedding vector(1024)` and `tsv tsvector` alongside
  `content`. See `docs/data-model.md`.
- **IMP-003**: Deduplicate by content hash at upload; the same file is never extracted or
  embedded twice (carried over). With a paid API this is also a cost control.
- **IMP-004**: Build the evaluation set of question/expected-chunk pairs, including Polish
  questions against English material. It tunes the floor, confirms 1024 against other
  sizes, and judges reranking (carried over).
- **IMP-005**: Log queries returning nothing, rejected answers, and keyword-only fallbacks
  (carried over).
- **IMP-006**: Chunk on paragraph and heading boundaries with overlap (carried over).
- **IMP-007**: Detect scanned pages and route them to `awaiting OCR`, not `failed`
  (carried over).
- **IMP-008**: Embedding is inside BND-001's boundary; the boundary test asserts no
  *generative* model is reachable from ingestion (carried over).
- **IMP-009**: `OPEN_ROUTER_API_KEY` comes from the environment, never the database or the
  client. With it unset, the backend uses the fake embedder and logs a warning.
- **IMP-010**: Concurrency is bounded at eight requests; 429 and 5xx are retried three
  times with backoff, then surface as `EmbeddingUnavailable`. A 404 is a refusal and is not
  retried.
- **IMP-011**: Keyword search's text-search configuration is per document language;
  PostgreSQL has no built-in Polish configuration, so Polish text uses `simple` until one
  is added (carried over).
- **IMP-012**: Revisit trigger: OpenRouter or Google change the zero-retention endpoints or
  batching, prices move by an order of magnitude, or the evaluation set favors another model.
- **IMP-013**: Also set OpenRouter's account-level "ZDR only" privacy setting
  (openrouter.ai/settings/privacy) as a second layer behind the request-level pin.

## References

- **REF-001**: [ADR-0016](adr-0016-voyage-embeddings.md) — superseded; the hybrid design
  and rules this record carries forward
- **REF-002**: [ADR-0019](adr-0019-openrouter-privacy-routing.md) — OpenRouter and the
  zero-retention allowlist this extends to embeddings
- **REF-003**: [ADR-0002](adr-0002-deterministic-extraction.md) — the ingestion boundary
  IMP-008 keeps intact
- **REF-004**: [OpenRouter embeddings](https://openrouter.ai/docs/api-reference/embeddings),
  [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection),
  [Gemini embeddings](https://ai.google.dev/gemini-api/docs/embeddings)

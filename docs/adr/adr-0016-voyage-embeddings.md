---
title: "ADR-0016: Hybrid retrieval with one fixed hosted embedding model (Voyage)"
status: "Accepted"
date: "2026-10-10"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "retrieval", "embeddings", "search"]
supersedes: "ADR-0014"
superseded_by: ""
---

# ADR-0016: Hybrid retrieval with one fixed hosted embedding model (Voyage)

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[ADR-0014](adr-0014-hybrid-retrieval.md) decided hybrid retrieval — PostgreSQL full-text
plus `pgvector`, fused with reciprocal rank fusion, behind a relevance floor — and that
**"embedding runs on a local model at ingestion"**. The hybrid design stands. The local
model does not, for reasons ADR-0014 did not weigh:

- **CON-001**: The product's target is a hosted, multi-user service. An embedding model in
  the worker puts model weights in the image and a CPU-bound step on every upload burst.
  Scaling ingestion then means scaling model compute ourselves.
- **CON-002**: Every vector in the store must come from the **same model**. Vectors from
  two models are not comparable, so the model cannot be a per-user or per-campaign choice,
  and it cannot be part of the assistant's provider switching
  ([ADR-0006](adr-0006-llm-gateway.md), AC-004), which is a per-message decision.
- **CON-003**: Material and questions may be in more than one language — English rulebooks,
  Polish questions or notes. An English-only model cannot match a Polish question to an
  English passage.
- **CON-004**: Hosted embedding is cheap at this scale. A 300-page rulebook is about 200k
  tokens: roughly $0.012 at `voyage-4`'s $0.06 per million, inside a 200M-token free
  allowance per account ([Voyage pricing](https://docs.voyageai.com/docs/pricing)).
- **CON-005**: By default Voyage may store API inputs and use them for training. Customers
  can opt out, which gives zero-day retention on hosted endpoints; opting out requires an
  organization admin with a payment method, and is irreversible
  ([Voyage FAQ](https://docs.voyageai.com/docs/faq)). Users upload purchased, copyrighted
  rulebooks and private campaign notes.
- **CON-006**: Keyword retrieval's strengths and paraphrase weakness, and the need for a
  retriever that can return *nothing* so Research mode can refuse (PRIN-001, AC-003), are
  unchanged from ADR-0014 CON-003 to CON-005.

## Decision

**Retrieval stays hybrid exactly as ADR-0014 decided. Embeddings come from one fixed,
hosted, multilingual model — Voyage `voyage-4` at 1024 dimensions — for every user and
every campaign, reached through an `Embedder` port.**

Carried over from ADR-0014 unchanged:

- Each chunk row carries its text, its `tsvector`, and its embedding — one row, one store.
- Both retrievers run per query; rankings are fused with RRF, not a tuned weight.
- A relevance floor applies: results below it are no result, so Research mode refuses.

New:

1. **One model, fixed.** `voyage-4`, 1024 dimensions, used for documents and questions
   alike. It is not configurable in Settings and is not part of provider switching, which
   applies to the assistant's chat model only (ADR-0006).
2. **The model is recorded with the vectors.** A metadata record names the model and
   dimension that produced the stored embeddings. Startup refuses to embed with a different
   model than the store records. Changing model is a deliberate re-embed migration.
3. **Behind a port.** `Embedder` (`embed(texts, purpose) → vectors`, purpose being
   document or query) with a Voyage adapter and a deterministic fake for tests. The
   Voyage SDK is imported only in that adapter, enforced like BND-002.
4. **Opt-out before real data.** The Voyage organization opts out of storage and training
   (zero-day retention) before the first real document is embedded. Development uses the
   fake adapter or test documents until then.
5. **Degrade, don't fail.** If embedding a question fails, the query runs keyword-only and
   logs it. If embedding a chunk fails during ingestion, the document stays `processing`
   and retries with backoff; it is not marked `failed` for a provider outage.
6. **Still deterministic in the sense that matters.** An embedding model derives vectors
   from the document's own text and writes no content. BND-001 bars a *generative* model
   from ingestion; this is not one (ADR-0014 IMP-008, carried over).

## Consequences

### Positive

- **POS-001**: Paraphrase and terminology are both served (carried over).
- **POS-002**: One store, one transaction; no separate vector service (carried over).
- **POS-003**: Citations are unaffected: a fused hit is still a chunk (carried over).
- **POS-004**: The relevance floor makes refusal a property of retrieval (carried over).
- **POS-005**: The worker carries no model. Ingestion scales by adding cheap workers, and
  the backend image stays small.
- **POS-006**: Cross-language retrieval works: a Polish question can find an English
  passage.
- **POS-007**: Vectors can never silently mix models; the store knows what produced them.

### Negative

- **NEG-001**: Ingestion depends on a third party. An outage delays indexing (decision 5
  keeps documents queued rather than failed).
- **NEG-002**: Two retrievers are harder to reason about than one (carried over).
- **NEG-003**: The relevance floor is a tuned number; tuning it wrong fails silently in
  both directions (carried over).
- **NEG-004**: Changing the model means re-embedding every chunk, now also paid per token.
- **NEG-005**: Document text and every question leave our infrastructure. The opt-out
  (decision 4) limits retention, not transmission.
- **NEG-006**: Local mode ([ADR-0013](adr-0013-postgres-for-local-and-hosted.md)) is no
  longer fully offline: uploading needs the network, and search without it is
  keyword-only.
- **NEG-007**: A provider-specific dimension (1024) is baked into the column type.

## Alternatives Considered

### Local model in the worker (ADR-0014's choice)

- **ALT-001**: **Description**: `multilingual-e5-small` or similar, run in-process via
  `fastembed`. Free, offline, private.
- **ALT-002**: **Rejection Reason**: Fails CON-001 for a hosted product, and multilingual
  quality at a CPU-friendly size trails the hosted option. Remains the fallback if the
  privacy trade (NEG-005) becomes unacceptable.

### Other hosted providers

- **ALT-003**: **Description**: OpenAI `text-embedding-3-small` (~$0.02/M, weaker across
  languages), Gemini Embedding (~$0.20/M), Z.AI (no embedding model on its international
  platform), `voyage-4-lite` (cheapest Voyage, not described as multilingual).
- **ALT-004**: **Rejection Reason**: `voyage-4` is the cheapest option explicitly built for
  multilingual retrieval, and Anthropic's recommended embedding partner, which keeps
  vendors aligned with the chat provider.

### Let users or deployments choose the embedding model

- **ALT-005**: **Description**: Make the model a setting, like the chat provider.
- **ALT-006**: **Rejection Reason**: Fails CON-002. A store with vectors from two models
  returns meaningless distances.

## Implementation Notes

- **IMP-001**: Retrieval stays behind one interface; fusion and floor are internal
  (carried over).
- **IMP-002**: Chunk rows carry `embedding vector(1024)` and `tsv tsvector` alongside
  `content`. See `docs/data-model.md`.
- **IMP-003**: Deduplicate by content hash at upload; the same file is never extracted or
  embedded twice (carried over). With a paid API this is also a cost control.
- **IMP-004**: Build the evaluation set of question/expected-chunk pairs, including
  Polish questions against English material. It tunes the floor, confirms 1024 against
  512 dimensions, and judges reranking (carried over, extended).
- **IMP-005**: Log queries returning nothing, rejected answers, and keyword-only fallbacks
  (carried over, extended).
- **IMP-006**: Chunk on paragraph and heading boundaries with overlap (carried over).
- **IMP-007**: Detect scanned pages and route them to `awaiting OCR`, not `failed`
  (carried over).
- **IMP-008**: Embedding is inside BND-001's boundary; the boundary test asserts no
  *generative* model is reachable from ingestion (carried over).
- **IMP-009**: `VOYAGE_API_KEY` comes from the environment, never the database or the
  client (same rule as ADR-0006 IMP-006).
- **IMP-010**: Batch chunk embedding per request, and use Voyage's batch endpoint for
  large backfills or re-embeds.
- **IMP-011**: Keyword search's text-search configuration is per document language;
  PostgreSQL has no built-in Polish configuration, so Polish text uses `simple` until one
  is added. Vector search is unaffected.
- **IMP-012**: Revisit trigger — Voyage changes its retention terms, prices move by an
  order of magnitude, or a local model matches `voyage-4` on the evaluation set.

## References

- **REF-001**: [ADR-0014](adr-0014-hybrid-retrieval.md) — superseded; the hybrid design
  this record carries forward
- **REF-002**: [Voyage pricing](https://docs.voyageai.com/docs/pricing),
  [embeddings](https://docs.voyageai.com/docs/embeddings),
  [FAQ: training opt-out](https://docs.voyageai.com/docs/faq)
- **REF-003**: [ADR-0006](adr-0006-llm-gateway.md) — provider switching, which this record
  excludes embeddings from
- **REF-004**: [ADR-0002](adr-0002-deterministic-extraction.md) — the ingestion boundary
  IMP-008 keeps intact

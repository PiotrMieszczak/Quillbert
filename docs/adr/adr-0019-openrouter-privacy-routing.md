---
title: "ADR-0019: OpenRouter as the single provider, with a zero-retention allowlist"
status: "Accepted"
date: "2026-10-12"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "ai", "gateway", "providers", "privacy"]
supersedes: "ADR-0006"
superseded_by: ""
---

# ADR-0019: OpenRouter as the single provider, with a zero-retention allowlist

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[ADR-0006](adr-0006-llm-gateway.md) established the LLM Gateway and chose two native
providers — **Claude** and **Ollama** — behind one provider-agnostic interface, with
runtime switching from Settings. Its ALT-003/004 **rejected** a third-party abstraction
(LiteLLM, LangChain) on the grounds that two providers and one call shape did not justify
it, with an explicit revisit clause: *"Revisit if the provider count grows substantially."*

Two premises have moved:

- **CON-001**: The MVP is now hosted-first
  ([ADR-0018](adr-0018-hosted-first-local-v2.md)). ADR-0006 CON-004's justification for a
  local provider — *"a user may run entirely offline via Ollama"* — no longer applies to
  v1. Ollama defers to v2 with local deployment.
- **CON-002**: The binding requirement on model access is now **data privacy**: only
  providers that do not train on, or retain, the prompts and documents sent to them are
  acceptable (for example Google Vertex). This is a GM's own campaign material and, through
  it, their players' data.
- **CON-003**: Reaching several zero-retention backends — and switching among them at
  runtime (ADR-0006 CON-001, the design's provider control) — through one integration is
  exactly the "provider count grows substantially" condition ADR-0006 ALT-004 named. One
  routing API replaces N native adapters.
- **CON-004**: OpenRouter is a hosted routing **API**, not a code abstraction library. It
  is reached through our own single adapter inside the Gateway; it does not own prompt
  assembly or streaming. ADR-0006 ALT-004's actual concern — a dependency that takes over
  the abstraction and moves the grounding prompt out of our control — does not apply.
- **CON-005**: The Gateway's core properties from ADR-0006 — one interface, no provider
  SDK outside the Gateway (BND-002), the grounding prompt owned in one place (PRIN-001),
  normalized streaming, availability reporting — are correct and are retained unchanged.

## Decision

**The Gateway's single provider is OpenRouter, configured to route only to an allowlist of
zero-data-retention backends.** The Gateway abstraction from ADR-0006 is kept; only the
provider behind it changes.

- **One adapter**: OpenRouter is the only provider adapter in `adapters/llm/` for v1
  (beside the `fake` test provider). No direct Anthropic or Ollama adapter ships in v1.
  Claude, if used, is reached as an OpenRouter model route.
- **Zero-retention allowlist**: the Gateway sends requests only to OpenRouter model routes
  whose provider has a no-training, no-retention data policy (e.g. Vertex-backed models).
  Routing to any provider outside the allowlist is refused, not silently downgraded
  (CON-002).
- **Model selection is not a user-facing control.** The active model is set by admin/env
  configuration; the Gateway resolves it per request (ADR-0006 CON-001's runtime
  resolution), so changing the configured model serves the next message with no code
  change. Each assistant mode may also prefer a model through its profile (ADR-0012
  IMP-001). There is no provider or model picker in the UI.
- **The Gateway still owns** the single `complete(messages, context, stream)` interface,
  streaming normalization, the grounding prompt (PRIN-001), availability reporting, and
  cost/latency instrumentation — all unchanged from ADR-0006.

## Consequences

### Positive

- **POS-001**: Many privacy-safe models reachable through one integration, with runtime
  switching, without writing and maintaining an adapter per provider (addresses ADR-0006
  ALT-004's revisit condition directly).
- **POS-002**: Data privacy is an enforced property, not a hope — the allowlist is the
  mechanism, and routing outside it fails closed (CON-002).
- **POS-003**: The Gateway's one-interface, one-grounding-prompt, no-SDK-leak guarantees
  (BND-002, PRIN-001) survive intact; the frontend and call sites are unaffected.
- **POS-004**: A single hosted provider matches the hosted-first MVP
  ([ADR-0018](adr-0018-hosted-first-local-v2.md)); there is no local-reachability state to
  handle in v1 beyond OpenRouter being reachable.

### Negative

- **NEG-001**: A dependency on one external routing service. If OpenRouter is down, the
  assistant is down — availability reporting (retained from ADR-0006 POS-005) surfaces it,
  but there is no local fallback in v1.
- **NEG-002**: No fully-offline operation in v1. ADR-0006 CON-004's offline path moves to
  v2 with Ollama and local deployment ([ADR-0018](adr-0018-hosted-first-local-v2.md)).
- **NEG-003**: The design had to change. The Settings screen previously drew **Claude** and
  **Ollama** radio rows; the written design ([docs/design/overview.md](../design/overview.md))
  now removes the provider selector entirely and shows the current *mode* in the panel
  header (ADR-0012 IMP-005). The external interactive prototype still shows the old rows
  until it is re-exported (BND-004 — the prototype is a reference, not imported).
- **NEG-004**: OpenRouter's own routing adds a hop and its own failure modes (a model
  route deprecated upstream, price/latency drift between backends) that a direct adapter
  would not have.

### Neutral

- **NEU-001**: ADR-0006's reasons for having a Gateway at all are unchanged and still
  correct; this record changes what sits behind it, not whether it exists.

## Alternatives Considered

### Keep native Claude + Ollama adapters (ADR-0006 as written)

- **ALT-001**: **Description**: Two hand-written adapters, as ADR-0006 decided.
- **ALT-002**: **Rejection Reason**: Ollama's justification (offline) is gone in a
  hosted-first MVP, and a privacy allowlist spanning several backends would mean writing an
  adapter per backend — the exact growth ADR-0006 ALT-004 said to revisit on.

### OpenRouter *plus* a direct Claude adapter

- **ALT-003**: **Description**: Keep a first-class direct Anthropic adapter and add
  OpenRouter alongside it for the privacy-routed models.
- **ALT-004**: **Rejection Reason**: Two code paths to the same capability for no v1
  benefit — Anthropic is reachable as an OpenRouter route under the same zero-retention
  policy. A direct adapter is a v2 option if a capability is needed that routing cannot
  expose (ADR-0006 NEG-001).

### A third-party abstraction library (LiteLLM, LangChain)

- **ALT-005**: **Description**: Adopt a client library that owns multi-provider calls.
- **ALT-006**: **Rejection Reason**: Unchanged from ADR-0006 ALT-004 — a library that owns
  prompt assembly would move the grounding prompt out of the Gateway (PRIN-001). OpenRouter
  is an API behind our own adapter, which is categorically different.

## Implementation Notes

- **IMP-001**: The OpenRouter adapter is the only file importing an OpenRouter client; the
  architectural test from ADR-0006 IMP-004 (no provider SDK imported outside the Gateway,
  BND-002) is retained, now asserted against this adapter.
- **IMP-002**: The grounding prompt is constructed in the Gateway and is identical across
  whichever allowlisted model serves the request (ADR-0006 IMP-002, PRIN-001).
- **IMP-003**: The allowlist is configuration, and the Gateway **fails closed** — a request
  that would route to a non-allowlisted provider is refused. A test asserts a
  non-allowlisted route is never sent (the privacy equivalent of ADR-0006 IMP-005's
  refusal test).
- **IMP-004**: OpenRouter's provider-routing / data-policy controls are set so a request
  can only be fulfilled by a zero-retention backend, never silently fall through to one
  that trains on data (CON-002).
- **IMP-005**: Revisit trigger — a native local provider (Ollama) returns in v2 with local
  deployment ([ADR-0018](adr-0018-hosted-first-local-v2.md) IMP-004); a native direct
  adapter returns if a needed capability cannot be reached through routing (ALT-004).
- **IMP-006**: The OpenRouter API key comes from environment configuration as
  `OPEN_ROUTER_API_KEY`, supplied in CI from a **GitHub Actions secret** (not an Actions
  variable — a variable stores the value in plaintext, readable with repo access). It is
  never sent to the frontend; Settings shows gateway availability and the active model
  (read-only), never credentials (ADR-0006 IMP-006).

## References

- **REF-001**: [ADR-0006](adr-0006-llm-gateway.md) — superseded by this record; its Gateway
  decision is retained, its Claude+Ollama provider set is not
- **REF-002**: [ADR-0018](adr-0018-hosted-first-local-v2.md) — the hosted-first MVP this
  pairs with; the local model provider defers together with local deployment
- **REF-003**: `docs/product-brief.md` PRIN-001 — the grounding rule still enforced in the
  Gateway
- **REF-004**: `docs/design/overview.md` — updated: provider selector removed, panel shows
  the current mode (NEG-003)
- **REF-005**: `docs/api-contract.md` — the read-only `/settings/ai` surface (no user-facing
  provider or model picker)

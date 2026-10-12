---
title: "ADR-0006: Centralized LLM Gateway with runtime provider switching"
status: "Superseded"
date: "2026-07-31"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "ai", "gateway", "providers"]
supersedes: ""
superseded_by: "ADR-0019"
---

# ADR-0006: Centralized LLM Gateway with runtime provider switching

## Status

Proposed | Accepted | Rejected | **Superseded** | Deprecated

> Superseded by [ADR-0019](adr-0019-openrouter-privacy-routing.md). The Gateway decision
> itself — one interface, no SDK outside the Gateway (BND-002), the grounding prompt owned
> in one place — is **retained**. What changed is the provider set: the MVP is hosted-first
> ([ADR-0018](adr-0018-hosted-first-local-v2.md)), so the offline justification for Ollama
> (CON-004) no longer holds in v1, and the binding requirement became data privacy. The
> single provider is now OpenRouter with a zero-retention allowlist, which is the
> "provider count grows substantially" revisit that ALT-004 named.

## Context

The assistant needs a language model. The design's Settings screen presents provider
selection as a first-class user choice — **Claude** and **Ollama** — with a green-tinted
callout explaining that requests route through a gateway. The AI panel header shows the
active provider in a pill that switches on click.

Provider choice is therefore a product feature, not a deployment detail.

Constraints:

- **CON-001**: The design requires switching providers from the UI at runtime, with no
  restart.
- **CON-002**: Ollama runs locally and may be unreachable; Claude requires an API key and
  network access. Availability differs and must be surfaced.
- **CON-003**: Providers differ in API shape, streaming format, context window, and
  capability. The application should not encode these differences at call sites.
- **CON-004**: Local-first operation (PRIN-004) means a user may run entirely offline via
  Ollama, or use Claude for quality. Both are legitimate.
- **CON-005**: Grounding rules (PRIN-001) must hold identically regardless of provider.

## Decision

All model access goes through a **single Gateway module** (`backend/app/gateway/`)
exposing one provider-agnostic interface. No provider SDK is imported anywhere else in
the codebase (BND-002).

The gateway:

1. Presents one `complete(messages, context, stream)` interface to callers.
2. Normalizes streaming into a single internal event shape (token, tool, done).
3. Resolves the active provider per request from settings, so switching takes effect on
   the next message.
4. Reports provider availability for the Settings screen.
5. Owns the grounding prompt, so PRIN-001 is enforced in one place for all providers.

## Consequences

### Positive

- **POS-001**: Switching providers is configuration, not code. AC-004 is satisfied
  directly by the design's Settings control.
- **POS-002**: The grounding rule lives in exactly one place. A provider cannot be added
  that quietly bypasses the requirement to answer only from context.
- **POS-003**: Adding a provider means implementing one adapter interface; nothing else
  in the application changes.
- **POS-004**: Streaming normalization means the SSE contract in `api-contract.md` is
  stable across providers, so the frontend never branches on provider.
- **POS-005**: Availability checking gives Settings honest state rather than failing at
  send time (CON-002).
- **POS-006**: Cost and latency instrumentation has one natural home.

### Negative

- **NEG-001**: The interface is a lowest common denominator. Provider-specific
  capabilities are either unavailable or need explicit capability flags.
- **NEG-002**: An extra indirection layer to traverse when debugging.
- **NEG-003**: Behaviour still differs across providers even behind one interface — a
  local 7B model and Claude produce materially different answers to the same prompt.
  The gateway unifies the interface, not the quality.
- **NEG-004**: Prompt tuning that helps one provider may hurt another, and the single
  grounding prompt must work acceptably for both.

## Alternatives Considered

### Direct provider SDK calls at each call site

- **ALT-001**: **Description**: Import the Anthropic SDK or an Ollama client wherever a
  model is needed.
- **ALT-002**: **Rejection Reason**: Makes runtime switching (CON-001) impractical and
  scatters the grounding prompt, so PRIN-001 becomes unenforceable by construction — the
  exact failure this architecture is designed to prevent.

### A third-party abstraction library (LiteLLM, LangChain)

- **ALT-003**: **Description**: Adopt an existing multi-provider abstraction.
- **ALT-004**: **Rejection Reason**: Two providers and one call shape do not justify a
  large dependency with its own abstractions and upgrade cadence. The adapter is small
  enough to own outright, and owning it keeps the grounding prompt and streaming contract
  under direct control. Revisit if the provider count grows substantially.

### Single provider (Claude only)

- **ALT-005**: **Description**: Support Claude alone and drop the provider selector.
- **ALT-006**: **Rejection Reason**: Contradicts the design, which presents provider
  choice as a user-facing feature, and forecloses fully-offline operation (CON-004).

## Implementation Notes

- **IMP-001**: The adapter interface covers completion, streaming, and an availability
  probe. Anything provider-specific is expressed as a capability flag, not a leaked type.
- **IMP-002**: The grounding prompt — supplied context, plus the instruction to state
  when context is insufficient — is constructed in the gateway and is identical across
  providers.
- **IMP-003**: Availability probing is cheap and cached briefly, so Settings stays
  responsive without hammering an unreachable Ollama.
- **IMP-004**: An architectural test asserts no module outside `gateway/` imports a
  provider SDK (BND-002), the same enforcement pattern as BND-001.
- **IMP-005**: Refusal behaviour (AC-003) is tested against **both** providers. A weaker
  local model is more likely to answer unsourced, so passing on Claude alone is not
  evidence (addresses NEG-003).
- **IMP-006**: API keys come from environment configuration and are never sent to the
  frontend; the Settings screen shows availability, never credentials.

## References

- **REF-001**: [ADR-0002](adr-0002-deterministic-extraction.md) — the ingestion boundary
  this complements; models are used here and nowhere else
- **REF-002**: `docs/api-contract.md` — SSE streaming contract and provider endpoints
- **REF-003**: `docs/product-brief.md` PRIN-001 — the grounding rule enforced here
- **REF-004**: `docs/design/overview.md` — Settings and AI panel provider controls

---
title: "ADR-0024: Quillbert prompt profiles, stamped by hash, traced on the message"
status: "Accepted"
date: "2026-10-20"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "assistant", "prompts", "observability"]
supersedes: ""
superseded_by: ""
---

# ADR-0024: Quillbert prompt profiles, stamped by hash, traced on the message

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[assistant-prompts.md](../assistant-prompts.md) planned how a Research prompt is built and
versioned. It said it would become binding only as an ADR. The chat is now being built
against a real model, so that plan is binding from here on, with three changes.

- **CON-001**: The assistant has a name. The GM meets **Quillbert**: the panel is titled
  Quillbert and it introduces itself. The plan's "no persona" stance was about keeping
  evidence rules out of personality, not about the name.
- **CON-002**: One composer now serves research, creative and chat replies
  ([ADR-0025](adr-0025-jev-routes-intent.md)). Each needs its own rule about invention.
- **CON-003**: The GM's greeting ("hi Quillbert", "what can you do?") must not be met with
  "Not in your material."
- **CON-004**: A bad answer must be findable later, together with its prompt version, its
  model, latency and cost, without copying campaign text into a second store.

## Decision

**Three prompt profiles live in `backend/app/adapters/llm/prompts/`, one module each. Each
profile has its system text, temperature, and a version stamp: the first 12 hex characters
of SHA-256 over that text. The Gateway is the only place a profile becomes provider
messages.**

| Profile | Temperature | Sources | Rule about invention |
|---------|-------------|---------|----------------------|
| `research` | 0 | Retrieved chunks, in the last user message | Never. Cite `[Sn]`, or say exactly "Not in your material." |
| `creative` | 0.9 | Retrieved chunks, as context to stay consistent with | The point. A draft for the GM, never presented as fact, no `[Sn]` |
| `chat` | 0.3 | None | States no rules or campaign facts. Introduces Quillbert and points to asking a question |

- Each system text opens with one role sentence naming Quillbert. The sentence sets the
  tone and carries no evidence rule. The evidence rules are the bullets that follow it.
- Assembly order: system text (stable, with no campaign data, clock or chunks), then prior
  turns oldest first, then the last user message, which holds the Question, then Sources,
  then Focus.
- No client field accepts prompt text. Quick-prompt chips are user text.
- Trace columns on the **assistant** message, written only by the Gateway path:
  `prompt_id`, `prompt_version`, `model`, `ttft_ms`, `duration_ms`, `prompt_tokens`,
  `completion_tokens`, `cost_usd`. `model` and usage are null when no provider was called
  (the deterministic refusal).
- The system text and chip copy are not stored per message. Git at that hash is the
  record.

## Consequences

### Positive

- **POS-001**: `GROUP BY prompt_version, model` is the evaluation and cost dashboard, with
  no new service.
- **POS-002**: The stable system prefix means prompt caching can be enabled later without
  reordering anything.
- **POS-003**: Greetings get a short, friendly reply that states no facts, and they do not
  spend retrieval.

### Negative

- **NEG-001**: Three prompts to test instead of one (ADR-0012 NEG-002, now real).
- **NEG-002**: A name invites the model to "be a character". The role sentence must stay
  one sentence. A test asserts that the Research text still contains its evidence rules.
- **NEG-003**: The hash identifies text, not a rollout. Serving two wordings at once would
  need a registry, which this ADR does not adopt.

## Alternatives Considered

### Hosted prompt registry (Langfuse, LangSmith)

- **ALT-001**: **Description**: Keep the prompts in a hosted hub with movable tags.
- **ALT-002**: **Rejection Reason**: A second home for the grounding text, the same thing
  ADR-0019 ALT-006 rejected. A hub also copies campaign text into a trace store. One
  engineer edits the prompts, so git is enough.

### No persona

- **ALT-003**: **Description**: Keep the plan's nameless assistant.
- **ALT-004**: **Rejection Reason**: CON-001. The name is product, and one sentence costs
  nothing against the rules.

## Implementation Notes

- **IMP-001**: `prompts/research.py` holds `REFUSAL = "Not in your material."`. The use
  case writes this exact string when no chunk clears the relevance floor, and does not call
  the provider in that case.
- **IMP-002**: Each module exposes `SYSTEM`, `TEMPERATURE`, `VERSION` and
  `compose(history, sources)`. `VERSION` is computed at import time.
- **IMP-003**: Tests:
  - The research text contains `ONLY the Sources block` and the refusal string.
  - Chunk text never appears in a system message.
  - A changed text changes `VERSION`.
  - A user message stores no trace columns.
  - The creative and chat profiles never produce citations.
- **IMP-004**: The prompt texts and the Sources format are specified in
  [assistant-prompts.md](../assistant-prompts.md). That file is now the reference for this
  ADR, not a proposal.

## References

- **REF-001**: [ADR-0012](adr-0012-two-ai-modes.md) IMP-001 — modes are profiles
- **REF-002**: [ADR-0019](adr-0019-openrouter-privacy-routing.md) — the Gateway is the only
  provider path
- **REF-003**: [ADR-0025](adr-0025-jev-routes-intent.md) — how a message gets its profile
- **REF-004**: [assistant-prompts.md](../assistant-prompts.md) — texts, formatter, tests

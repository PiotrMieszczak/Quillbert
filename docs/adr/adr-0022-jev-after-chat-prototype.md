---
title: "ADR-0022: Jev judges Research answers after the chat prototype; the GM keeps the mode"
status: "Accepted"
date: "2026-10-19"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "assistant", "jev", "privacy"]
supersedes: ""
superseded_by: ""
---

# ADR-0022: Jev judges Research answers after the chat prototype; the GM keeps the mode

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

The assistant the GM talks to is a chat model behind the Gateway, streamed as AG-UI
([ADR-0009](adr-0009-ag-ui-protocol.md), [ADR-0019](adr-0019-openrouter-privacy-routing.md)).
Jev (`typesafe/jev-1.14`) is a different kind of model on the same router: it returns a
typed Choice, Noul, Score, or Box with a probability, and it does not write prose.

- **CON-001**: Research answers are trusted because they come from indexed material and
  say so when the material does not cover the question (PRIN-001). A second opinion on
  whether a finished sentence follows from its cited chunk would make a miss visible.
- **CON-002**: Research, Creative, and in-character are separate surfaces so an invention
  cannot be mistaken for a retrieved fact (PRIN-006,
  [ADR-0012](adr-0012-two-ai-modes.md) ALT-002). The GM chooses the surface.
- **CON-003**: A live session targets interactions under 300ms (PRIN-003). Jev's published
  median latency is about 0.17s, which is most of that budget before a chat model starts.
- **CON-004**: Campaign text may go only to a zero-retention, no-training provider
  ([ADR-0019](adr-0019-openrouter-privacy-routing.md) CON-002). OpenRouter lists TypeSafe
  as zero retention and no-training. TypeSafe's own help center says retention depends on
  an agreed ZDR arrangement, and its enterprise page sells zero data retention as an
  add-on.
- **CON-005**: Upload-to-indexed and a streamed chat reply do not exist as a working
  prototype yet. `run_turn` streams text and does not retrieve or cite. A judge of
  citations has nothing to judge.
- **CON-006**: Jev is called on OpenRouter's Decisions API (`POST /api/alpha/decisions`),
  not the chat-completions API. The model page dates the current release to 14 Oct 2026.
  It is not available through EU in-region routing.

## Decision

**Jev is adopted as a judge beside the chat model, and it is built only after a GM can
upload a document, see it reach Indexed, and receive a streamed chat reply.** The chat
model keeps writing the answer. The GM keeps the mode.

Two judgments, both non-blocking for the first token:

1. **Support check, Research only.** After the reply is on screen, a Noul asks whether a
   sentence follows from the chunk it cites. The UI marks a high-confidence no. It does
   not delete or rewrite the sentence.
2. **Mode hint, Research only.** When the question asks the model to invent, the UI may
   offer a link to Creative. The in-flight reply and the stored message stay Research.
   In-character is never offered by Jev; it is entered from a character, as ADR-0012
   decided.

Jev is reached by a second method on the existing OpenRouter adapter inside the Gateway
(BND-002). The request fails closed unless that endpoint is on the zero-retention
allowlist. No campaign text is sent until OpenRouter's zero-retention listing and
TypeSafe's own retention terms describe that same endpoint (CON-004).

## Consequences

### Positive

- **POS-001**: A Research claim that the cited chunk does not support can be marked
  without another generative pass.
- **POS-002**: A GM who asks for an adventure from the Research panel gets a way to the
  Creative page without the panel changing mode underneath them.
- **POS-003**: The upload-and-chat prototype stays one chat model and one stream. Jev
  does not enter that loop.

### Negative

- **NEG-001**: A wrong Noul marks a fair sentence, or misses a bad one. Calibration is
  across many predictions; one answer can still be wrong. The mark is the product, so a
  noisy threshold trains the GM to ignore it.
- **NEG-002**: A wrong hint nags. The GM asked a grounded question and the panel suggests
  they meant to invent.
- **NEG-003**: The Decisions API is alpha, and the model is days old. Request shape and
  probabilities can move between releases.
- **NEG-004**: Confirming CON-004 can fail. If TypeSafe's OpenRouter endpoint retains
  prompts, Jev is not called, and POS-001 and POS-002 do not ship.
- **NEG-005**: Each check sends cited chunks, or the question, to TypeSafe. That is
  another copy of campaign text, allowed only while CON-004 holds.

## Alternatives Considered

### Jev chooses the mode

- **ALT-001**: **Description**: One composer. Jev classifies the question as Research,
  Creative, or in-character, and the assistant answers in that mode.
- **ALT-002**: **Rejection Reason**: This is ADR-0012 ALT-001, which ALT-002 rejected.
  The GM would have to notice which rule governed the last reply, mid-session. PRIN-006
  exists so that inference is not required. A friendlier composer is the failure the mode
  split was built to prevent. In-character has a further problem: the speaker is a
  specific NPC, which a classifier cannot know from the question alone.

### Jev Router chooses the chat model

- **ALT-003**: **Description**: `typesafe/jev-router` picks the writing model and the
  reasoning effort per request, balancing task difficulty against cost.
- **ALT-004**: **Rejection Reason**: Research keeps one model at temperature 0 so the same
  question against the same sources answers the same way (ADR-0012 IMP-001a). The router's
  `models` list is a preference with fallback: an empty pool is retried without the list.
  Provider filters still apply; the include list does not hold the allowlist. The model
  that saw the text is known only after the response.

### Build Jev into the first chat loop

- **ALT-005**: **Description**: Add the Decisions client while the upload and chat
  prototype is still being built.
- **ALT-006**: **Rejection Reason**: CON-005. The support check needs citations the
  prototype does not produce yet, and a pre-flight call spends CON-003's budget before
  the first token.

## Implementation Notes

- **IMP-001**: Trigger — a document uploads, reaches Indexed, and a chat turn streams a
  reply with citations. Until that is true, there is no Decisions client and no Jev UI.
- **IMP-002**: The client lives in the OpenRouter adapter. Nothing outside `adapters/llm/`
  imports it (BND-002). The call is refused when the endpoint is off the allowlist
  (ADR-0019 IMP-003).
- **IMP-003**: The support check runs after `TextMessageEnd`. The mode hint may run in
  parallel with the stream. Neither call is on the path to the first token.
- **IMP-004**: A stored assistant message records the mode the GM had open. A test asserts
  that mode is not a value returned by Jev.
- **IMP-005**: The support check flags only a high no-probability. The threshold is
  configuration, chosen against a labeled sample of supported and unsupported sentences,
  and revisited when the Jev release changes (NEG-001, NEG-003).
- **IMP-006**: Jev is not called from ingestion (ADR-0002, BND-001), does not approve
  `propose_*` writes (ADR-0011, BND-007), and is not Jev Router (ALT-004).

## References

- **REF-001**: [ADR-0012](adr-0012-two-ai-modes.md) — modes stay GM-chosen; ALT-002 is the
  rejection of a model that switches tone
- **REF-002**: [ADR-0019](adr-0019-openrouter-privacy-routing.md) — the allowlist this call
  must pass
- **REF-003**: [ADR-0009](adr-0009-ag-ui-protocol.md) — the chat stream Jev does not replace
- **REF-004**: OpenRouter, [Jev](https://openrouter.ai/docs/guides/community/jev) and
  [Jev Router](https://openrouter.ai/docs/guides/routing/routers/jev-router), read
  2026-10-19
- **REF-005**: TypeSafe, [System One](https://docs.typesafe.ai/concepts/system-one) and
  [how submitted data is retained](https://help.typesafe.ai/articles/5974925716-how-is-submitted-data-used-or-retained)

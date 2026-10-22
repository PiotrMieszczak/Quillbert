---
title: "ADR-0025: One composer; Jev routes each message, and every reply shows its mode"
status: "Superseded"
date: "2026-10-20"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "assistant", "jev", "ux", "privacy"]
supersedes: "ADR-0022"
superseded_by: "ADR-0026"
---

# ADR-0025: One composer; Jev routes each message, and every reply shows its mode

## Status

Proposed | Accepted | Rejected | **Superseded** | Deprecated

## Context

[ADR-0012](adr-0012-two-ai-modes.md) made Research, Creative and in-character separate
surfaces and rejected one assistant that switches on request (ALT-001/002).
[ADR-0022](adr-0022-jev-after-chat-prototype.md) adopted Jev only as a judge and rejected
letting it choose the mode (ALT-001/002). Both rejections rest on one failure: an invention
read as a fact mid-session (PRIN-006).

The product owner has overruled the surface split on UX grounds. A GM should not have to
decide which mode to open before asking. This ADR keeps the failure in view and moves the
guard from *where you ask* to *how each reply is labelled*.

- **CON-001**: The GM asks in one place. Choosing a mode first is friction the product
  owner rejects.
- **CON-002**: PRIN-006 still holds. The GM must be able to tell, on screen and later,
  whether a reply came from their material or was invented.
- **CON-003**: Jev (`typesafe/jev-1.14`, OpenRouter Decisions API
  `POST /api/alpha/decisions`) returns a typed Choice with per-option probabilities and a
  confidence. It costs $0.042 per million input tokens, and output is free (TypeSafe
  models page, read 2026-10-20).
- **CON-004**: Campaign text may go only to a zero-retention, no-training provider
  ([ADR-0019](adr-0019-openrouter-privacy-routing.md) CON-002). TypeSafe states that Jev is
  not trained on customer requests. Zero retention is described as an enterprise term. That
  it applies to the OpenRouter endpoint is not confirmed (carried from ADR-0022 CON-004).
  The product owner accepts that risk at this stage, before there are real users' private
  campaigns (decided 2026-10-21).
- **CON-005**: The first token should not wait on a classifier (PRIN-003). Retrieval and
  query embedding already take time before the model is called.
- **CON-006**: In-character needs a speaker, and a classifier cannot know which NPC from
  the question alone (ADR-0022 ALT-002, still true).

## Decision

**The assistant panel has one composer. Each user message is routed to `research`,
`creative` or `chat` by a Jev Choice, unless the GM chose the mode explicitly. Every
assistant reply carries its mode as a visible badge, and offers a one-click re-ask in the
other mode. When in doubt, the route is `research`, which never invents.**

1. **Routing.** The question and the last two turns (never chunks) go to Jev as one Choice
   question with three options. The call runs in parallel with query embedding and
   retrieval, with a 300 ms budget.
2. **Fallback to research.** The route falls back to `research` in each of these cases:
   - Jev's confidence is below `jev_route_min_confidence`.
   - Jev errors or times out.
   - Jev is disabled (`jev_enabled = false`, the kill switch).

   The turn never fails because of routing.
3. **GM override.** A send body may carry `mode`. That is the GM's explicit choice, through
   the flip on a reply. Jev is not called.
4. **Provenance.** `message.mode` is the authoritative mode of each assistant message.
   `route_source` (`jev` | `gm` | `default`) and `route_confidence` are stored beside it.
   `conversation.mode` is no longer read.
5. **Visible mode.** Research replies show "From your material" with their citations.
   Creative replies show "Invented". Chat replies carry no badge and state no facts
   ([ADR-0024](adr-0024-quillbert-prompt-profiles.md)).
6. **Support check (kept from ADR-0022).** After `TextMessageEnd` on a research reply, one
   Decisions request carries one Noul per cited sentence (the sentence and its cited chunk).
   A sentence above the flag threshold is marked in the UI and is never deleted or
   rewritten.
7. **Privacy exception.** Jev is **on by default in every environment** (`jev_enabled =
   true`). This is a deliberate, scoped exception to ADR-0019 CON-002 and IMP-003, and it
   applies to the TypeSafe Decisions endpoint only. That endpoint receives two things: for
   routing, the question and the last two turns; for the support check, the cited sentence
   and its chunk excerpt. Every chat-completion route stays on the zero-retention
   allowlist. `jev_enabled = false` is the kill switch: routing becomes `default` and the GM
   uses the flip.
8. **What is unchanged.** In-character is still entered from a character (CON-006). Creative
   output is still never indexed (BND-008, ADR-0012 IMP-006).

This supersedes ADR-0022 and replaces ADR-0012's surface rule for research and creative
(ALT-002's rejection, the "Where" row, and IMP-005's header naming). ADR-0012's profiles,
temperatures and indexing rule stand.

## Consequences

### Positive

- **POS-001**: The GM asks and gets an answer. The question "which mode was I in?" no
  longer comes before the question.
- **POS-002**: Provenance is per reply rather than per page, so it survives scrolling back
  and reopening a conversation.
- **POS-003**: Routing costs about two hundredths of a thousandth of a dollar per turn, and
  hides inside retrieval latency.
- **POS-004**: A misroute costs one click, and it is recorded (`route_source = gm` after a
  Jev route), which makes it the labelled sample for tuning the threshold.

### Negative

- **NEG-001**: PRIN-006 now rests on a badge. A badge is weaker than a separate page (this
  is ADR-0012 NEG-003 come true). The badge must be unmissable, and the design must give
  "Invented" a treatment that is not just a colour.
- **NEG-002**: Jev can route an honest question to creative. The research default on low
  confidence limits this, but at high confidence Jev can still be wrong.
- **NEG-003**: The Decisions API is alpha and the model is days old (ADR-0022 NEG-003).
- **NEG-004**: Each routed turn sends the question to TypeSafe, and each support check
  sends an excerpt of an uploaded document. Neither is confirmed to be zero-retention
  (CON-004), and that may include passages from purchased rulebooks. The product owner
  accepted this risk. **Revisit trigger:** before real users' private campaign material
  reaches production, either confirm TypeSafe's zero retention for this endpoint or set
  `jev_enabled = false`.
- **NEG-005**: Long creative drafts land in a 400px panel (ADR-0012 CON-004). The Creative
  page, with proposals, remains the place for large drafts when it exists.

## Alternatives Considered

### GM-chosen modes (ADR-0012 / ADR-0022 as written)

- **ALT-001**: **Description**: Research in the panel, Creative on its own page, Jev only as
  a judge.
- **ALT-002**: **Rejection Reason**: CON-001. The product owner rejected the up-front choice
  as bad UX.

### Jev routes silently

- **ALT-003**: **Description**: One composer with routing and no badge or flip.
- **ALT-004**: **Rejection Reason**: Fails CON-002. That is exactly ADR-0012 ALT-002.

### Jev Router picks the chat model

- **ALT-005**: **Description**: `typesafe/jev-router` chooses the model and reasoning effort.
- **ALT-006**: **Rejection Reason**: The router's `models` list is a preference with
  fallback, not an allowlist. The serving model is known only after the call. Research loses
  its fixed temperature-0 model (ADR-0022 ALT-004, still true).

## Implementation Notes

- **IMP-001**: `Router` is a port with two implementations. `JevRouter` lives in
  `adapters/llm/` and calls `OpenRouterChat.decide`. `DefaultRouter` always returns
  `research`. Nothing outside `adapters/llm/` imports the Decisions client (BND-002).
- **IMP-002**: The Choice question uses `instructions` "Which kind of reply does the game
  master want?" and these `criteria`:
  - `research`: a question about rules, lore or what happened in the campaign.
  - `creative`: a request to invent, draft, describe or improvise new content.
  - `chat`: a greeting, thanks, or a question about Quillbert itself.
- **IMP-003**: Tests:
  - Low confidence goes to research.
  - A Jev exception goes to research and the turn still succeeds.
  - A GM override makes zero router calls.
  - The stored `route_source` matches each path.
  - Creative writes no citations.
  - Chat calls no search.
- **IMP-004**: `jev_route_min_confidence` (start at 0.7) and `jev_support_flag_threshold`
  are configuration. They are tuned on a labelled sample of about 30 questions and about
  30 cited sentences, and revisited when the Jev release changes.
- **IMP-005**: Jev is not called from ingestion (BND-001). It does not approve `propose_*`
  writes (BND-007) and is not Jev Router.
- **IMP-006**: A `dm.route` Custom event carries `{mode, source, confidence}` so the badge
  renders before the first text delta.

## References

- **REF-001**: [ADR-0012](adr-0012-two-ai-modes.md) — modes as profiles. Its surface rule is
  replaced here
- **REF-002**: [ADR-0022](adr-0022-jev-after-chat-prototype.md) — superseded. The support
  check and privacy gate are carried over
- **REF-003**: [ADR-0024](adr-0024-quillbert-prompt-profiles.md) — the three profiles a
  route selects
- **REF-004**: OpenRouter, [Jev](https://openrouter.ai/docs/guides/community/jev) and
  [Jev Router](https://openrouter.ai/docs/guides/routing/routers/jev-router); TypeSafe
  [Choice](https://docs.typesafe.ai/primitives/choice),
  [Noul](https://docs.typesafe.ai/primitives/noul),
  [Models](https://docs.typesafe.ai/models). All read 2026-10-20

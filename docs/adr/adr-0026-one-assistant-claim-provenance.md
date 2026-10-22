---
title: "ADR-0026: One assistant; provenance per claim; memory is what the GM saves"
status: "Accepted"
date: "2026-10-21"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "assistant", "memory", "ux", "privacy", "i18n"]
supersedes: "ADR-0025"
superseded_by: ""
---

# ADR-0026: One assistant; provenance per claim; memory is what the GM saves

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[ADR-0025](adr-0025-jev-routes-intent.md) kept one composer and still gave each reply one
mode, chosen by a Jev classifier. The product owner rejects modes as a concept, not just
the choice of where to ask.

- **CON-001**: The work a GM brings mixes the two. "Find the plot holes in act 2 and
  propose fixes" needs cited facts *and* invented fixes in one reply. A per-reply mode can
  only be one of them.
- **CON-002**: An idea the GM agrees to must persist. Today it dies with the conversation.
- **CON-003**: The assistant should know how this GM writes adventures. That knowledge
  spans every campaign they run.
- **CON-004**: PRIN-006 still holds. An invention must never read as a fact, and an
  unaccepted invention must never become retrievable (AC-017).
- **CON-005**: ADR-0025 needed a privacy exception for Jev (its item 7, NEG-004). The
  TypeSafe endpoint is not confirmed zero-retention.
- **CON-006**: The GM preps in more than one language. Polish and German questions over
  English rulebooks are normal.
- **CON-007**: A smoke test on 2026-10-21 tried 11 models on zero-retention endpoints
  against a synthetic adventure with planted plot holes, in English, Polish and German.
  Results are in [assistant-prompts.md](../assistant-prompts.md#model-choice). Every
  model replied in the question's language. The failure that separated them was a
  **cited invention**: a `[Sn]` attached to prose the model made up.

## Decision

**One prompt profile, `quillbert`, with no modes and no router. Provenance is shown per
paragraph, computed from citations. Memory is only what the GM explicitly saves: campaign
notes become ordinary Markdown documents, and writing preferences become a per-user style
guide.**

1. **One profile.** Every turn retrieves, as before, and the model gets one rule set:
   - A statement about the campaign, its rules or its history cites `[Sn]`.
   - Text with no citation is the assistant's own idea, and is phrased as one.
   - A citation goes only on what the source states. Never on the assistant's own
     description, read-aloud or suggestion.
   - When the material does not answer a factual question, the reply says so plainly
     before offering any idea.
2. **Provenance per paragraph.** The UI marks every paragraph with no valid citation as
   "Idea — not from your material". The treatment is an icon plus a label, not a colour
   alone. This is computed from the citations the turn already parses. No classifier is
   involved and it does not depend on the reply's language.
3. **Campaign memory is a saved note.** The model may call `propose_memory` with
   `target: "campaign"`, a title and a body. The call returns a draft card and writes
   nothing (ADR-0011, BND-007). When the GM clicks Save, the frontend uploads the edited
   text as `notes/<slug>.md` through the ordinary document upload. Deterministic
   ingestion indexes it, and it is retrieved and cited like any other source.
4. **Style memory is a per-user guide.** There is one text per user: "How I write
   adventures", a `style_guide` field on the user profile. The GM edits it in Settings,
   and `propose_memory` with `target: "style"` drafts an addition the GM saves through
   `PATCH /settings`. It is placed right after the system
   text, so the prefix stays stable and cacheable.
5. **Conversations are not memory.** Raw conversations are never indexed. Only saved
   notes persist beyond the conversation's own history window.
6. **Language.** The reply, and any note, is in the language of the GM's latest message.
   Proper names stay as the source spells them.
7. **No Jev.** Routing and the support check are removed, and so is ADR-0025's privacy
   exception. Every model call is on the zero-retention allowlist again (ADR-0019).

This supersedes ADR-0025. It replaces the research/creative/chat split of
[ADR-0012](adr-0012-two-ai-modes.md) and [ADR-0024](adr-0024-quillbert-prompt-profiles.md).
ADR-0012's in-character mode stands, and so do ADR-0024's hash versioning and trace
columns, now with one `prompt_id`.

## Consequences

### Positive

- **POS-001**: The GM asks and gets one answer that is both grounded and useful. There is
  no mode to choose, and no re-ask in the other mode.
- **POS-002**: Agreed decisions persist as documents the GM can read, edit and delete in
  the library. They are also cited in later answers, because they are sources.
- **POS-003**: Memory needs no new storage path, store or ingestion code. A note is a
  Markdown upload, and the extractor already reads Markdown.
- **POS-004**: Privacy returns to a single rule: zero-retention only. The Jev exception
  and its revisit trigger disappear.
- **POS-005**: Provenance survives translation. Citations mark facts whatever language
  the reply is in.

### Negative

- **NEG-001**: The guard moves from code to the prompt. ADR-0024 IMP-001's deterministic
  "Not in your material." refusal goes, because a question with no hits may still want
  ideas. Refusal accuracy is now measured by the eval (IMP-006), not guaranteed.
- **NEG-002**: A model can cite a wrong source and produce a cited invention, which the UI
  shows as a fact. This was the leading failure in the smoke test (CON-007). The prompt
  forbids it, the eval measures it, and the GM can open every citation.
- **NEG-003**: Per-paragraph marking is coarse. A paragraph with one cited sentence and
  one invented sentence reads as cited. The prompt asks for ideas in their own
  paragraphs, but nothing enforces it.
- **NEG-004**: Cross-language retrieval rests on vectors alone. Keyword search runs in
  each document's own language, so a Polish question cannot match an English chunk by
  keyword.
- **NEG-005**: A saved note is GM-authored text that the model drafted. If the GM saves a
  draft without reading it, an invention becomes canon. Save is the GM's act, and the
  card shows the full text before it.

## Alternatives Considered

### Keep ADR-0025: one composer, routed modes

- **ALT-001**: **Description**: Jev picks research, creative or chat for each message.
- **ALT-002**: **Rejection Reason**: CON-001. A mixed request has no right single mode.
  It also keeps the privacy exception (CON-005).

### Index conversations as memory

- **ALT-003**: **Description**: Chunk and embed past conversations so the assistant
  recalls them.
- **ALT-004**: **Rejection Reason**: It makes unaccepted inventions retrievable, which
  fails AC-017 and CON-004. Saved notes give recall with the GM's consent.

### A dedicated memory table

- **ALT-005**: **Description**: A `memory` entity with its own CRUD, retrieval and
  injection.
- **ALT-006**: **Rejection Reason**: It repeats documents, chunking, search and citation
  for the same job. A note in the library is visible and editable with the tools that
  already exist.

### Hosted memory services (provider memory tools, mem0-style stores)

- **ALT-007**: **Description**: Let a provider or a memory service decide what to
  remember.
- **ALT-008**: **Rejection Reason**: The model decides what becomes canon, without a
  review (ADR-0011 ALT-001). It is also a second store of campaign text outside the
  allowlist (ADR-0019).

## Implementation Notes

- **IMP-001**: `prompts/quillbert.py` replaces `prompts/research.py`. It keeps the
  `SYSTEM` / `VERSION` / `compose` shape (ADR-0024 IMP-002). The text is in
  [assistant-prompts.md](../assistant-prompts.md).
- **IMP-002**: `propose_memory` is the first tool. The loop is bounded at 5 iterations
  (ADR-0011 IMP-002). The tool returns its arguments as the draft. It is never reachable
  from ingestion (ADR-0011 IMP-007).
- **IMP-003**: Paragraph marking runs on the frontend over the stored reply and its
  citations. A paragraph is cited if it contains a label that survived `_citations`.
- **IMP-004**: OpenRouter request settings:
  - Keep ADR-0019's pin: `only`, `zdr`, `data_collection: deny`, no fallbacks.
  - Add `require_parameters: true`, so a dropped parameter becomes an error rather than
    a silent strip. Gemini 3.x rejects `temperature`, so research's temperature 0 was
    being dropped.
  - Send `temperature` only when it is configured.
  - Set `session_id` to the conversation id for sticky, cache-warm routing.
  - Size `chat_max_tokens` for reasoning tokens.
- **IMP-005**: The model and endpoint stay configuration (ADR-0019, AC-004). The default
  is `openai/gpt-6-luna` on `azure/eu`, chosen by the product owner on cost and speed.
  The fallback is `z-ai/glm-5.3` on `novita/fp8`. Both join `ZDR_PROVIDERS`. Both must
  also be inside the OpenRouter account's allowed providers, which act as a ceiling.
- **IMP-006**: Before the default ships, the eval in
  [assistant-prompts.md](../assistant-prompts.md#model-choice) runs:
  - About 30 questions on real material, in English, Polish and German.
  - Polish questions over English documents.
  - 3 runs each.

  A cited-invention rate above the fallback's blocks the default.
- **IMP-007**: Tests:
  - `propose_memory` writes nothing.
  - A saved note is found by search and cited.
  - The style guide is in the system prefix, never in the user message.
  - Every request carries `zdr` and `require_parameters`.
  - A non-allowlisted endpoint is still refused.

## References

- **REF-001**: [ADR-0025](adr-0025-jev-routes-intent.md) — superseded by this record
- **REF-002**: [ADR-0011](adr-0011-assistant-tools.md) — proposals: the model drafts, the
  GM commits
- **REF-003**: [ADR-0012](adr-0012-two-ai-modes.md),
  [ADR-0024](adr-0024-quillbert-prompt-profiles.md) — the split this replaces. In-character
  and trace columns stand
- **REF-004**: [ADR-0019](adr-0019-openrouter-privacy-routing.md) — the zero-retention
  allowlist
- **REF-005**: OpenRouter
  [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection),
  [prompt caching](https://openrouter.ai/docs/guides/best-practices/prompt-caching), and
  `/api/v1/endpoints/zdr`. All read 2026-10-21

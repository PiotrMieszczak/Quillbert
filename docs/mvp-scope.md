# MVP Scope

The design defines the **target product**. This document defines what **v1 ships**.

Every screen in the design is built — the design is the source of truth for the
interface. The distinction is how much *behaviour* sits behind each screen in v1.

## Scope tiers

| Tier | Meaning |
|------|---------|
| **Full** | Built to the design, backed by real persistence and real logic |
| **Local** | Built to the design, persisted locally, no AI or derived behaviour |
| **Read-only** | Built to the design, renders real data, editing deferred |
| **Deferred** | Not in v1; route exists and states it is coming |

## In scope

### Authentication — Full

Through **Supabase Auth** (GoTrue), the auth bundled with the Supabase stack the deployment
already runs ([ADR-0020](adr/adr-0020-supabase-auth.md)) — the project is tool-first, so
auth is configured, not hand-built.

- Signup, login, logout — Supabase Auth (password hashing is GoTrue's)
- Sessions as Supabase-issued JWTs; the FastAPI backend validates them, mints none
- Google OAuth via Supabase
- Password reset via Supabase
- Every route scoped to the authenticated owner (`BND-003`)

### Shell and navigation — Full

- Login screen with **real authentication** ([ADR-0020](adr/adr-0020-supabase-auth.md)):
  email and password, Google OAuth, and password reset, via Supabase Auth
- Campaign picker with add-campaign modal (image + mandatory system)
- App shell: 72px header, floating nav rail (60px ↔ 236px), AI panel column
- Mobile shell ≤900px: bottom tab bar, More sheet, AI slide-over
- Settings: account fields and AI provider selection

### Documents — Full

The differentiating capability. Upload → extract → index → retrieve.

- Upload PDF, Markdown, plain text, and DOCX (not legacy .doc)
- Deterministic extraction (PyMuPDF), chunking on paragraph and heading
  boundaries, PostgreSQL full-text **and** vector indexing (ADR-0021)
- Deduplication by `sha256` — the same file uploaded twice is not processed twice
- Scanned pages read with Tesseract OCR (English and Polish); pages too unreliable to cite
  are left out of the index and counted. Without Tesseract installed, a scan waits in
  `awaiting OCR`, not `failed`
- Background processing with live status: `Queued` → `Processing` (%) → `Indexed` / `Failed`
- Document list exactly as designed, including per-item progress
- Hybrid search across a campaign's indexed material — keyword and vector, fused (RRF)

### Assistant — Full

One assistant, no modes ([ADR-0026](adr/adr-0026-one-assistant-claim-provenance.md)).
The safety property moves from the reply to the claim: **every fact cites its source, and
every uncited paragraph is marked as an idea**. A GM must never have to infer whether
something was retrieved or invented.

| Surface | Where | Invention |
|---------|-------|-----------|
| **Quillbert** | Side panel | Facts cite `[Sn]`; ideas (plot fixes, hooks, read-aloud) are uncited and marked "Idea — not from your material" |
| **In character** | Panel, opened from a character | Within one voice; never canon unless saved |

**Memory** is what the GM saves: a `propose_memory` draft becomes a Markdown note in the
library (indexed and cited like any upload), or an addition to the GM's per-user style
guide. Conversations themselves are never indexed. Replies and notes follow the language
of the GM's question.

Built-in rules: the D&D SRD 5.1 (2014) and SRD 5.2 (2024) in the shared vault,
`wizard-vault`: upstream Arkon, consumed over MCP
([ADR-0029](adr/adr-0029-wizard-vault-over-mcp.md)). Until the licensor answers
([#124](https://github.com/PiotrMieszczak/Quillbert/issues/124)) only the maintainer uses it. Traveller rules come from the GM's
own upload.


- Chat panel streaming [AG-UI](https://docs.ag-ui.com/) events over SSE ([ADR-0009](adr/adr-0009-ag-ui-protocol.md))
- **Plot analysis and drafting** in the same panel: plot holes, fixes, hooks, read-aloud
- **Saved notes and a per-user style guide** as the assistant's memory
- **In-character chat** entered from a character page, with their portrait in the header
- Retrieval grounded in the active campaign's indexed chunks, with citations
- LLM Gateway abstracting provider; OpenRouter is the single provider, restricted to a
  zero-retention allowlist; the active model is admin/env config, not a user-facing
  selector ([ADR-0019](adr/adr-0019-openrouter-privacy-routing.md))
- Tool-call indicator chips (the design's green check rows) for every tool that runs
- **Three request shapes** ([ADR-0011](adr/adr-0011-assistant-tools.md)):
  retrieve-and-answer ("what are opportunity attacks?"), fetch-and-transform
  ("summarise last session"), and extract-and-propose ("create an NPC from this module")
- **Proposals, never silent writes.** An extracted entity arrives as a pre-filled form
  citing the chunks each field came from. Nothing is saved until the GM confirms
- A typing indicator. No attach affordance in the composer: files enter through the
  Documents page. Quick-prompt chips are deferred until they can be answered

### NPCs, Players, Factions — Full

The design models these as one `Character` entity split by an `isPlayer` flag, plus a
separate `Faction` entity. All support create, read, update, delete, plus portrait upload.

- NPC list with relationship filters (all / ally / enemy / family / professional / neutral)
- Player list and Add Player form
- Faction list and detail, with members and inter-faction relationships
- Character detail: stats, connections, quote, GM notes, disposition

### Regions and Adventures — Full

The entities a GM needs to *build* a campaign, not only run one.

- **Regions** nested at any scale — realm, settlement, district, site, building. Notable
  places surface on their parent's page so a GM reaches them in one click mid-session
- **Adventures** with premise, GM-private background, hooks tagged by motivation, and
  ordered scenes carrying read-aloud text and private notes
- Scenes tagged by purpose (hook / complication / setback / climax / payoff) so the shape
  of an adventure is readable at a glance
- Quests can belong to an adventure or stand alone

### Quests — Full

- Five-status quest log (available, in progress, completed, failed, inactive)
- Progress counters (`cur` / `max`) with progress bars
- Parent/subquest relationships
- Create, edit, status transitions, reactivate

### Sessions — Full

- Session log list
- Rich-text composer for session entries
- Entries are indexed alongside documents and become retrievable material

### Knowledge Graph — Read-only

Rendered from real relationship data, not mock data.

- Force-directed layout of characters and factions
- Relationship-coloured edges with legend
- Search highlights matches and dims the rest
- Hover info card; click navigates to entity detail
- **Deferred:** editing relationships from the graph; graph-backed AI queries

## Out of scope for v1

| Item | Why | Revisit when |
|------|-----|--------------|
| **Neo4j / graph database** | The domain is graph-shaped, but the *queries* are not — every one the design asks for is zero or one hop. A graph DB earns its cost on deep traversal, which nothing here does. The argument survives the move to PostgreSQL unchanged. See [ADR-0003 ALT-011](adr/adr-0003-sqlite-single-store.md). | Graph queries exceed 2 hops, or edge counts make the graph endpoint slow |
| **Cross-encoder reranking** | Hybrid retrieval ships in v1 ([ADR-0021](adr/adr-0021-gemini-embeddings-via-openrouter.md)). Reranking is likely the next quality jump, but it puts a second model in the live query path (PRIN-003) and its gain over RRF is unmeasured here. | It beats plain RRF on the evaluation set (ADR-0021 IMP-004) |
| **Dedicated vector database** | `pgvector` sits in the same row and transaction as the chunk text. A separate store reintroduces the multi-store consistency burden for corpus sizes where it is not the bottleneck. | Measured recall or latency problems, not scale anxiety |
| **Multi-agent orchestration** | One assistant with retrieval tools is simpler and easier to evaluate than five agents behind an intent router. | A single agent measurably underperforms on distinct task types |
| **Agent framework (LangChain, Pydantic AI)** | Three or four tools in one bounded loop is not framework territory, and a framework would own prompt assembly — moving the grounding rule out of the Gateway. See [ADR-0011](adr/adr-0011-assistant-tools.md). | Real branching or sub-agents. Reassess Pydantic AI first |
| **Automatic entity extraction on upload** | This is what [ADR-0002](adr/adr-0002-deterministic-extraction.md) forbids: a model in the ingestion path writing unreviewed. A hundred silently created NPCs of uncertain quality is worse than none. | Extraction accuracy is measurable against a fixture corpus |
| **AG-UI beyond streaming** | Sub-agent composition, agent steering, generative UI, and shared-state sync are unused. The protocol is adopted for streaming only. | A second agent, or the UI needs to steer a running one |
| **Local self-hosting** | v1 is hosted-first; proving the product does not require proving a second deployment shape or its setup surface. PostgreSQL stays the single store so this is a deployment recipe, not a rewrite. See [ADR-0018](adr/adr-0018-hosted-first-local-v2.md). | v1 is proven and there is demand to run it fully on a GM's own hardware |
| **Local model provider (Ollama)** | The offline justification depends on local deployment, which is itself deferred. v1 uses OpenRouter restricted to zero-retention backends. See [ADR-0019](adr/adr-0019-openrouter-privacy-routing.md). | Local deployment is promoted, or a fully-offline path is needed |
| **Automatic entity extraction from PDFs** | Auto-creating NPCs from a module is attractive and unreliable. Manual entry first; the extraction path stays open. | Extraction accuracy can be measured against a fixture corpus |
| **Session recap generation** | Depends on a corpus of session logs existing first. | Session logs are in regular use |

## Acceptance criteria for v1

The MVP is done when all of the following hold:

- **AC-001** A GM uploads a 400-page PDF; it reaches `Indexed` without manual steps, and
  progress is visible throughout.
- **AC-002** A rules question against indexed material returns a grounded answer citing
  its source chunk.
- **AC-003** Asking about material that was never indexed produces an explicit statement
  that the material does not cover it, in the language of the question, before any idea —
  never a plausible invention presented as fact.
- **AC-004** The model is set by admin/env configuration, not a user-facing control;
  changing it serves the next message from the new model with no code change, and the
  Gateway only ever routes to a zero-retention (non-training) provider on the allowlist.
- **AC-005** Characters, factions, and quests survive a restart (real persistence).
- **AC-006** The knowledge graph renders actual relationships from stored data.
- **AC-007** Every designed screen matches the spec's tokens, spacing, and states at both
  desktop and ≤900px.
- **AC-008** Document processing never blocks the UI.
- **AC-009** A user signs up, logs out, logs back in, and finds their campaigns, through
  Supabase Auth — password hashing and session issuance are Supabase's, not custom code.
- **AC-010** One user cannot read another user's campaigns, characters, or documents —
  verified by test, not by inspection.
- **AC-011** A password reset link works once and expires; requesting a reset for an
  unknown address returns the same response as for a known one.
- **AC-012** "Summarise last session" returns a summary drawn from that session's record,
  not from general knowledge.
- **AC-013** "Create an NPC from this module" produces a **draft form**, not a saved row.
  Nothing appears in the NPC list until the GM confirms.
- **AC-014** Each populated field in a proposal cites the chunk it came from; a field with
  no source is marked as unsourced rather than presented as extracted.
- **AC-015** "Find plot holes and propose fixes" returns cited facts and uncited ideas in
  one reply; every paragraph without a valid citation is visibly marked as an idea, by
  label and icon, not colour alone (ADR-0026).
- **AC-016** No citation is attached to invented text: in the model eval, read-aloud and
  suggested fixes carry no `[Sn]` (ADR-0026 IMP-006).
- **AC-017** Unsaved assistant and in-character output is never indexed. Asking about
  something only invented in a conversation returns the AC-003 statement.
- **AC-020** Saying "yes, go with that" yields a `propose_memory` draft and writes
  nothing. After the GM saves it, the note appears in the library, and a question in a
  new conversation cites it.
- **AC-021** A line saved to the style guide changes later drafts in every campaign of
  that GM, and appears in no other user's prompt.
- **AC-022** A question in Polish (or German) over English documents is answered in
  Polish with citations to the English passages; source names keep their original
  spelling.
- **AC-018** A region's page lists its notable children; a region nested three levels deep
  and marked notable is still one click from its parent.
- **AC-019** Read-aloud text and GM notes are visually distinct everywhere both appear.
  Nothing marked GM-private can be surfaced in a read-aloud context.

## Deliberately unresolved

The design has no screen for these; they need design work before implementation:

- **Upload progress at the moment of upload** — the list shows status, but the
  drag-and-drop / file-picker interaction and its immediate feedback are unspecified.
- **Extraction failure** — no designed state for a PDF that cannot be parsed. v1 needs a
  `Failed` treatment with a retry affordance.
- **Empty states** — no designed empty state for a new campaign with no documents, NPCs,
  factions, or quests. This is the *first* thing a new user sees.
- ~~**Citation presentation**~~ — closed: numbered markers and a source list under the
  bubble ([design/overview.md](design/overview.md), AI panel).

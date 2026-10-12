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

Built by hand rather than delegated, because the project is a learning exercise as much as
a tool ([ADR-0008](adr/adr-0008-own-auth-v1.md)).

- Signup, login, logout — argon2 password hashing
- Sessions as signed JWTs in httpOnly, Secure, SameSite cookies
- Google OAuth, full authorization-code flow with `state` validation
- Password reset — single-use expiring tokens, sent by email
- Every route scoped to the authenticated owner (`BND-003`)

### Shell and navigation — Full

- Login screen with **real authentication** ([ADR-0008](adr/adr-0008-own-auth-v1.md)):
  email and password with argon2 hashing, JWT sessions in httpOnly cookies, Google OAuth,
  and password reset
- Campaign picker with add-campaign modal (image + mandatory system)
- App shell: 72px header, floating nav rail (60px ↔ 236px), AI panel column
- Mobile shell ≤900px: bottom tab bar, More sheet, AI slide-over
- Settings: account fields and AI provider selection

### Documents — Full

The differentiating capability. Upload → extract → index → retrieve.

- Upload PDF, Markdown, plain text, and DOCX (not legacy .doc)
- Deterministic extraction (PyMuPDF / pdfplumber), chunking on paragraph and heading
  boundaries, PostgreSQL full-text **and** vector indexing (ADR-0014)
- Deduplication by `sha256` — the same file uploaded twice is not processed twice
- Scanned pages detected and routed to `awaiting OCR`, not `failed`
- Background processing with live status: `Queued` → `Processing` (%) → `Indexed` / `Failed`
- Document list exactly as designed, including per-item progress
- Hybrid search across a campaign's indexed material — keyword and vector, fused (RRF)

### Assistant — Full

Three modes, deliberately separate ([ADR-0012](adr/adr-0012-two-ai-modes.md)). The
separation is the safety property: a GM must never have to infer whether something was
retrieved or invented.

| Mode | Where | Invention |
|------|-------|-----------|
| **Research** | Side panel, every screen | Never — cites sources, refuses when unsupported |
| **Creative** | Its own page | The point — campaign-aware, output is a draft |
| **In character** | Panel, opened from a character | Within one voice; never canon unless saved |


- Chat panel streaming [AG-UI](https://docs.ag-ui.com/) events over SSE ([ADR-0009](adr/adr-0009-ag-ui-protocol.md))
- A **Creative page** for drafting adventures, NPCs, factions, regions, and dialogue
- **In-character chat** entered from a character page, with their portrait in the header
- Retrieval grounded in the active campaign's indexed chunks, with citations
- LLM Gateway abstracting provider; Ollama and Claude both selectable at runtime
- Tool-call indicator chips (the design's green check rows) for every tool that runs
- **Three request shapes** ([ADR-0011](adr/adr-0011-assistant-tools.md)):
  retrieve-and-answer ("what are opportunity attacks?"), fetch-and-transform
  ("summarise last session"), and extract-and-propose ("create an NPC from this module")
- **Proposals, never silent writes.** An extracted entity arrives as a pre-filled form
  citing the chunks each field came from. Nothing is saved until the GM confirms
- Quick-prompt chips, typing indicator, attach affordance

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
| **Cross-encoder reranking** | Hybrid retrieval ships in v1 ([ADR-0014](adr/adr-0014-hybrid-retrieval.md)). Reranking is likely the next quality jump, but it puts a second model in the live query path (PRIN-003) and its gain over RRF is unmeasured here. | It beats plain RRF on the evaluation set (ADR-0014 IMP-004) |
| **Dedicated vector database** | `pgvector` sits in the same row and transaction as the chunk text. A separate store reintroduces the multi-store consistency burden for corpus sizes where it is not the bottleneck. | Measured recall or latency problems, not scale anxiety |
| **OCR for scanned PDFs** | Native-text PDFs cover the common case. OCR adds a heavy dependency chain. The design's `Queued` + "awaiting OCR" state is built; the processor is not. | Users upload scanned material in practice |
| **Multi-agent orchestration** | One assistant with retrieval tools is simpler and easier to evaluate than five agents behind an intent router. | A single agent measurably underperforms on distinct task types |
| **Agent framework (LangChain, Pydantic AI)** | Three or four tools in one bounded loop is not framework territory, and a framework would own prompt assembly — moving the grounding rule out of the Gateway. See [ADR-0011](adr/adr-0011-assistant-tools.md). | Real branching or sub-agents. Reassess Pydantic AI first |
| **Automatic entity extraction on upload** | This is what [ADR-0002](adr/adr-0002-deterministic-extraction.md) forbids: a model in the ingestion path writing unreviewed. A hundred silently created NPCs of uncertain quality is worse than none. | Extraction accuracy is measurable against a fixture corpus |
| **AG-UI beyond streaming** | Sub-agent composition, agent steering, generative UI, and shared-state sync are unused. The protocol is adopted for streaming only. | A second agent, or the UI needs to steer a running one |
| **Managed auth provider (Supabase, Clerk)** | Auth is built by hand deliberately — the project is a learning exercise, and a provider hides the mechanism. See [ADR-0008](adr/adr-0008-own-auth-v1.md). | The maintenance burden outgrows its teaching value |
| **Automatic entity extraction from PDFs** | Auto-creating NPCs from a module is attractive and unreliable. Manual entry first; the extraction path stays open. | Extraction accuracy can be measured against a fixture corpus |
| **Session recap generation** | Depends on a corpus of session logs existing first. | Session logs are in regular use |
| **Plot analysis / suggestions** | Same dependency, plus a much fuzzier success criterion. | Core retrieval is trusted |

## Acceptance criteria for v1

The MVP is done when all of the following hold:

- **AC-001** A GM uploads a 400-page PDF; it reaches `Indexed` without manual steps, and
  progress is visible throughout.
- **AC-002** A rules question against indexed material returns a grounded answer citing
  its source chunk.
- **AC-003** Asking about material that was never indexed produces an explicit "not in
  your material" response, not a plausible invention.
- **AC-004** Switching the provider between Claude and Ollama in Settings changes which
  backend serves the next message, with no code change or restart.
- **AC-005** Characters, factions, and quests survive a restart (real persistence).
- **AC-006** The knowledge graph renders actual relationships from stored data.
- **AC-007** Every designed screen matches the spec's tokens, spacing, and states at both
  desktop and ≤900px.
- **AC-008** Document processing never blocks the UI.
- **AC-009** A user signs up, logs out, logs back in, and finds their campaigns. Passwords
  are stored only as argon2 hashes.
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
- **AC-015** Research mode refuses an unsupported question; Creative mode answers the same
  question by inventing. The two are reachable only from their own surfaces.
- **AC-016** Every message records which mode produced it, and the mode is visible in the
  interface at the time — not inferable only from the text.
- **AC-017** Creative and in-character output is never indexed. Asking Research mode about
  something only invented in Creative mode returns "not in your material".
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
- **Citation presentation** — the assistant must show sources (AC-002), but the design
  does not specify how a citation renders inside a chat bubble.

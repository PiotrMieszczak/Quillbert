# Product Brief

## One line

An in-session workspace for tabletop RPG game masters: campaign material on the left,
an assistant grounded in that material on the right.

## The problem

Running a session means holding too much in your head at once. A GM juggles a rulebook,
an adventure module, their own notes, a cast of NPCs, faction politics, and a quest log —
while improvising in real time in front of players. The failure mode is not *lack of
information*; it is **retrieval latency**. The answer is in the PDF. Finding it takes
ninety seconds, and the table is waiting.

Existing tools solve half of it. Note apps store material but cannot answer questions
about it. Generic AI chat answers questions but invents rules that are not in *your*
books, which is worse than useless at the table.

## The product

Quillbert helps a game master **build** a campaign and **run** it, with an AI that does
both jobs without confusing them.

**One assistant, Quillbert** — the side panel, available while you work
([ADR-0026](adr/adr-0026-one-assistant-claim-provenance.md)). Your uploaded documents are
its source of truth: every fact it states cites the passage it came from, and it says
plainly when your material does not cover a question. Ask it to find a plot hole or
draft a scene and it invents, but every invented paragraph is marked as an idea, never
dressed as a fact. It answers in the language you ask in.

**It remembers what you decide.** When you agree to an idea, Quillbert drafts a note; you
edit it and save it, and it joins your library as a source like any other. Your writing
standards live in a personal style guide it follows in every campaign. Nothing becomes
canon without your Save.

**In character** opens from any character: their portrait and name replace the
assistant's, their sheet and notes become context, and you talk to them directly.

Around all of it sits the session-running workspace the design defines: NPCs, players,
factions, a quest log, session records, and a knowledge graph of how everyone relates.

### Who it is for

Game masters running live sessions, primarily at a table or over video, for systems like
D&D 2024 and Traveller 2e. Single-user, hosted in v1 (local self-hosting is a v2 goal —
[ADR-0018](adr/adr-0018-hosted-first-local-v2.md)). Not a player-facing tool, not a
virtual tabletop, not a campaign-sharing platform.

### The core loop

1. **Prepare** — upload rulebooks, modules, and notes; they are extracted and indexed.
2. **Populate** — record NPCs, players, factions, and quests for the campaign.
3. **Run** — during a session, ask the assistant, consult the graph, update quest state.
4. **Record** — write a session log; it becomes searchable material for next time.

## Product principles

**PRIN-001 — Facts are grounded; inventions are labelled.**
Every statement about the campaign or its rules cites the indexed passage it came from.
When material does not cover a factual question, the assistant says so before offering
anything of its own. Inventing is allowed — finding fixes for a plot hole is invention —
but an invention never carries a citation
([ADR-0026](adr/adr-0026-one-assistant-claim-provenance.md)).

**PRIN-006 — The GM always knows which parts are from their material.**
An invention mistaken for a retrieved fact eventually becomes canon. Provenance is shown
per paragraph: cited text is from the material, uncited text is marked as an idea. Only
what the GM explicitly saves becomes a source.

**PRIN-002 — Extraction is deterministic.**
Text extraction and parsing use libraries, not language models. This keeps ingestion
testable against fixtures, cheap, and reproducible. AI acts only on already-indexed data.
See [adr/adr-0002-deterministic-extraction.md](adr/adr-0002-deterministic-extraction.md).

**PRIN-003 — The session is the priority.**
The workspace is used live, with players waiting. Interactions target under 300ms.
Nothing blocks the GM mid-session; long work (document processing) happens in the
background with visible status.

**PRIN-004 — Hosted first, with real accounts; local is a v2 goal.**
The v1 MVP targets **hosted** deployment — on the maintainer's own hardware or a service —
and proves the product there. Running the full stack locally on a game master's own machine
is a genuine, wanted goal, but it is **deferred to v2**, not a v1 gate
([ADR-0018](adr/adr-0018-hosted-first-local-v2.md)). PostgreSQL stays the single store in
both, so the v2 local path is a deployment recipe rather than a rewrite
([ADR-0013](adr/adr-0013-postgres-for-local-and-hosted.md), retained for its store
decision). v1 has **real authentication** — signup, login, Google OAuth, and password
reset — through **Supabase Auth**, the auth that ships with the Supabase stack the
deployment already runs ([ADR-0020](adr/adr-0020-supabase-auth.md)).

That choice follows from the project's purpose: it is **tool-first** — a personal
replacement for NotebookLM and Claude Desktop for running campaigns — with learning a side
effect, not the origin. A paired consequence of hosting first is the model provider — v1
uses OpenRouter restricted to
zero-retention backends, and the fully-offline local model (Ollama) defers to v2 with local
deployment ([ADR-0019](adr/adr-0019-openrouter-privacy-routing.md)).

**PRIN-005 — The interface is calm.**
Dark, low-chrome, image-forward. The tool sits beside a game; it should not compete with
it for attention.

## What success looks like

The MVP is successful if a GM can:

1. Upload a rulebook and see it reach `Indexed` status without intervention.
2. Ask a rules question mid-session and get a correct answer grounded in that book,
   fast enough not to stall the table.
3. Keep their campaign's NPCs, factions, and quests in the workspace instead of scattered
   notes, and find them faster than before.
4. Ask for plot holes or a new hook, agree to a fix, and save it as a note — with no
   doubt about which parts came from their books and which the model invented — then
   see a later answer cite that note.

If retrieval is not trustworthy, nothing else in the product matters — every other
feature assumes the GM believes the answers.

## Explicit non-goals

- **Not a virtual tabletop.** No maps, tokens, initiative tracking, or dice rolling.
- **Not player-facing.** No player logins, no shared views, no handouts.
- **Not a rules engine.** It retrieves and explains rules; it does not adjudicate them.
- **Not a source of truth about your rules.** Quillbert invents when asked; only its cited
  statements should be trusted as coming from your books.
- **Not multi-tenant.** No hosting, no organisations, no collaboration in v1.

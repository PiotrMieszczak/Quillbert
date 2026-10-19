# Architectural Decision Records

Decisions that constrain implementation live here, not scattered through prose. If a
choice would surprise a new contributor, or if someone might reasonably undo it without
knowing why it was made, it belongs in an ADR.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](adr-0001-react-vite-spa.md) | React + Vite SPA with FastAPI backend | Accepted |
| [0002](adr-0002-deterministic-extraction.md) | Deterministic document extraction, no LLM in the ingestion path | Accepted |
| [0003](adr-0003-sqlite-single-store.md) | SQLite as the single data store; no graph database in v1 | Superseded |
| [0004](adr-0004-css-modules-over-tailwind.md) | CSS Modules over design tokens; Tailwind excluded | Accepted |
| [0005](adr-0005-fts5-before-vectors.md) | FTS5 keyword retrieval before semantic search | Superseded |
| [0006](adr-0006-llm-gateway.md) | Centralized LLM Gateway with runtime provider switching | Superseded |
| [0007](adr-0007-local-profile-auth.md) | Local profile in v1; Supabase Auth when hosting arrives | Superseded |
| [0008](adr-0008-own-auth-v1.md) | Build authentication by hand in v1 | Superseded |
| [0009](adr-0009-ag-ui-protocol.md) | AG-UI protocol for assistant streaming | Accepted |
| [0010](adr-0010-no-agent-framework.md) | No agent framework; own the assistant loop | Superseded |
| [0011](adr-0011-assistant-tools.md) | Assistant tools, and writes go through a proposal | Accepted |
| [0012](adr-0012-two-ai-modes.md) | Two AI modes — Research and Creative — plus in-character roleplay | Accepted |
| [0013](adr-0013-postgres-for-local-and-hosted.md) | PostgreSQL as the single store for local and hosted | Superseded |
| [0014](adr-0014-hybrid-retrieval.md) | Hybrid keyword + vector retrieval with embedded chunks | Superseded |
| [0015](adr-0015-frontend-api-contract.md) | Generated API types and a frontend adapter layer | Accepted |
| [0016](adr-0016-voyage-embeddings.md) | Hybrid retrieval with one fixed hosted embedding model (Voyage) | Superseded |
| [0017](adr-0017-import-sources.md) | Google Drive as an import source; storage chosen per deployment | Accepted |
| [0018](adr-0018-hosted-first-local-v2.md) | Hosted-first MVP; local deployment deferred to v2 | Accepted |
| [0019](adr-0019-openrouter-privacy-routing.md) | OpenRouter as the single provider, zero-retention allowlist | Accepted |
| [0020](adr-0020-supabase-auth.md) | Supabase Auth in v1; the project is tool-first | Accepted |
| [0021](adr-0021-gemini-embeddings-via-openrouter.md) | Hybrid retrieval with Gemini Embedding 2, reached through OpenRouter | Accepted |

## Format

Records follow the structure documented in the `adr` plugin
(see the `llm_utils` marketplace):

- YAML frontmatter: `title`, `status`, `date`, `authors`, `tags`, `supersedes`,
  `superseded_by`
- Sections: Status, Context, Decision, Consequences (positive and negative),
  Alternatives Considered, Implementation Notes, References
- **Coded bullets** — `CON-001`, `POS-001`, `NEG-001`, `ALT-001`, `IMP-001`, `REF-001`.
  Stable identifiers let later records cite a specific point precisely
  ("supersedes ADR-0005 NEG-001") and make records greppable.

Filename convention: `adr-NNNN-[title-slug].md`, sequential four-digit numbering.

## Status values

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion; not yet binding |
| **Accepted** | In force; implementation should follow it |
| **Rejected** | Considered and declined; kept so it is not re-litigated |
| **Superseded** | Replaced by a later ADR, named in `superseded_by` |
| **Deprecated** | No longer applies, with no direct replacement |

Records are immutable once accepted. A changed decision means a **new ADR** that
supersedes the old one — the history of why is as valuable as the current state.

## Decision themes in this set

Two threads run through these records and are worth reading together:

**Where AI is and is not used.** [ADR-0002](adr-0002-deterministic-extraction.md) bars
models from ingestion; [ADR-0006](adr-0006-llm-gateway.md) confines them to a single
gateway at query time. Both are enforced by architectural tests rather than convention,
because both erode the first time someone adds "just one small call".

**The same question, asked twice, with different facts.**
[ADR-0010](adr-0010-no-agent-framework.md) rejected an agent framework given one read-only
tool; [ADR-0011](adr-0011-assistant-tools.md) re-made the case once the assistant gained
several tools and a write. The answer held, but the reasoning had to be redone rather than
assumed — which is what supersession is for. An ADR that quietly read as though "no
framework" were self-evident would hide that it was a close call the second time.

**A superseded record is kept, not deleted.** [ADR-0007](adr-0007-local-profile-auth.md)
deferred authentication to a managed provider; [ADR-0008](adr-0008-own-auth-v1.md) reverses
it once the project's purpose is stated as learning, not shipping. Both are correct under
their own premises, and keeping the first shows *what changed* — the premise, not the
analysis. That is the whole reason accepted records are immutable.

**Deferral with a trigger, not deferral by silence.**
[ADR-0003](adr-0003-sqlite-single-store.md) and
[ADR-0005](adr-0005-fts5-before-vectors.md) each declined infrastructure that earlier
planning treated as given — a graph database and a vector store. Neither was rejected
outright; each named the measurement that would justify revisiting.

**And a trigger that actually fired.** Both were superseded together by
[ADR-0013](adr-0013-postgres-for-local-and-hosted.md) and
[ADR-0014](adr-0014-hybrid-retrieval.md) — not because the analysis was wrong, but because
ADR-0003 ALT-004 named its own revisit condition ("if the product ever becomes hosted or
multi-user") and the product's target changed to include hosting. The premise moved, the
reasoning held, and the conclusion inverted. That is the same shape as 0007 → 0008.

**The same shape, a third time.** [ADR-0018](adr-0018-hosted-first-local-v2.md) and
[ADR-0019](adr-0019-openrouter-privacy-routing.md) moved the premise again: the MVP is now
hosted-first, so 0013's co-equal-deployment framing and 0006's offline-capable provider set
no longer fit v1. In both the earlier conclusion is *retained, not reversed* — PostgreSQL
stays the store (0018), the Gateway stays the one interface (0019) — and only the scope
around it narrows. 0006 ALT-004 named its own revisit ("if the provider count grows
substantially"); a privacy allowlist across several backends is that growth, met by one
OpenRouter integration.

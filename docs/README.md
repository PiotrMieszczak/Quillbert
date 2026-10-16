# Quillbert — Documentation

MVP documentation for **Quillbert** (earlier working names: *DM Assistant*, *Referee*), an
in-session workspace for tabletop RPG game masters. Accepted ADRs keep the earlier names —
records are immutable.

This documentation set is the starting point for a fresh build. It supersedes the
`referee-assistant` proof of concept, whose architecture, agent model, and technical
guides are **not** carried forward. The authoritative inputs are the Claude Design
project *RPG Assistant Design Spec* and the decisions recorded here.

## Reading order

| # | Document | What it answers |
|---|----------|-----------------|
| 1 | [product-brief.md](product-brief.md) | What we are building, for whom, and why |
| 2 | [mvp-scope.md](mvp-scope.md) | What ships in v1 and what explicitly does not |
| 3 | [data-model.md](data-model.md) | Entities, relationships, and storage |
| 4 | [architecture.md](architecture.md) | System shape, stack, and boundaries |
| 4a | [folder-structure.md](folder-structure.md) | Folder layout and dependency rules for both apps |
| 5 | [design/overview.md](design/overview.md) | Screens, layout, and interaction behaviour |
| 6 | [design/reference.md](design/reference.md) | Colors, type, spacing, radii, shadows |

**▶ [Open the interactive design](https://claude.ai/code/artifact/a7d4de30-0826-4747-b295-a584fe6f0f28)** — the running prototype, and
the source of truth for anything visual. Click through it rather than reading about it.

**▶ [Open the architecture board](https://miro.com/app/board/uXjVHrcVIJQ=/)** — the system shape and both
data flows on a Miro board, mirroring [architecture.md](architecture.md).
| 7 | [api-contract.md](api-contract.md) | HTTP surface between frontend and backend |
| 8 | [roadmap.md](roadmap.md) | Delivery phases and acceptance gates |
| 9 | [adr/](adr/) | Architectural Decision Records |

## Status

**Pre-implementation.** No application code exists yet. These documents define the
work; the repository is scaffolded in a later phase (see [roadmap.md](roadmap.md)).

## Source of truth

- **Design** — the [published prototype](https://claude.ai/code/artifact/a7d4de30-0826-4747-b295-a584fe6f0f28), from Claude
  Design project `ec1d38ec-c81f-42b8-8952-7a922851f405` ("RPG Assistant Design Spec"),
  file `Referee Workspace.dc.html`. It is a *reference*, not production code: read it for
  structure, layout, and exact values, and rebuild with the project's own primitives. Its
  runtime (`support.js`) is a build artifact and is never ported.
  The link is pinned to a published version, so the documented design does not shift
  mid-implementation.
- **Decisions** — anything that constrains implementation belongs in [adr/](adr/),
  not in prose scattered across these files.

## Conventions

- Design tokens are the only source of visual values. No hardcoded hex in components.
- **No Tailwind.** Styling is CSS Modules over CSS custom properties (see
  [adr/adr-0004-css-modules-over-tailwind.md](adr/adr-0004-css-modules-over-tailwind.md)).
- Documents state decisions, not aspirations. If something is unbuilt, it is listed
  under "Out of scope" or in the roadmap — never described in the present tense.

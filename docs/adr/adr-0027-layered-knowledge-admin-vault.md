---
title: "ADR-0027: Layered knowledge: an admin vault, a GM library, and the campaign"
status: "Accepted"
date: "2026-10-23"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "retrieval", "assistant", "data-model", "admin"]
supersedes: "ADR-0023"
superseded_by: ""
---

# ADR-0027: Layered knowledge: an admin vault, a GM library, and the campaign

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[ADR-0023](adr-0023-system-rules-library.md) planned one shared scope, a per-system rules
library seeded by an operator. The product now wants more than rules, and more than one
owner:

- **CON-001**: The admin curates what Quillbert needs to be useful to everyone: rules,
  how to build adventures, how to fix plot holes, and one adventure template with a PDF
  layout. It should load only what a task needs, to save tokens.
- **CON-002**: A GM running 5, 10 or 20 campaigns wants Quillbert to be *their*
  assistant: their own references and methods, their templates, their tone, in every
  campaign. The per-user style guide (AC-021, ADR-0026) is the start of this.
- **CON-003**: Arkon, an external knowledge service, was evaluated as the shared library
  (#95, report in `reports/`). It meant a second extraction pipeline, embedding model and
  store. Its access model (departments and tokens) could not express a per-GM library
  without provisioning an identity per GM. Its only meaning-based search needed a patch,
  and returns formatted text. It is not adopted.
- **CON-004**: Ingestion stays deterministic for every layer (ADR-0002, BND-001).
  Citations must keep showing where a fact came from (PRIN-006).

## Decision

**Quillbert owns its knowledge in three layers, nearest first: campaign → GM library →
admin vault. One pipeline, one store, one embedding model serve all three. An admin
manages the vault in the app.**

### Layers × kinds

| Kind | How it reaches the model | Across layers |
|------|--------------------------|---------------|
| **Reference** (rules, lore, notes) | hybrid search, cited as fact | **additive**: all three layers searched in one query |
| **Craft** (adventure building, plot-hole fixing, pacing) | loaded **by task**, never by search rank; never cited as fact | **additive only**: the vault's base always loads. A GM adds their own and may mark one *preferred*, which comes first and wins a conflict. A GM cannot turn the base off. |
| **Template** (adventure, NPC, encounter; structure + PDF layout) | fetched **by name** for the task; shapes the output | **override, nearest wins**: campaign choice → GM profile choice → vault default |
| **Behaviour** (tone, standards) | the GM's style guide, a system block after the prompt (ADR-0026) | layered on the base prompt, never above the grounding rules (PRIN-001) |

### Scope of a document

- **Campaign:** `campaign_id` set, as today.
- **GM library:** `owner_id` set, `campaign_id` null. Visible to every campaign of that GM.
- **Vault:** both null. Visible to every GM.

A GM-library or vault document lists the `systems` it applies to; an empty list means all
systems. Retrieval for a campaign: its own chunks, plus its owner's library, plus the
vault, each filtered to the campaign's system. This runs in one SQL statement, ranked
together, as today.

### Admin

- The admin is a user whose Supabase token carries `app_metadata.role = "admin"`. Only
  Supabase's service role can set `app_metadata`.
- The backend checks that claim on every vault and template write. The UI hiding a button
  is not access control.
- **Screens:**
  - **Vault:** upload, a Markdown editor for craft, tags (kind, systems, licence and
    attribution), delete.
  - **Templates:** with a PDF preview.
  - **Revisions:** every edit to craft or a template is a revision that can be restored.
  - **Probe:** what Quillbert would load for a question in a given system, without
    calling the chat model.
- GMs see the vault read-only.
- What the admin may see of GMs' own content is decided in
  [ADR-0028](adr-0028-safety-without-surveillance.md).

## Consequences

### Positive

- **POS-001**: One ingestion pipeline, one embedding model and one store for everything.
  BND-001 and BND-002 hold without exceptions.
- **POS-002**: A GM's material follows them across campaigns without copies.
- **POS-003**: Craft and templates cost tokens only when the task needs them.
- **POS-004**: Every citation can name its layer, so a GM can tell their own material
  from the vault's (PRIN-006).

### Negative

- **NEG-001**: BND-003 widens. A campaign now reads two shared scopes, its owner's
  library and the vault, and the query must never let one GM's library reach another
  GM's campaign. The test suite must include that case.
- **NEG-002**: Everything in the vault reaches every GM. Only openly licensed or original
  content goes in, with its attribution.
- **NEG-003**: Revisions and the template editor are new code that git would otherwise
  give for free.
- **NEG-004**: Other AI tools can't read the vault until a read-only MCP endpoint exists
  (deferred).

## Alternatives Considered

- **ALT-001: Arkon as the shared library** (CON-003). Two of everything, and a per-GM
  layer it can't represent cheaply. Rejected for this product.
- **ALT-002: Vault as files in git, synced by a command.** Cheaper to build, and history
  comes free. Rejected as the primary path because the admin wants to curate in the
  browser. An export/import command may still mirror the vault to files.
- **ALT-003: Let a GM replace the vault's craft.** Rejected. The base is the quality floor
  every GM gets; a GM's preferred entry already wins a conflict.

## Implementation Notes

- **IMP-001**: `document` and `chunk` gain `owner_id` (nullable) and `systems` (text[]).
  `chunk` copies them from its document. A check allows exactly the three scopes. Craft
  entries are documents with `kind = craft` and a `preferred` flag. They are indexed like
  any document but excluded from reference search.
- **IMP-002**: Templates are their own table: structure as JSON, PDF layout, owner
  (null for the vault), revisions. A choice is stored per GM profile and per campaign.
- **IMP-003**: `RunAssistantTurn` receives the campaign's `system_id` and owner. Today it
  passes `None` (#100).
- **IMP-004**: A citation carries its layer as `attribution` (empty for the campaign
  layer).
- **IMP-005**: `Identity` gains `is_admin` from the verified token. Every vault and
  template write route requires it, with a test that a GM token gets 403.
- **IMP-006**: Stories: #100 (layers), #101 (craft and templates), #102 (admin UI), under
  epic #99.

## References

- **REF-001**: [ADR-0023](adr-0023-system-rules-library.md): superseded; the per-system
  library becomes the vault filtered by `systems`.
- **REF-002**: [ADR-0026](adr-0026-one-assistant-claim-provenance.md): the style guide
  and provenance per claim, unchanged.
- **REF-003**: [ADR-0028](adr-0028-safety-without-surveillance.md): what the admin may
  see.
- **REF-004**: #95: Arkon evaluation.

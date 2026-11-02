---
title: "ADR-0030: Character sheets per system, drafted from the vault's rules and saved by the admin"
status: "Accepted"
date: "2026-11-02"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "data-model", "assistant", "admin"]
supersedes: ""
superseded_by: ""
---

# ADR-0030: Character sheets per system, drafted from the vault's rules and saved by the admin

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

- **CON-001**: `character.stats` is free JSON (DEC-002), `[{k, v}]`. Nothing checks it,
  so a Traveller NPC can carry `WIS 17`, and a skill with a speciality has no place to
  go.
- **CON-002**: NPC and Player pages need to know what a system's stat block holds in
  order to render and edit it. Traveller 2e has six characteristics and skills with
  specialities; D&D 2024 has abilities, saves, AC, HP and Hit Dice.
- **CON-003**: The vault ([ADR-0029](adr-0029-wizard-vault-service.md)) already holds
  each system's character-creation rules. Writing a sheet by hand for each system
  repeats what those rules say.
- **CON-004**: A model reading the rules can misread them (ADR-0011 CON-002). It must
  not touch ingestion (BND-001), and its output is a draft until a person accepts it
  (BND-007).
- **CON-005**: wizard-vault's MCP is read-only, so Quillbert cannot store anything
  there.

## Decision

**Each system has one character sheet, stored in Quillbert. The assistant drafts it
from the vault's rules; the admin reviews it and saves it. The saved sheet renders the
stat block and validates `stats`.**

- **Format:** a small typed sheet, defined by one Pydantic model, not full JSON Schema:
  `sections[{key, label, fields[{key, label, type: int | text | list, min?, max?,
  item_fields?}]}]`, plus `sources[{document_id, heading_path}]`. `list` with
  `item_fields` holds repeating rows such as Traveller skills with a speciality, or
  5e feats. The same model validates `stats` and supplies the JSON Schema the
  model's structured output must follow.
- **Draft:** an admin asks for a draft for a system. Quillbert searches the vault's
  `rules` for that system (character creation, characteristics, skills, combat
  statistics) and reads the top sections in full. One Gateway call returns a sheet in
  which each section names the heading it came from. Nothing is persisted. The prompt
  is versioned and hash-stamped like the chat profiles (ADR-0024).
- **Save:** the admin edits the draft, sees the rendered sheet and its sources, and
  saves. The save is an ordinary validated write to `sheet_template`, one row per
  system.
- **Use:** a character's `stats` is an object keyed by section and field key. When the
  campaign's system has a sheet, every write is validated against it (types, ranges,
  unknown keys rejected). Without a sheet, `stats` is accepted as a free object, as
  DEC-002 allows today.
- **Who:** only an admin (`app_metadata.role = "admin"`, ADR-0027 IMP-005) drafts or
  saves. Every GM reads the sheet of their campaign's system.

### Why this is not a model in ingestion

The model reads chunks that are already indexed and returns a draft that no one has
saved. It does not change what a source says, does not decide what is indexed, and
writes nothing; the admin's save does. This is ADR-0011's proposal rule applied to an
admin artefact, not a campaign one.

## Consequences

### Positive

- **POS-001**: A new system needs rules in the vault and one reviewed draft, not
  hand-written schema code.
- **POS-002**: Stat blocks are checked on write, so pages and the assistant can rely
  on their shape.
- **POS-003**: Every saved sheet keeps the rule headings it was drafted from, so the
  admin can check a field against its source.

### Negative

- **NEG-001**: A wrong draft accepted carelessly reaches every campaign of that system.
  The review screen shows sources beside every section to make checking cheap.
- **NEG-002**: Changing a saved sheet can leave existing `stats` invalid. v1 validates
  on write only; old rows stay readable and are fixed on their next edit.
- **NEG-003**: The format is our own. It cannot express conditional fields, and
  derived values such as characteristic DMs or ability modifiers are not computed.
- **NEG-004**: One sheet per system in v1: no per-GM or per-campaign override yet
  (ADR-0027's nearest-wins rule for templates), and no revisions.

## Alternatives Considered

- **ALT-001: Hand-written sheets uploaded to the vault and fetched by name.** No model
  involved, but every system is manual work, and Quillbert would depend on the vault
  for page rendering, not only for retrieval. Rejected by the maintainer.
- **ALT-002: Sheets fixed in code per system.** Cheapest option, but a new system needs
  a release, and nothing is based on the uploaded rules. Rejected.
- **ALT-003: Full JSON Schema with a generic form renderer.** It is expressive, but the
  renderer is heavy and the drafts become harder to review. Revisit if NEG-003 bites.
- **ALT-004: Store sheets in wizard-vault.** Rejected: its MCP is read-only (CON-005),
  and saving would mean exporting a file and uploading it by hand.

## Implementation Notes

- **IMP-001**: `domain/sheets/` holds the `Sheet` model and `validate_stats(sheet,
  stats)`. The `sheet_template` table has `system_id` (PK, FK `system.id`), `sheet`
  jsonb, `saved_by` and `saved_at`.
- **IMP-002**: `LLMProvider` gains a non-streaming `complete_json(prompt, schema)`,
  implemented inside the Gateway (BND-002).
- **IMP-003**: Routes: `POST /admin/sheets/{system_id}/draft`,
  `PUT /admin/sheets/{system_id}` and `GET /systems/{system_id}/sheet`. A GM token gets
  `403` on both admin routes, with a test.
- **IMP-004**: DEC-002 in `data-model.md` is updated: `stats` is an object validated
  against the system's sheet when one exists.
- **IMP-005**: Stories: #126 (sheets), #107 (cast backend), #110 (detail views).
  Deferred and ticketed: `propose_character` filling a sheet, overrides, revisions.

## References

- **REF-001**: [ADR-0029](adr-0029-wizard-vault-service.md): where the rules come from.
- **REF-002**: [ADR-0011](adr-0011-assistant-tools.md): drafts and the proposal rule.
- **REF-003**: [ADR-0027](adr-0027-layered-knowledge-admin-vault.md) IMP-002 and IMP-005:
  templates as a Quillbert table, and the admin claim.
- **REF-004**: [ADR-0024](adr-0024-quillbert-prompt-profiles.md): prompt versioning.

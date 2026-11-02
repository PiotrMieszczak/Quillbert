---
title: "ADR-0029: The shared vault is wizard-vault, a separate service read over MCP"
status: "Accepted"
date: "2026-11-02"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "retrieval", "assistant", "integration"]
supersedes: ""
superseded_by: ""
---

# ADR-0029: The shared vault is wizard-vault, a separate service read over MCP

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

Replaces the **vault layer** of [ADR-0027](adr-0027-layered-knowledge-admin-vault.md)
only. Its campaign and GM-library layers, and its craft and template rules, stand.

## Context

- **CON-001**: ADR-0027 placed the vault inside Quillbert, with an admin screen, a
  third document scope and revisions. None of it was built. The shelf check in
  `0010_document_layers` allows two scopes, not three.
- **CON-002**: The maintainer wants the same curated rules, craft and templates in
  Claude Code and Codex, not only in Quillbert. ADR-0027 NEG-004 left that as a
  deferred MCP endpoint.
- **CON-003**: Arkon was dropped on 2026-10-26 (#127 closed). Its replacement,
  wizard-vault, is live at `https://wizard-vault.app/mcp`. It is a FastAPI service with
  its own login and a vault per admin, and it uses Quillbert's model-free ingestion,
  chunking and OpenRouter ZDR embedder. It exposes read-only MCP tools: `search`,
  `list_documents`, `get_outline`, `get_section`, `get_template` and `get_links`.
- **CON-004**: Every vault result carries `licence` and `attribution`. ADR-0027 NEG-002
  still holds: everything Quillbert serves from the vault reaches every GM.

## Decision

**The shared vault is wizard-vault. Quillbert reads it over MCP as a third retrieval
source and never writes to it.**

- **Transport:** plain JSON-RPC `tools/call` over HTTPS with `httpx`. The server is
  stateless (no session id), so no MCP SDK is added. Quillbert has its own
  revocable client token (`WIZARD_VAULT_TOKEN`). An empty token disables the source.
- **Retrieval:** a Research turn searches the campaign and the GM library in SQL, as
  today, and the vault with `systems=[campaign.system_id]` and
  `kinds=["rules","lore"]`. The two lists are merged by reciprocal rank. Vault
  documents are tagged with Quillbert's system ids (`traveller-2e`, `dnd-2024`), so
  nothing maps one name to another.
- **Citations:** a vault hit is cited like any other, with `attribution` set to
  `Vault · {title} · {licence}`. The vault has no chunk row in Quillbert, so a citation
  stores a snapshot of the filename, heading and passage.
- **Failure:** a vault timeout or error never fails the turn. The answer comes from
  the campaign and library, with a visible note that the vault was not reached.
- **Content:** only openly licensed or original material goes in the vault Quillbert
  reads. The Traveller rule set there is the maintainer's own summary of the 2D6 core
  mechanics, with no setting content, and is labelled as such.

## Consequences

### Positive

- **POS-001**: One curated library serves Quillbert, Claude Code and Codex.
- **POS-002**: BND-001 holds for vault content too: wizard-vault's ingestion is
  model-free (its ADR-0002), and Quillbert only reads.
- **POS-003**: Quillbert drops ADR-0027's admin vault screens, third scope and
  revisions: code it never had to build.

### Negative

- **NEG-001**: A network call joins every Research turn. It is bounded by a short
  timeout, and losing it degrades the answer rather than failing it.
- **NEG-002**: Ranking crosses two indexes. Reciprocal rank uses only order, so a
  weak vault hit can outrank a strong campaign hit at the same position.
- **NEG-003**: Licence hygiene lives in another app. A mislabelled vault document
  reaches every GM, and Quillbert cannot check it.

## Alternatives Considered

- **ALT-001: ADR-0027's in-app vault.** Rejected: it duplicates what wizard-vault
  already does, and other AI tools cannot read it.
- **ALT-002: Sync vault chunks into Quillbert's tables.** One query and one ranking,
  but a second copy that goes stale, plus a sync job. Revisit if NEG-001 or NEG-002
  hurts in practice.
- **ALT-003: The official `mcp` client SDK.** Session handling Quillbert does not need
  against a stateless server. Revisit if wizard-vault ever needs sessions or
  streaming results.

## Implementation Notes

- **IMP-001**: Adapter `adapters/library/wizard_vault.py`; a combining `ChunkSearch`
  wraps the SQL search and the vault. Closed PR #98 (`arkon.py`, `combined.py`, the
  citation-snapshot migration and their tests) is the starting point.
- **IMP-002**: Settings `wizard_vault_url` and `wizard_vault_token`, with the token in
  Openship as `WIZARD_VAULT_TOKEN`.
- **IMP-003**: Tests: adapter (httpx mock transport), merge order, the vault-down note,
  and a Research turn that cites a vault passage. Story #125.
- **IMP-004**: Retrieving craft and templates from the vault by task is deferred.

## References

- **REF-001**: [ADR-0027](adr-0027-layered-knowledge-admin-vault.md): layers; its vault
  layer is replaced here.
- **REF-002**: [ADR-0002](adr-0002-deterministic-extraction.md), BND-001.
- **REF-003**: [ADR-0021](adr-0021-gemini-embeddings-via-openrouter.md): the embedding
  model wizard-vault also uses.
- **REF-004**: #112 (wizard-vault), #119 (this ADR), #125 (adapter).

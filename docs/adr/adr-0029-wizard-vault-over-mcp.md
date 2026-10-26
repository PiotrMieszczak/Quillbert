---
title: "ADR-0029: The shared vault is upstream Arkon, consumed over MCP"
status: "Accepted"
date: "2026-10-26"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "retrieval", "mcp", "deployment"]
supersedes: "ADR-0027 (vault layer only)"
superseded_by: ""
---

# ADR-0029: The shared vault is upstream Arkon, consumed over MCP

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

[ADR-0027](adr-0027-layered-knowledge-admin-vault.md) put all three knowledge layers,
campaign, GM library and admin vault, in Quillbert's own store. The vault has since moved
out (#112, epic #99):

- **CON-001**: The vault serves every GM and, through MCP, other AI tools too (ADR-0027
  NEG-004). It is a module of its own, `wizard-vault`, not a scope inside one campaign
  database.
- **CON-002**: Arkon (`nduckmink/arkon`) already does the vault's job: ingestion, search
  and an MCP server. It was rejected in ADR-0027 ALT-001 because it could not hold a
  per-GM layer. The vault has no per-GM layer, so that objection does not apply to it.
- **CON-003**: On 2026-10-26 the maintainer chose to use upstream Arkon directly for the
  MVP: no fork, no mirror, no custom service. Fixes go upstream.
- **CON-004**: Ingestion stays model-free (ADR-0002, BND-001), and every model call stays
  on a zero-retention route (ADR-0019, BND-002), in this module as in the app.

## Decision

**The shared vault, `wizard-vault`, is upstream Arkon pinned at `5e4069d` and consumed
over MCP. There is no fork or mirror. Its configuration lives in this repository under
`deploy/wizard-vault/`. Fixes go upstream as pull requests (#121).**

- This replaces ADR-0027's **vault layer only**. The campaign and GM-library layers stay in
  Quillbert's store, as ADR-0027 decided.
- Moving the pin is a reviewed change to `deploy/wizard-vault/`, made after the upstream
  change it needs has merged.
- Deployment is #120; seed content is #122.

## Consequences

### Positive

- **POS-001**: No vault code to build or maintain: ingestion, search and the MCP server
  come from upstream.
- **POS-002**: Any MCP client can read the vault, which closes ADR-0027 NEG-004.
- **POS-003**: Fixes we need land upstream and help other Arkon users, rather than living
  in a fork we would have to rebase.

### Negative

- **NEG-001**: Arkon is licensed under PolyForm Internal Use 1.0.0. Until the licensor
  answers (#124), only the maintainer may use the vault; it is not offered to other GMs.
- **NEG-002**: Two stores now exist, Quillbert's and the vault's, each with its own
  extraction and embeddings. ADR-0027 POS-001 (one pipeline, one store) no longer holds
  for the vault.
- **NEG-003**: Import must use `preserve_verbatim` with wiki synthesis off, so that no
  model touches ingestion (BND-001). Any other import mode breaks citations and is not
  allowed.
- **NEG-004**: Two upstream defects stay open until their fixes merge (#121): the
  `project_ids` crash and the stray gitlink. Until then we work around them in
  `deploy/wizard-vault/`, not in a fork.

## Alternatives Considered

- **ALT-001: Keep the vault in Quillbert's store** (ADR-0027). One store, but the admin
  UI, revisions and an MCP endpoint all to build. Rejected for the MVP.
- **ALT-002: Fork or mirror Arkon.** Lets us patch freely, but every upstream change
  becomes a rebase. Rejected (CON-003).
- **ALT-003: A custom vault service.** Most control, most code. Rejected (CON-003).

## Implementation Notes

- **IMP-001**: AI clients get only the read-only MCP tools. No write tool is exposed to
  them (BND-007).
- **IMP-002**: Every result carries a licence line naming its source and attribution
  (ADR-0027 NEG-002, PRIN-006).
- **IMP-003**: Embeddings run only through an OpenRouter zero-retention route, as in
  [ADR-0021](adr-0021-gemini-embeddings-via-openrouter.md), or are off.
- **IMP-004**: Issues: #120 (deploy), #121 (upstream PRs), #122 (seed content), #123
  (Openship takeover), #124 (licensor question), under #112.

## References

- **REF-001**: [ADR-0027](adr-0027-layered-knowledge-admin-vault.md): its vault layer is
  replaced; the campaign and GM-library layers stand.
- **REF-002**: [ADR-0002](adr-0002-deterministic-extraction.md): no model in ingestion.
- **REF-003**: [ADR-0019](adr-0019-openrouter-privacy-routing.md) and
  [ADR-0021](adr-0021-gemini-embeddings-via-openrouter.md): zero-retention routing and
  embeddings.
- **REF-004**: Upstream: <https://github.com/nduckmink/arkon>, commit `5e4069d`.

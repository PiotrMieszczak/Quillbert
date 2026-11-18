---
title: "ADR-0031: A GM connects read-only knowledge sources over MCP"
status: "Accepted"
date: "2026-11-18"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "retrieval", "assistant", "integration", "security", "privacy"]
supersedes: ""
superseded_by: ""
---

# ADR-0031: A GM connects read-only knowledge sources over MCP

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

Replaces the **Transport** paragraph of
[ADR-0029](adr-0029-wizard-vault-service.md) only. Its retrieval, citation, failure and
content rules stand, and wizard-vault becomes one source read through the client decided
here.

## Context

- **CON-001**: ADR-0029 gave Quillbert one MCP source, configured by the operator. GMs
  keep material elsewhere too: a rules reference such as a 5e.tools server, notes, boards,
  the web.
- **CON-002**: A server a GM names is untrusted. Its URL can point at Quillbert's own
  network, its tool descriptions and results can carry instructions, and its
  `readOnlyHint` is its own claim.
- **CON-003**: Anything sent to such a server leaves the zero-retention allowlist of
  [ADR-0019](adr-0019-openrouter-privacy-routing.md).
- **CON-004**: MCP servers also send mail, post to chat and run code. Quillbert answers
  from material; it does not act for the GM in other systems.
- **CON-005**: There is no tool loop yet. `run_turn.py` retrieves, then streams
  ([ADR-0011](adr-0011-assistant-tools.md)'s tools are not built).
- **CON-006**: ADR-0029 chose stateless JSON-RPC with no session. Servers in general
  require `initialize`, may issue a session id, and may answer as an SSE stream.

## Decision

**A GM may connect MCP servers as read-only knowledge sources. Quillbert reads through
a connection and never sends, posts or writes through one.**

1. **What fits.** A place the GM's material lives, useful with read tools alone: rules
   and reference, notes and wikis, files, boards, campaign managers, web search. Not
   mail, chat, calendar, payments, code or shell. Not a server that wraps a model or an
   agent (BND-002), and not a memory service (ADR-0026).
2. **Two paths.** A *custom server* the GM adds by URL, and later a *catalog* of vetted
   entries with OAuth and a tool allowlist written by us. The catalog is a constant in
   the repository.
3. **Transport.** Streamable HTTP over HTTPS only. No stdio. The client is hand-written
   on sync `httpx`: `initialize`, `notifications/initialized`, `tools/list`,
   `tools/call`, with JSON or SSE replies and the session id carried.
4. **Address guard.** HTTPS only, no credentials in the URL, and every address the host
   resolves to must be public. The socket goes to the address that was checked, with TLS
   verified against the name. Redirects are not followed. The guard runs on every call.
5. **Limits.** 3 s to connect, 8 s per reply, 256 KB per reply, three connections per
   GM. A source that fails never fails the turn; the reply says it was not reached.
6. **How a source is used.** Phase 1: the GM ticks tools, and each turn Quillbert calls
   them with the question. The model sees results as sources and never sees tool names
   or descriptions. A tool the server marks as not read-only cannot be ticked. Phase 2
   lets the model choose among the ticked tools, inside ADR-0011's bounded loop.
7. **What is sent.** The GM's question text and nothing else. No chunks, no history, no
   character or faction fields, so `notes` cannot leave (DEC-004).
8. **Consent and scope.** A connection belongs to one GM and is off for a campaign until
   that GM switches it on. Saving one requires consent to the text that says questions
   leave Quillbert; the time is stored.
9. **Secrets.** One bearer token per connection, encrypted at rest with a key from the
   environment. It is never returned by the API and never logged.
10. **Citations.** A result is cited as `External · {name}`, or `Web · {domain}`, with a
    snapshot of the passage on the citation (ADR-0029). It is never indexed (AC-017).

## Consequences

### Positive

- **POS-001**: A GM's reference lives where they keep it and still reaches the answer.
- **POS-002**: One client serves wizard-vault and every GM connection.
- **POS-003**: In phase 1 a hostile server cannot steer a tool call: the model chooses
  no tool and writes no argument.
- **POS-004**: BND-007 holds without an exception. A result is context; nothing a server
  returns can write to the campaign.

### Negative

- **NEG-001**: "Zero-retention only" is no longer the whole privacy rule
  ([ADR-0026](adr-0026-one-assistant-claim-provenance.md) POS-004, ADR-0019 CON-002).
  Model calls still obey it; a question sent to a connection does not. The GM opts in
  per connection and per campaign.
- **NEG-002**: A citation to an external source is not backed by deterministic
  extraction ([ADR-0002](adr-0002-deterministic-extraction.md), ADR-0029 POS-002). A
  server can return text a model wrote. The label shows where it came from; it does not
  make it true. PRIN-001's "indexed passage" wording changes with the retrieval story.
- **NEG-003**: BND-003 gains a read scope per GM. One GM's connection must never be
  called for another GM's campaign, and the suite must test it.
- **NEG-004**: Read-only cannot be verified. A server may lie in `readOnlyHint`, and a
  GM may tick a tool with side effects on their own server.
- **NEG-005**: Each enabled connection adds a network round trip of up to 8 s to a turn,
  and one more index to the rank fusion of ADR-0029 NEG-002.
- **NEG-006**: A GM can connect a read-only tool that is off-purpose, such as a mail
  search. Decision 1 is enforced for actions, not for every kind of reading.

## Alternatives Considered

- **ALT-001: The official `mcp` SDK.** It is async and opens its own connections. The
  backend is sync, and the guard must own the socket target. Revisit if the protocol
  outgrows three methods.
- **ALT-002: Catalog only, no custom URL.** No user-supplied address at all, but no
  hosted server exists for 5e.tools, Obsidian, Kanka or Foundry. Rejected by the
  maintainer: which reference a GM reads is the GM's choice.
- **ALT-003: Model-driven tools from the start.** Needed for sources that take two
  steps, find then read. It requires the tool loop first and widens the injection
  surface. It is phase 2, not rejected.
- **ALT-004: stdio servers run by Quillbert.** Rejected: it executes a GM's code on the
  host.
- **ALT-005: Send retrieved context so servers can rank better.** Rejected: it sends
  campaign text out, and `notes` with it.

## Implementation Notes

- **IMP-001**: Port `ports/mcp.py`; adapter `adapters/mcp/` with `client.py` and
  `address_guard.py`. Tests use `httpx.MockTransport` and a stub resolver. Story #158.
- **IMP-002**: The guard checks the IPv4 address inside an IPv4-mapped or DNS64
  (`64:ff9b::/96`) address, so an IPv6-only host cannot be used to reach private IPv4.
- **IMP-003**: Registration API, `mcp_server` and `campaign_mcp_server`, the encrypted
  token and the rate limit on "test connection": #159.
- **IMP-004**: Retrieval merge, external citations and the not-reached note: #160.
  wizard-vault through the same client: #125.
- **IMP-005**: Settings screen with the Connections card: #161.
- **IMP-006**: OAuth, the catalog and the phase 2 tool loop get their own stories under
  #157. Figma's server refuses clients outside its allowlist and is not planned.

## References

- **REF-001**: [ADR-0029](adr-0029-wizard-vault-service.md): its transport is replaced
  here.
- **REF-002**: [ADR-0011](adr-0011-assistant-tools.md), BND-007.
- **REF-003**: [ADR-0019](adr-0019-openrouter-privacy-routing.md), BND-002.
- **REF-004**: [ADR-0026](adr-0026-one-assistant-claim-provenance.md), BND-008, AC-017.
- **REF-005**: [ADR-0027](adr-0027-layered-knowledge-admin-vault.md), BND-003.
- **REF-006**: [ADR-0028](adr-0028-safety-without-surveillance.md): limits.
- **REF-007**: #157 (epic), #158 to #161.

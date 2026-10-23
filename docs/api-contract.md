# API Contract

Base path `/api/v1`. JSON throughout, except the assistant stream (SSE) and uploads
(multipart). All resources except campaigns are scoped to a campaign and enforce that
scope server-side (BND-003).

## Conventions

- IDs are integers except `campaign.id`, an opaque string (random, not derived from the name)
- All endpoints require a Supabase bearer token (see Auth)
- Timestamps are ISO 8601 UTC
- Errors: `{ "detail": "message" }` with a conventional status code
- Collections return bare arrays; v1 has no pagination (single-user scale)

## Auth

Identity is **Supabase Auth** ([ADR-0020](adr/adr-0020-supabase-auth.md)). The SPA signs
in, signs up, resets passwords and does Google OAuth against Supabase directly
(`supabase-js`); **this API has no `/auth/*` endpoints** and mints no tokens.

The SPA sends the Supabase access token on every request:

```
Authorization: Bearer <access_token>
```

The backend verifies it against the project's JWKS (`<SUPABASE_URL>/auth/v1/.well-known/jwks.json`):
signature, `exp`, `iss` = `<SUPABASE_URL>/auth/v1`, `aud` = `authenticated`, and a `sub`.
A missing, malformed, expired or foreign token returns `401` with
`WWW-Authenticate: Bearer`. With `SUPABASE_URL` unset the backend still boots but returns
`401` everywhere (fail closed).

Password-reset requests (AC-011) are answered by Supabase, which does not reveal whether an
address is registered; the SPA shows the same message either way.

**Every endpoint requires a valid token** and is scoped to the authenticated user.
Unauthenticated requests return `401`; requesting another user's resource returns `404`,
not `403` — a `403` confirms the resource exists.

## Campaigns

| Method | Path | Purpose |
|--------|------|---------|
| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| `GET` | `/campaigns` | The caller's campaigns for the picker, most recently played first, then newest | Built |
| `POST` | `/campaigns` | Create — `name` and `systemId` required | Built |
| `GET` | `/campaigns/{id}` | Single campaign | Built |
| `POST` | `/campaigns/{id}/image` | Set or replace the banner (multipart, field `file`) | Built |
| `GET` | `/campaigns/{id}/image` | The banner bytes | Built |
| `PATCH` | `/campaigns/{id}` | Rename, change tint | Planned |
| `DELETE` | `/campaigns/{id}` | Delete campaign and all contents | Planned |

```jsonc
// POST /campaigns
{ "name": "Ashfall Reach", "systemId": "dnd-2014", "tint": "#EF7777" }
// 201
{ "id": "3f0c9a…", "name": "Ashfall Reach",
  "system": { "id": "dnd-2014", "name": "D&D 2014" },
  "tint": "#EF7777", "imageUrl": null, "sessionCount": 0, "lastPlayedAt": null }
```

- A missing `systemId` is a `422` (request validation); an unknown one is a `422` with
  `{ "detail": "unknown system '…'" }`.
- `name` is trimmed and whitespace-collapsed; empty or over 120 characters is a `400`.
- `tint` is optional (default `#E8B87A`) and must be `#RRGGBB`, else `400`. The SPA picks it
  from the system: D&D 2014 `#EF7777`, D&D 2024 `#E8B87A`, Traveller 2e `#7BA3D6`.
- `sessionCount` is `0` until sessions exist.
- Every campaign belongs to the caller (DEC-005). Another user's campaign is a `404`, here
  and on every route under `/campaigns/{id}/…` (documents, conversations).

**Banner.** `POST /campaigns/{id}/image` accepts PNG, JPEG or WebP, judged by the bytes,
up to 10 MB: anything else is `415`, larger is `413`. It answers `200` with the campaign.
Replacing a banner deletes the old file. `imageUrl` is the API path of the image with a
version query (`/api/v1/campaigns/{id}/image?v=…`) that changes with each upload, so the
response may be cached forever. It needs the bearer token like any other route, so the SPA
fetches it and shows it from a blob URL rather than pointing an `<img>` at it.

`GET /systems` — the systems the add-campaign picker offers, by name.

```jsonc
// GET /systems
[{ "id": "dnd-2014", "name": "D&D 2014" }, { "id": "dnd-2024", "name": "D&D 2024" },
 { "id": "traveller-2e", "name": "Traveller 2e" }]
```

## Documents

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/campaigns/{cid}/documents` | List with status and progress |
| `POST` | `/campaigns/{cid}/documents` | Upload (multipart) — returns `202` |
| `GET` | `/campaigns/{cid}/documents/{id}` | Single document, for polling |
| `POST` | `/campaigns/{cid}/documents/{id}/retry` | Re-run a failed extraction |
| `DELETE` | `/campaigns/{cid}/documents/{id}` | Remove document, chunks, and index rows |

```jsonc
// GET /campaigns/ashfall/documents
[
  { "id": 1, "filename": "Core Rulebook v3.pdf", "kind": "PDF", "pageCount": 412,
    "meta": "stat blocks · rules", "status": "indexed", "progress": 100, "error": null },
  { "id": 3, "filename": "Bestiary — Regional.pdf", "kind": "PDF", "pageCount": 156,
    "meta": "extracting stat blocks", "status": "processing", "progress": 64, "error": null }
]
```

`POST` takes one multipart field, `file`. It accepts `.pdf`, `.md`, `.txt` and `.docx`
(not legacy `.doc`), checked by extension **and** by the file's first bytes, up to
`MAX_UPLOAD_MB` (default 200). A bare file name is kept; any client path is dropped.

| Status | When |
|--------|------|
| `202` | New document, `status: "queued"`, `progress: 0` |
| `200` | Uploading a file whose `sha256` already exists in the campaign returns the existing document and stores nothing new (ADR-0021 IMP-003) |
| `400` | Empty file, missing or over-long file name |
| `413` | Larger than the limit |
| `415` | Unsupported extension, or content that does not match it |
| `422` | No `file` part in the request |

A document is only visible inside its campaign: another campaign's id answers `404`, and
the same bytes in two campaigns are two documents.

### My library ([ADR-0027](adr/adr-0027-layered-knowledge-admin-vault.md))

The same document shape on one more shelf, outside any campaign. Research in a campaign
also searches its owner's library documents for the campaign's system. The shared vault is
an external service ([#112](https://github.com/PiotrMieszczak/Quillbert/issues/112)), not
a shelf here.

| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| `GET` | `/library/documents` | the caller | Their own library |
| `POST` | `/library/documents` | the caller | Upload: `file`, `systems` (comma-separated system ids; empty = all) |
| `DELETE` | `/library/documents/{id}` | the caller | Remove; another GM's id is `404` |

An unknown system id is `400`. Library documents carry `"systems": [...]` in the response;
campaign documents have `[]`.

`DELETE` answers `204` with no body and removes the row and its stored file (chunks and
index rows go with it once extraction exists). A missing id, or one from another campaign,
is `404`. Afterwards the same bytes can be uploaded again as a new document.

Upload returns `202 Accepted` immediately with `status: "queued"`. The client polls this
list while any document is `queued`, `processing`, or `awaiting_ocr`, then stops (PRIN-003 — upload never
blocks).

## Search

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/campaigns/{cid}/search?q=` | Hybrid search over indexed chunks — keyword + vector, RRF-fused |

```jsonc
[{ "chunkId": 812, "documentId": 1, "filename": "Core Rulebook v3.pdf",
   "heading": "Opportunity Attacks", "pageFrom": 195, "pageTo": 195,
   "snippet": "…when a hostile creature <mark>leaves your reach</mark>…",
   "score": 0.0312, "matchedBy": ["keyword", "vector"] }]
```

`score` is the fused RRF score, not a keyword rank — it is comparable between results of
one query, not across queries. `matchedBy` says which retriever(s) surfaced the chunk,
which is what makes a bad result diagnosable (ADR-0021 NEG-002).

An empty array means nothing cleared the relevance floor. That is a real answer, not an
error: the assistant says the material does not cover it rather than answering from weak matches (AC-003).

## Characters

Covers NPCs and player characters; `isPlayer` selects the list.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/campaigns/{cid}/characters?isPlayer=&relationship=` | Filtered list |
| `POST` | `/campaigns/{cid}/characters` | Create |
| `GET` | `/campaigns/{cid}/characters/{id}` | Detail with connections |
| `PATCH` | `/campaigns/{cid}/characters/{id}` | Update |
| `DELETE` | `/campaigns/{cid}/characters/{id}` | Delete |
| `POST` | `/campaigns/{cid}/characters/{id}/portrait` | Multipart upload |

```jsonc
{ "id": 4, "name": "Brother Cael", "role": "Human Cleric", "level": 5,
  "isPlayer": true, "relationship": "ally", "location": "The Party",
  "disposition": "Steadfast", "lastSeen": "Session 13",
  "armorClass": "18", "hitPoints": "47", "speed": "30 ft",
  "stats": [{ "k": "STR", "v": 14 }, { "k": "WIS", "v": 17 }],
  "tags": ["Healer", "Faith"],
  "quote": "The Light does not ask who deserves it.",
  "notes": "Ties the party to Mother Ansel's temple faction.",
  "portraitUrl": null,
  "playerProfile": { "playerName": "Jordan Kim", "class": "Cleric (Light)",
                     "race": "Human", "background": "Acolyte", "xp": "6,500",
                     "pronouns": "they/them", "bonds": "Sworn to the temple…" },
  "connections": [{ "targetType": "character", "targetId": 7,
                    "name": "Mother Ansel", "kind": "ally" }] }
```

`notes` is GM-private and excluded from assistant context by default (DEC-004).

## Factions

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/campaigns/{cid}/factions` | List |
| `POST` | `/campaigns/{cid}/factions` | Create |
| `GET` | `/campaigns/{cid}/factions/{id}` | Detail with members and connections |
| `PATCH` | `/campaigns/{cid}/factions/{id}` | Update |
| `DELETE` | `/campaigns/{cid}/factions/{id}` | Delete |
| `PUT` | `/campaigns/{cid}/factions/{id}/members` | Replace membership (character ids) |

## Relationships

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/campaigns/{cid}/relationships` | All edges, for the graph |
| `POST` | `/campaigns/{cid}/relationships` | Create an edge |
| `PATCH` | `/campaigns/{cid}/relationships/{id}` | Change kind |
| `DELETE` | `/campaigns/{cid}/relationships/{id}` | Remove |

```jsonc
// GET /campaigns/ashfall/graph — nodes and edges ready to render
{ "nodes": [{ "id": "character:4", "type": "character", "name": "Brother Cael",
              "role": "Human Cleric", "level": 5, "faction": "The Ashfall Temple",
              "relationship": "ally" }],
  "edges": [{ "id": 12, "source": "character:4", "target": "faction:2", "kind": "ally" }] }
```

## Quests

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/campaigns/{cid}/quests?status=` | List, optionally by status tab |
| `POST` | `/campaigns/{cid}/quests` | Create, optionally with `parentQuestId` |
| `PATCH` | `/campaigns/{cid}/quests/{id}` | Update fields, progress, or status |
| `DELETE` | `/campaigns/{cid}/quests/{id}` | Delete |

Status transitions — including Reactivate from `failed` or `inactive` back to
`inprogress` — are ordinary `PATCH` calls on `status`.

## Sessions

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/campaigns/{cid}/sessions` | List, newest first |
| `POST` | `/campaigns/{cid}/sessions` | Create from the composer |
| `PATCH` | `/campaigns/{cid}/sessions/{id}` | Update |
| `DELETE` | `/campaigns/{cid}/sessions/{id}` | Delete |

Creating or updating a session re-chunks and re-indexes its body so past sessions are
retrievable alongside documents.

## Assistant

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/campaigns/{cid}/conversations` | List |
| `POST` | `/campaigns/{cid}/conversations` | Start one |
| `GET` | `/campaigns/{cid}/conversations/{id}/messages` | History with citations |
| `POST` | `/campaigns/{cid}/conversations/{id}/messages` | Send; responds as SSE |

The send body is AG-UI's `RunAgentInput`, so any AG-UI client can drive the endpoint
(the panel uses `@ag-ui/client`'s `HttpAgent`). The server owns history and the prompt:
it reads **only the content of the last user message** and ignores client-sent history,
`tools`, `context` and `state`. `threadId` must equal the conversation id in the path.

```jsonc
// POST .../conversations/12/messages   (Accept: text/event-stream)
{ "threadId": "12", "runId": "run-88",
  "messages": [{ "id": "u-1", "role": "user", "content": "How does grappling work?" }],
  "tools": [], "context": [], "state": null, "forwardedProps": {} }
  // One profile (ADR-0026): no mode field. Nothing in the body carries prompt text.

// GET .../messages → MessageOut[]
{ "id": 57, "role": "assistant", "content": "A grapple is … [S1]",
  "createdAt": "…",
  "citations": [{ "label": "S1", "chunkId": 812, "documentId": 1,
                  "filename": "SRD 5.2.pdf", "pageFrom": 177, "heading": "Grappled",
                  "attribution": "SRD 5.2 · CC-BY-4.0" }] }
  // attribution: "My library" for a GM-library passage (ADR-0027); null for the
  // campaign's own documents.
```

`GET /campaigns/{cid}/conversations` lists newest first. The panel opens the newest one, or
starts one on the first send.

**Streaming response.** `text/event-stream`, carrying
[AG-UI](https://docs.ag-ui.com/concepts/events) events in the protocol's own framing: one
`data:` line per event, a JSON object with a `type` field
([ADR-0009](adr/adr-0009-ag-ui-protocol.md)). The server encodes them with the
`ag-ui-protocol` package's `EventEncoder`; the panel decodes them with `@ag-ui/client`.
Neither side hand-writes event types. The protocol defines the schema; this contract
documents only what is product-specific.

```
data: {"type":"RUN_STARTED","threadId":"12","runId":"run-88"}

data: {"type":"TOOL_CALL_START","toolCallId":"t1","toolCallName":"search_documents"}

data: {"type":"TOOL_CALL_ARGS","toolCallId":"t1","delta":"{\"query\":\"How does grappling work?\"}"}

data: {"type":"TOOL_CALL_END","toolCallId":"t1"}

data: {"type":"TOOL_CALL_RESULT","messageId":"t1-result","toolCallId":"t1","content":"Searched 2 documents · 6 passages"}

data: {"type":"TEXT_MESSAGE_START","messageId":"57","role":"assistant"}

data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"57","delta":"A grapple is"}

data: {"type":"TEXT_MESSAGE_END","messageId":"57"}

data: {"type":"CUSTOM","name":"dm.citation","value":{"label":"S1","chunkId":812,"documentId":1,"filename":"Core Rulebook v3.pdf","pageFrom":195,"heading":"Opportunity Attacks","attribution":null}}

data: {"type":"RUN_FINISHED","threadId":"12","runId":"run-88"}
```

On failure after `RUN_STARTED` (provider error, timeout, database error) the stream ends
with `{"type":"RUN_ERROR","message":"…","code":"provider_error"}` and no assistant message
is stored. Client disconnect closes the upstream provider stream.

**Proposals arrive as a custom event too.** An extracted entity is not written; it is
emitted for the GM to confirm ([ADR-0011](adr/adr-0011-assistant-tools.md)):

```
data: {"type":"CUSTOM","name":"dm.proposal","value":{
        "kind":"character",
        "draft":{"name":"Brother Cael","role":"Human Cleric","level":5},
        "sources":{"name":[812],"role":[812],"level":[815]}}}
```

`sources` maps each populated field to the chunks it came from. A field absent from
`sources` was invented by the model and the form marks it as unsourced. The GM submits the
result through the ordinary `POST /campaigns/{cid}/characters` — there is no privileged
assistant write path.

**Memory drafts are a model tool call.** When the GM agrees to something, the model calls
`propose_memory`; the server streams the call and writes nothing
([ADR-0026](adr/adr-0026-one-assistant-claim-provenance.md)):

```
data: {"type":"TOOL_CALL_START","toolCallId":"t2","toolCallName":"propose_memory"}

data: {"type":"TOOL_CALL_ARGS","toolCallId":"t2","delta":"{\"target\":\"campaign\",\"title\":\"Old Tam kept the signet\",\"body\":\"Old Tam (Abbot Corvin) kept the Abbot's signet ring…\"}"}

data: {"type":"TOOL_CALL_END","toolCallId":"t2"}
```

The panel renders the arguments as an editable card. `target` is `campaign` or `style`;
`title` is under 8 words; `body` is Markdown in the language of the GM's message. Save:

- `campaign` → the ordinary `POST /campaigns/{cid}/documents` with a file
  `notes/<slug>.md` holding `# <title>` and the body. It is indexed and cited like any
  upload.
- `style` → `PATCH /settings` with `styleGuide` set to the current guide plus the body.

Discarding the card sends nothing.

**Citations are a custom event.** AG-UI has no citation type — grounding is a product
concern, not a protocol one — so they are emitted as a namespaced `dm.citation` custom
event. That keeps the product-specific part visibly distinct from the protocol.

Tool-call events drive the design's green check chips. Citation events populate source
references (AC-002). When retrieval finds nothing relevant, the assistant says so
explicitly rather than answering unsourced (AC-003).

Citations follow `TextMessageEnd`: they are parsed from the finished text. The panel marks
each paragraph that holds none of the cited labels as an idea (ADR-0026). The retrieval
step is reported as the `search_documents` tool call above even though the server runs
it, not the model; `propose_memory` is the only model-driven tool, in a loop bounded at 5
iterations. There is no `dm.proposal` yet.

A stream always opens with `RUN_STARTED` and closes with exactly one of `RUN_FINISHED` or
`RUN_ERROR`. A stream ending without either is a bug: the client cannot tell it from a
dropped connection.

## Settings

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/settings` | Profile fields, including `styleGuide` |
| `PATCH` | `/settings` | Update profile fields, including `styleGuide` (the per-user style guide, ADR-0026) |
| `POST` | `/settings/avatar` | Multipart upload |
| `GET` | `/settings/ai` | Gateway reachability and the active model (read-only) |

```jsonc
// GET /settings/ai — read-only; the model is admin/env config, not selectable here (ADR-0019)
{ "model": "google-vertex/gemini-2.5-pro", "label": "Gemini 2.5 Pro (Vertex)",
  "available": true }
```

There is no provider or model picker: the active model is set by admin/env configuration,
and the Gateway only ever routes to a zero-retention (non-training) provider on the
allowlist ([ADR-0019](adr/adr-0019-openrouter-privacy-routing.md), AC-004).

# API Contract

Base path `/api/v1`. JSON throughout, except the assistant stream (SSE) and uploads
(multipart). All resources except campaigns are scoped to a campaign and enforce that
scope server-side (BND-003).

## Conventions

- IDs are integers except `campaign.id`, which is a slug
- All endpoints except `/auth/*` require an authenticated session
- Timestamps are ISO 8601 UTC
- Errors: `{ "detail": "message" }` with a conventional status code
- Collections return bare arrays; v1 has no pagination (single-user scale)

## Auth

Sessions are signed JWTs delivered in **httpOnly, Secure, SameSite=Lax cookies** — not in
response bodies, and never in `localStorage`. The browser attaches them automatically, so
no `Authorization` header is used ([ADR-0008](adr/adr-0008-own-auth-v1.md)).

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/auth/signup` | Create an account; sets session cookies |
| `POST` | `/auth/login` | Email and password; sets session cookies |
| `POST` | `/auth/logout` | Clears cookies, revokes the refresh token |
| `POST` | `/auth/refresh` | Exchanges the refresh cookie for a new access cookie |
| `GET` | `/auth/me` | The current user, or `401` |
| `GET` | `/auth/google` | Starts the OAuth flow; redirects to Google |
| `GET` | `/auth/google/callback` | Handles the return; validates `state`; sets cookies |
| `POST` | `/auth/password-reset` | Requests a reset email |
| `POST` | `/auth/password-reset/confirm` | Consumes the token, sets a new password |

```jsonc
// POST /auth/signup
{ "email": "gm@ashfall.table", "password": "…", "displayName": "Game Master" }
// 201 — cookies set; no token in the body
{ "id": 1, "email": "gm@ashfall.table", "displayName": "Game Master",
  "tableName": null, "avatarUrl": null, "emailVerified": false }
```

```jsonc
// POST /auth/password-reset
{ "email": "someone@example.com" }
// 202 — ALWAYS this response, whether or not the address is registered.
{ "detail": "If that address has an account, a reset link has been sent." }
```

That identical response is deliberate: differentiating would turn the endpoint into an
account-enumeration oracle (IMP-007).

**Every other endpoint requires a session** and is scoped to the authenticated user.
Unauthenticated requests return `401`; requesting another user's resource returns `404`,
not `403` — a `403` confirms the resource exists.

## Campaigns

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/campaigns` | List for the picker |
| `POST` | `/campaigns` | Create — `name` and `systemId` required |
| `GET` | `/campaigns/{id}` | Single campaign |
| `PATCH` | `/campaigns/{id}` | Rename, change image or tint |
| `DELETE` | `/campaigns/{id}` | Delete campaign and all contents |

```jsonc
// POST /campaigns
{ "name": "Ashfall Reach", "systemId": "dnd-2024", "tint": "#E8B87A" }
// 201
{ "id": "ashfall", "name": "Ashfall Reach",
  "system": { "id": "dnd-2024", "name": "D&D 2024" },
  "tint": "#E8B87A", "imageUrl": null, "sessionCount": 0, "lastPlayedAt": null }
```

An unknown `systemId` is a `422`.

`POST /campaigns/{id}/image` — multipart, sets the banner.

`GET /systems` — the systems the add-campaign picker offers.

```jsonc
// GET /systems
[{ "id": "dnd-2024", "name": "D&D 2024" }, { "id": "traveller-2e", "name": "Traveller 2e" }]
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

Uploading a file whose `sha256` already exists in the campaign returns the existing
document rather than processing it again (ADR-0016 IMP-003).

Upload returns `202 Accepted` immediately with `status: "queued"`. The client polls this
list while any document is `queued` or `processing`, then stops (PRIN-003 — upload never
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
which is what makes a bad result diagnosable (ADR-0016 NEG-002).

An empty array means nothing cleared the relevance floor. That is a real answer, not an
error: Research mode refuses on it rather than answering from weak matches (AC-003).

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

**Streaming response.** `text/event-stream`, carrying
[AG-UI](https://docs.ag-ui.com/concepts/events) events
([ADR-0009](adr/adr-0009-ag-ui-protocol.md)). The protocol defines the event schema; this
contract documents only what is product-specific.

```
event: RunStarted
data: {"threadId":"conv-12","runId":"run-88"}

event: ToolCallStart
data: {"toolCallId":"t1","toolCallName":"search_documents"}

event: ToolCallResult
data: {"toolCallId":"t1","content":"3 documents searched, 5 chunks"}

event: TextMessageStart
data: {"messageId":"m-57","role":"assistant"}

event: TextMessageContent
data: {"messageId":"m-57","delta":"Opportunity attacks trigger when"}

event: Custom
data: {"name":"dm.citation","value":{"chunkId":812,"documentId":1,
       "filename":"Core Rulebook v3.pdf","pageFrom":195}}

event: TextMessageEnd
data: {"messageId":"m-57"}

event: RunFinished
data: {"threadId":"conv-12","runId":"run-88","outcome":"success"}
```

**Proposals arrive as a custom event too.** An extracted entity is not written; it is
emitted for the GM to confirm ([ADR-0011](adr/adr-0011-assistant-tools.md)):

```
event: Custom
data: {"name":"dm.proposal","value":{
        "kind":"character",
        "draft":{"name":"Brother Cael","role":"Human Cleric","level":5},
        "sources":{"name":[812],"role":[812],"level":[815]}}}
```

`sources` maps each populated field to the chunks it came from. A field absent from
`sources` was invented by the model and the form marks it as unsourced. The GM submits the
result through the ordinary `POST /campaigns/{cid}/characters` — there is no privileged
assistant write path.

**Citations are a custom event.** AG-UI has no citation type — grounding is a product
concern, not a protocol one — so they are emitted as a namespaced `dm.citation` custom
event. That keeps the product-specific part visibly distinct from the protocol.

Tool-call events drive the design's green check chips. Citation events populate source
references (AC-002). When retrieval finds nothing relevant, the assistant says so
explicitly rather than answering unsourced (AC-003).

A stream always opens with `RunStarted` and closes with exactly one of `RunFinished` or
`RunError`. A stream ending without either is a bug: the client cannot tell it from a
dropped connection.

## Settings

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/settings` | Profile and provider |
| `PATCH` | `/settings` | Update profile fields or `provider` |
| `POST` | `/settings/avatar` | Multipart upload |
| `GET` | `/settings/providers` | Available providers and reachability |

```jsonc
// GET /settings/providers
[{ "id": "claude", "label": "Claude", "available": true },
 { "id": "ollama", "label": "Ollama", "available": false,
   "detail": "No response at http://localhost:11434" }]
```

Switching providers takes effect on the next message with no restart (AC-004).

---
title: "ADR-0017: Google Drive as an import source; storage chosen per deployment"
status: "Accepted"
date: "2026-10-10"
authors: "Piotr Mieszczak"
tags: ["architecture", "decision", "ingestion", "integrations", "storage"]
supersedes: ""
superseded_by: ""
---

# ADR-0017: Google Drive as an import source; storage chosen per deployment

## Status

Proposed | **Accepted** | Rejected | Superseded | Deprecated

## Context

Documents enter the library by upload (file picker or drag-and-drop) into the `FileStore`
port: a local folder, or an object store when hosted
([ADR-0013](adr-0013-postgres-for-local-and-hosted.md) IMP-005). Game masters keep their
rulebooks and notes in cloud drives, and asked whether files could live there, or come from
there.

- **CON-001**: After indexing, search and answers use the chunks in PostgreSQL, and chunk
  text also passes through the embedding provider
  ([ADR-0016](adr-0016-voyage-embeddings.md)). Where the *original* file is kept therefore
  does not control who can read the content. The original is needed for extraction, retry,
  and opening the source.
- **CON-002**: Google Drive has a public API. Its per-file scope `drive.file`, granted
  through the Google Picker, is classed **non-sensitive** and needs only basic app
  verification; the broad `drive` / `drive.readonly` scopes are restricted and need a
  security assessment ([Drive scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)).
- **CON-003**: iCloud Drive has no public server-side API. CloudKit reaches only an app's
  own container, not a user's Drive files; the alternatives use the user's Apple ID
  session and break without notice.
- **CON-004**: Users already sign in with Google ([ADR-0008](adr-0008-own-auth-v1.md)), so
  Drive access is an incremental permission on an existing OAuth client.
- **CON-005**: Ingestion must stay deterministic ([ADR-0002](adr-0002-deterministic-extraction.md),
  BND-001): text in the index is text that is really in the source.

## Decision

**Google Drive is an import source, not a storage backend. Storage location is a
deployment choice, not a user choice.**

1. **Import, then forget.** The user picks files in the Google Picker. The backend
   downloads each one once with a `drive.file` token and passes it to the same upload path
   as a local file: `FileStore`, `sha256` deduplication, `queued`, the worker. Nothing
   syncs, watches, or writes back to Drive.
2. **Narrowest scope.** `drive.file` only, requested incrementally when the user first
   imports, never at sign-in. Restricted scopes are not requested.
3. **Same types as upload.** PDF, Markdown, text, DOCX. Google Docs are exported as DOCX
   through the Drive export endpoint, so they need no extractor of their own.
4. **Provenance recorded.** The document records where it came from (`upload` or
   `google_drive`, plus the Drive file id), for display and re-import. Re-importing the
   same bytes is caught by `sha256` like any duplicate.
5. **Storage per deployment.** `FileStore` stays one port with a disk adapter (local) and
   an object-store adapter (hosted), chosen by configuration. Users do not pick it.

## Consequences

### Positive

- **POS-001**: One ingestion path. A Drive import is an upload with a different first step,
  so extraction, deduplication, progress and retry are not duplicated.
- **POS-002**: No sync problem: no stale copies, no deletions to reconcile, no expiring
  tokens holding the library hostage. Reprocessing never needs Google to be reachable.
- **POS-003**: A non-sensitive scope keeps Google verification light (CON-002).

### Negative

- **NEG-001**: An updated file in Drive does not update the library; the user re-imports.
- **NEG-002**: Google Picker and incremental authorization add frontend and OAuth work on
  top of ADR-0008's sign-in.
- **NEG-003**: Users who wanted their files to *stay* only in their own drive do not get
  that; the original is copied into our `FileStore` (CON-001 explains why it would not buy
  privacy anyway).

## Alternatives Considered

### Drive (or other cloud drives) as the storage backend

- **ALT-001**: **Description**: Keep originals in the user's Drive; store only a reference.
- **ALT-002**: **Rejection Reason**: Adds sync, token expiry, rate limits and deletion
  handling for no privacy gain (CON-001), and makes retry depend on Google.

### iCloud Drive

- **ALT-003**: **Description**: Import from, or store in, iCloud Drive.
- **ALT-004**: **Rejection Reason**: No public server-side API (CON-003). Revisit if Apple
  publishes one.

### YouTube videos as a source (as NotebookLM offers)

- **ALT-005**: **Description**: Paste a YouTube URL; index the video's transcript.
- **ALT-006**: **Rejection Reason, for now**: The official caption download works only for
  videos the user can edit. Reading other videos' captions means scraping, which is
  blocked from cloud IPs and of uncertain standing under YouTube's terms. Transcribing the
  audio ourselves puts a speech-to-text model in ingestion — a generative model that can
  write words nobody said, which BND-001 exists to prevent (CON-005). NotebookLM can do
  this because Google owns YouTube. A user-supplied caption file (`.vtt` / `.srt`) is
  deterministic and stays open as a separate decision.

### User-selectable storage location

- **ALT-007**: **Description**: Each user chooses local disk, our cloud, or their drive.
- **ALT-008**: **Rejection Reason**: A setting that looks like a privacy control but is not
  one (CON-001), multiplied across adapters every user could combine.

## Implementation Notes

- **IMP-001**: Scheduled after upload (#21) and auth (ADR-0008); not part of the v1 scope
  in `docs/mvp-scope.md` until scheduled there.
- **IMP-002**: The Drive download runs server-side with the user's token, in the same
  campaign scope as an upload (BND-003). Tokens are stored hashed or encrypted, like other
  credentials (`docs/data-model.md`, User).
- **IMP-003**: Drive files over the upload size limit are rejected before download, using
  the size in the file's Drive metadata.
- **IMP-004**: Revisit trigger — users ask for live sync in numbers, or a second provider
  (OneDrive, Dropbox) is requested; both would reopen ALT-001 with real demand behind it.

## References

- **REF-001**: [Google Drive API scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)
- **REF-002**: [ADR-0013](adr-0013-postgres-for-local-and-hosted.md) IMP-005 — the
  `FileStore` port
- **REF-003**: [ADR-0016](adr-0016-voyage-embeddings.md) — where chunk text goes after
  import
- **REF-004**: [ADR-0002](adr-0002-deterministic-extraction.md) — why ingestion stays
  deterministic

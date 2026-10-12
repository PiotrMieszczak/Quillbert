import type { LibraryDocument } from "./types";

/** A picked file as the row it becomes before extraction: queued, nothing known yet.
 *  shortcut: local only until #21 accepts uploads and returns the real document. */
export function queuedFromFile(file: File, id: string): LibraryDocument {
  return {
    id,
    name: file.name,
    kind: file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "DOC",
    pages: null,
    meta: "waiting to upload",
    status: "Queued",
    progress: 0,
  };
}
